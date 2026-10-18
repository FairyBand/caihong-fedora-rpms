/******************************************************************************
    OBS Studio hardware video encoders for V4L2 memory-to-memory devices
    Copyright (C) 2026 by fairyband <zl3004431@gmail.com>
    Frame copy and timeout handling derived from obs-ffmpeg-video-encoders.c
    by Lain Bailey <lain@obsproject.com>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
******************************************************************************/

/*
 * The encoders drive libavcodec's h264_v4l2m2m / hevc_v4l2m2m wrappers, which
 * talk to stateful V4L2 encoders such as the Qualcomm Iris VPU.  They are only
 * registered when a V4L2 M2M device that can produce the codec exists.
 */

#include <obs-module.h>
#include <obs-avc.h>
#include <obs-hevc.h>
#include <util/base.h>
#include <util/darray.h>
#include <util/dstr.h>
#include <util/platform.h>
#include <media-io/video-io.h>

#include <libavcodec/avcodec.h>
#include <libavutil/error.h>
#include <libavutil/frame.h>
#include <libavutil/pixdesc.h>

#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <string.h>
#include <sys/ioctl.h>
#include <unistd.h>
#include <linux/videodev2.h>

OBS_DECLARE_MODULE()
OBS_MODULE_USE_DEFAULT_LOCALE("obs-v4l2m2m", "en-US")

#define do_log(level, format, ...) \
	blog(level, "[%s encoder: '%s'] " format, enc->codec_name, obs_encoder_get_name(enc->encoder), ##__VA_ARGS__)

#define error(format, ...) do_log(LOG_ERROR, format, ##__VA_ARGS__)
#define warn(format, ...) do_log(LOG_WARNING, format, ##__VA_ARGS__)
#define info(format, ...) do_log(LOG_INFO, format, ##__VA_ARGS__)

#define SEC_TO_NSEC 1000000000LL
#define TIMEOUT_MAX_SEC 5
#define TIMEOUT_MAX_NSEC (TIMEOUT_MAX_SEC * SEC_TO_NSEC)

struct v4l2m2m_encoder {
	obs_encoder_t *encoder;
	const char *codec_name;
	bool hevc;

	AVCodecContext *context;
	AVFrame *vframe;
	AVPacket *pkt;
	int64_t start_ts;

	DARRAY(uint8_t) buffer;
	DARRAY(uint8_t) header;
};

/* ------------------------------------------------------------------------- */
/* Device probing                                                            */

static bool device_has_format(int fd, enum v4l2_buf_type type, uint32_t pixfmt)
{
	struct v4l2_fmtdesc desc = {.type = type};

	for (desc.index = 0; ioctl(fd, VIDIOC_ENUM_FMT, &desc) == 0; desc.index++) {
		if (desc.pixelformat == pixfmt)
			return true;
	}
	return false;
}

/* Return true when some /dev/video* M2M node encodes NV12 into @codec_fmt. */
static bool find_m2m_encoder(uint32_t codec_fmt)
{
	DIR *dir = opendir("/dev");
	struct dirent *ent;
	bool found = false;

	if (!dir)
		return false;

	while (!found && (ent = readdir(dir))) {
		if (strncmp(ent->d_name, "video", 5) != 0)
			continue;

		struct dstr path = {0};
		dstr_printf(&path, "/dev/%s", ent->d_name);
		int fd = open(path.array, O_RDWR | O_NONBLOCK | O_CLOEXEC);
		dstr_free(&path);
		if (fd < 0)
			continue;

		struct v4l2_capability cap = {0};
		if (ioctl(fd, VIDIOC_QUERYCAP, &cap) == 0) {
			uint32_t caps = (cap.capabilities & V4L2_CAP_DEVICE_CAPS) ? cap.device_caps
										   : cap.capabilities;
			enum v4l2_buf_type out_type = 0, cap_type = 0;
			bool m2m = true;

			if (caps & V4L2_CAP_VIDEO_M2M_MPLANE) {
				out_type = V4L2_BUF_TYPE_VIDEO_OUTPUT_MPLANE;
				cap_type = V4L2_BUF_TYPE_VIDEO_CAPTURE_MPLANE;
			} else if (caps & V4L2_CAP_VIDEO_M2M) {
				out_type = V4L2_BUF_TYPE_VIDEO_OUTPUT;
				cap_type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
			} else {
				m2m = false;
			}

			if (m2m && device_has_format(fd, cap_type, codec_fmt) &&
			    device_has_format(fd, out_type, V4L2_PIX_FMT_NV12)) {
				blog(LOG_INFO, "[obs-v4l2m2m] %s (%s) can encode %.4s", ent->d_name,
				     (const char *)cap.card, (const char *)&codec_fmt);
				found = true;
			}
		}
		close(fd);
	}

	closedir(dir);
	return found;
}

/* ------------------------------------------------------------------------- */
/* Encoder                                                                   */

static const char *h264_getname(void *unused)
{
	UNUSED_PARAMETER(unused);
	return obs_module_text("V4L2M2M.H264");
}

static const char *hevc_getname(void *unused)
{
	UNUSED_PARAMETER(unused);
	return obs_module_text("V4L2M2M.HEVC");
}

static void v4l2m2m_video_info(void *data, struct video_scale_info *info)
{
	UNUSED_PARAMETER(data);

	/* The libavcodec wrapper only accepts NV12 in limited range. */
	info->format = VIDEO_FORMAT_NV12;
	info->range = VIDEO_RANGE_PARTIAL;
}

static void set_error(struct v4l2m2m_encoder *enc, const char *text_id, const char *detail)
{
	struct dstr msg = {0};

	dstr_copy(&msg, obs_module_text(text_id));
	dstr_replace(&msg, "%1", enc->codec_name);
	if (detail)
		dstr_replace(&msg, "%2", detail);
	obs_encoder_set_last_error(enc->encoder, msg.array);
	error("%s", msg.array);
	dstr_free(&msg);
}

static void set_color(AVCodecContext *ctx, enum video_colorspace cs)
{
	switch (cs) {
	case VIDEO_CS_601:
		ctx->color_primaries = AVCOL_PRI_SMPTE170M;
		ctx->color_trc = AVCOL_TRC_SMPTE170M;
		ctx->colorspace = AVCOL_SPC_SMPTE170M;
		break;
	case VIDEO_CS_SRGB:
		ctx->color_primaries = AVCOL_PRI_BT709;
		ctx->color_trc = AVCOL_TRC_IEC61966_2_1;
		ctx->colorspace = AVCOL_SPC_BT709;
		break;
	case VIDEO_CS_DEFAULT:
	case VIDEO_CS_709:
	default:
		ctx->color_primaries = AVCOL_PRI_BT709;
		ctx->color_trc = AVCOL_TRC_BT709;
		ctx->colorspace = AVCOL_SPC_BT709;
		break;
	}
	ctx->color_range = AVCOL_RANGE_MPEG;
	ctx->chroma_sample_location = AVCHROMA_LOC_LEFT;
}

static int h264_profile(const char *name)
{
	if (strcmp(name, "baseline") == 0)
		return AV_PROFILE_H264_CONSTRAINED_BASELINE;
	if (strcmp(name, "main") == 0)
		return AV_PROFILE_H264_MAIN;
	return AV_PROFILE_H264_HIGH;
}

static void v4l2m2m_destroy(void *data)
{
	struct v4l2m2m_encoder *enc = data;

	avcodec_free_context(&enc->context);
	av_frame_free(&enc->vframe);
	av_packet_free(&enc->pkt);
	da_free(enc->buffer);
	da_free(enc->header);
	bfree(enc);
}

static bool v4l2m2m_init_codec(struct v4l2m2m_encoder *enc, obs_data_t *settings, const char *lib)
{
	video_t *video = obs_encoder_video(enc->encoder);
	const struct video_output_info *voi = video_output_get_info(video);
	int bitrate = (int)obs_data_get_int(settings, "bitrate");
	int keyint_sec = (int)obs_data_get_int(settings, "keyint_sec");
	const char *profile = obs_data_get_string(settings, "profile");
	int ret;

	const AVCodec *codec = avcodec_find_encoder_by_name(lib);
	if (!codec) {
		set_error(enc, "V4L2M2M.Error", "encoder not found in libavcodec");
		return false;
	}

	enc->context = avcodec_alloc_context3(codec);
	enc->vframe = av_frame_alloc();
	enc->pkt = av_packet_alloc();
	if (!enc->context || !enc->vframe || !enc->pkt)
		return false;

	AVCodecContext *ctx = enc->context;
	ctx->width = (int)obs_encoder_get_width(enc->encoder);
	ctx->height = (int)obs_encoder_get_height(enc->encoder);
	ctx->time_base = (AVRational){(int)voi->fps_den, (int)voi->fps_num};
	ctx->framerate = (AVRational){(int)voi->fps_num, (int)voi->fps_den};
	ctx->pix_fmt = AV_PIX_FMT_NV12;
	ctx->bit_rate = (int64_t)bitrate * 1000;
	ctx->rc_max_rate = ctx->bit_rate;
	ctx->max_b_frames = 0;
	ctx->gop_size = keyint_sec > 0 ? (int)(keyint_sec * voi->fps_num / voi->fps_den) : 250;
	ctx->flags |= AV_CODEC_FLAG_GLOBAL_HEADER;
	if (!enc->hevc)
		ctx->profile = h264_profile(profile);
	set_color(ctx, voi->colorspace);

	info("settings:\n"
	     "\tlibrary:      %s\n"
	     "\tbitrate:      %d\n"
	     "\tkeyint:       %d frames\n"
	     "\tprofile:      %s\n"
	     "\twidth:        %d\n"
	     "\theight:       %d\n"
	     "\tfps:          %u/%u",
	     lib, bitrate, ctx->gop_size, enc->hevc ? "main" : profile, ctx->width, ctx->height, voi->fps_num,
	     voi->fps_den);

	ret = avcodec_open2(ctx, codec, NULL);
	if (ret < 0) {
		set_error(enc, "V4L2M2M.Error", av_err2str(ret));
		return false;
	}

	if (ctx->extradata_size > 0)
		da_copy_array(enc->header, ctx->extradata, (size_t)ctx->extradata_size);
	else
		warn("no global stream header, extracting it from the first packet");

	enc->vframe->format = ctx->pix_fmt;
	enc->vframe->width = ctx->width;
	enc->vframe->height = ctx->height;
	enc->vframe->color_range = ctx->color_range;
	enc->vframe->color_primaries = ctx->color_primaries;
	enc->vframe->color_trc = ctx->color_trc;
	enc->vframe->colorspace = ctx->colorspace;
	enc->vframe->chroma_location = ctx->chroma_sample_location;
	ret = av_frame_get_buffer(enc->vframe, base_get_alignment());
	if (ret < 0) {
		set_error(enc, "V4L2M2M.Error", av_err2str(ret));
		return false;
	}

	return true;
}

static void *v4l2m2m_create(obs_data_t *settings, obs_encoder_t *encoder, bool hevc)
{
	video_t *video = obs_encoder_video(encoder);
	const struct video_output_info *voi = video_output_get_info(video);

	switch (voi->colorspace) {
	case VIDEO_CS_2100_PQ:
	case VIDEO_CS_2100_HLG: {
		const char *text = obs_module_text("V4L2M2M.UnsupportedColorSpace");
		obs_encoder_set_last_error(encoder, text);
		blog(LOG_ERROR, "[obs-v4l2m2m] %s", text);
		return NULL;
	}
	default:
		break;
	}

	switch (voi->format) {
	case VIDEO_FORMAT_I010:
	case VIDEO_FORMAT_P010:
	case VIDEO_FORMAT_I210:
	case VIDEO_FORMAT_P216:
	case VIDEO_FORMAT_P416:
	case VIDEO_FORMAT_V210:
	case VIDEO_FORMAT_I412:
	case VIDEO_FORMAT_YA2L: {
		const char *text = obs_module_text("V4L2M2M.UnsupportedVideoFormat");
		obs_encoder_set_last_error(encoder, text);
		blog(LOG_ERROR, "[obs-v4l2m2m] %s", text);
		return NULL;
	}
	default:
		break;
	}

	struct v4l2m2m_encoder *enc = bzalloc(sizeof(*enc));
	enc->encoder = encoder;
	enc->hevc = hevc;
	enc->codec_name = hevc ? "V4L2 HEVC" : "V4L2 H.264";

	blog(LOG_INFO, "---------------------------------");
	if (!v4l2m2m_init_codec(enc, settings, hevc ? "hevc_v4l2m2m" : "h264_v4l2m2m")) {
		v4l2m2m_destroy(enc);
		return NULL;
	}
	return enc;
}

static void *h264_create(obs_data_t *settings, obs_encoder_t *encoder)
{
	return v4l2m2m_create(settings, encoder, false);
}

static void *hevc_create(obs_data_t *settings, obs_encoder_t *encoder)
{
	return v4l2m2m_create(settings, encoder, true);
}

static void copy_nv12(AVFrame *pic, const struct encoder_frame *frame, int height)
{
	for (int plane = 0; plane < 2; plane++) {
		int frame_rowsize = (int)frame->linesize[plane];
		int pic_rowsize = pic->linesize[plane];
		int bytes = frame_rowsize < pic_rowsize ? frame_rowsize : pic_rowsize;
		int plane_height = plane ? (height + 1) / 2 : height;

		for (int y = 0; y < plane_height; y++)
			memcpy(pic->data[plane] + y * pic_rowsize, frame->data[plane] + y * frame_rowsize, bytes);
	}
}

/* Fill @packet from enc->pkt.  Returns false if the encoder fell too far behind. */
static bool output_packet(struct v4l2m2m_encoder *enc, struct encoder_packet *packet)
{
	AVPacket *pkt = enc->pkt;
	const int64_t cur_ts = (int64_t)os_gettime_ns();
	const int64_t pause_offset = (int64_t)obs_encoder_get_pause_offset(enc->encoder);

	if (!enc->header.num) {
		uint8_t *new_packet = NULL, *header = NULL, *sei = NULL;
		size_t new_size = 0, header_size = 0, sei_size = 0;

		if (enc->hevc)
			obs_extract_hevc_headers(pkt->data, pkt->size, &new_packet, &new_size, &header, &header_size,
						 &sei, &sei_size);
		else
			obs_extract_avc_headers(pkt->data, pkt->size, &new_packet, &new_size, &header, &header_size,
						&sei, &sei_size);
		if (header_size)
			da_copy_array(enc->header, header, header_size);
		bfree(new_packet);
		bfree(header);
		bfree(sei);
	}

	da_copy_array(enc->buffer, pkt->data, (size_t)pkt->size);

	packet->data = enc->buffer.array;
	packet->size = enc->buffer.num;
	packet->type = OBS_ENCODER_VIDEO;
	packet->pts = pkt->pts;
	/* No B-frames, so decode order equals presentation order. */
	packet->dts = pkt->pts;
	packet->keyframe = (pkt->flags & AV_PKT_FLAG_KEY) ||
			   (enc->hevc ? obs_hevc_keyframe(packet->data, packet->size)
				      : obs_avc_keyframe(packet->data, packet->size));
	packet->priority = enc->hevc ? obs_parse_hevc_packet_priority(packet)
				     : obs_parse_avc_packet_priority(packet);

	const int64_t recv_ts_nsec =
		(int64_t)util_mul_div64((uint64_t)pkt->pts, (uint64_t)SEC_TO_NSEC * enc->context->time_base.num,
					(uint64_t)enc->context->time_base.den) +
		enc->start_ts;
	if (cur_ts - recv_ts_nsec - pause_offset > TIMEOUT_MAX_NSEC) {
		char timeout_str[16];
		snprintf(timeout_str, sizeof(timeout_str), "%d", TIMEOUT_MAX_SEC);
		set_error(enc, "V4L2M2M.Timeout", timeout_str);
		return false;
	}
	return true;
}

static bool v4l2m2m_encode(void *data, struct encoder_frame *frame, struct encoder_packet *packet,
			   bool *received_packet)
{
	struct v4l2m2m_encoder *enc = data;
	int send_ret, ret;

	*received_packet = false;
	if (!enc->start_ts)
		enc->start_ts = (int64_t)os_gettime_ns();

	ret = av_frame_make_writable(enc->vframe);
	if (ret < 0) {
		error("av_frame_make_writable failed: %s", av_err2str(ret));
		return false;
	}
	copy_nv12(enc->vframe, frame, enc->context->height);
	enc->vframe->pts = frame->pts;

	send_ret = avcodec_send_frame(enc->context, enc->vframe);
	if (send_ret < 0 && send_ret != AVERROR(EAGAIN)) {
		error("avcodec_send_frame failed: %s", av_err2str(send_ret));
		return false;
	}

	ret = avcodec_receive_packet(enc->context, enc->pkt);
	if (ret < 0 && ret != AVERROR(EAGAIN)) {
		error("avcodec_receive_packet failed: %s", av_err2str(ret));
		return false;
	}

	/* The input queue was full: the packet above made room, retry once. */
	if (send_ret == AVERROR(EAGAIN)) {
		send_ret = avcodec_send_frame(enc->context, enc->vframe);
		if (send_ret < 0)
			warn("dropping frame %lld: %s", (long long)frame->pts, av_err2str(send_ret));
	}

	if (ret == 0 && enc->pkt->size > 0) {
		bool ok = output_packet(enc, packet);
		*received_packet = true;
		av_packet_unref(enc->pkt);
		return ok;
	}

	av_packet_unref(enc->pkt);
	return true;
}

static bool v4l2m2m_extra_data(void *data, uint8_t **extra_data, size_t *size)
{
	struct v4l2m2m_encoder *enc = data;

	if (!enc->header.num)
		return false;
	*extra_data = enc->header.array;
	*size = enc->header.num;
	return true;
}

static void v4l2m2m_defaults(obs_data_t *settings)
{
	obs_data_set_default_int(settings, "bitrate", 8000);
	obs_data_set_default_int(settings, "keyint_sec", 2);
	obs_data_set_default_string(settings, "profile", "high");
}

static obs_properties_t *properties(bool hevc)
{
	obs_properties_t *props = obs_properties_create();
	obs_property_t *p;

	p = obs_properties_add_int(props, "bitrate", obs_module_text("Bitrate"), 100, 160000, 50);
	obs_property_int_set_suffix(p, " Kbps");

	p = obs_properties_add_int(props, "keyint_sec", obs_module_text("KeyframeIntervalSec"), 0, 20, 1);
	obs_property_int_set_suffix(p, " s");

	if (!hevc) {
		p = obs_properties_add_list(props, "profile", obs_module_text("Profile"), OBS_COMBO_TYPE_LIST,
					    OBS_COMBO_FORMAT_STRING);
		obs_property_list_add_string(p, "baseline", "baseline");
		obs_property_list_add_string(p, "main", "main");
		obs_property_list_add_string(p, "high", "high");
	}

	return props;
}

static obs_properties_t *h264_properties(void *unused)
{
	UNUSED_PARAMETER(unused);
	return properties(false);
}

static obs_properties_t *hevc_properties(void *unused)
{
	UNUSED_PARAMETER(unused);
	return properties(true);
}

static struct obs_encoder_info h264_encoder_info = {
	.id = "v4l2m2m_h264",
	.type = OBS_ENCODER_VIDEO,
	.codec = "h264",
	.get_name = h264_getname,
	.create = h264_create,
	.destroy = v4l2m2m_destroy,
	.encode = v4l2m2m_encode,
	.get_defaults = v4l2m2m_defaults,
	.get_properties = h264_properties,
	.get_extra_data = v4l2m2m_extra_data,
	.get_video_info = v4l2m2m_video_info,
};

static struct obs_encoder_info hevc_encoder_info = {
	.id = "v4l2m2m_hevc",
	.type = OBS_ENCODER_VIDEO,
	.codec = "hevc",
	.get_name = hevc_getname,
	.create = hevc_create,
	.destroy = v4l2m2m_destroy,
	.encode = v4l2m2m_encode,
	.get_defaults = v4l2m2m_defaults,
	.get_properties = hevc_properties,
	.get_extra_data = v4l2m2m_extra_data,
	.get_video_info = v4l2m2m_video_info,
};

bool obs_module_load(void)
{
	bool any = false;

	if (avcodec_find_encoder_by_name("h264_v4l2m2m") && find_m2m_encoder(V4L2_PIX_FMT_H264)) {
		obs_register_encoder(&h264_encoder_info);
		any = true;
	}
	if (avcodec_find_encoder_by_name("hevc_v4l2m2m") && find_m2m_encoder(V4L2_PIX_FMT_HEVC)) {
		obs_register_encoder(&hevc_encoder_info);
		any = true;
	}

	if (!any)
		blog(LOG_INFO, "[obs-v4l2m2m] no V4L2 M2M H.264/HEVC encoder found");
	return true;
}

const char *obs_module_description(void)
{
	return "V4L2 memory-to-memory hardware video encoders";
}
