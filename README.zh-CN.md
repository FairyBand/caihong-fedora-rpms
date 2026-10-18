# Caihong Fedora RPM 仓库

GitHub 仓库：<https://github.com/FairyBand/caihong-fedora-rpms>

这里维护 OnePlus Pad Pro (`caihong`) 的 Fedora Workstation 44 ARM64 设备适配
RPM。仓库与 rootfs 工程分离，Copr 使用 aarch64 builder 构建；当前版本固定从
`caihong-linux-rootfs` 的 commit `4a343b670fcc5892be01857bc79cdb656a79787e` 取设备数据，外部源码在各 spec 中固定
commit。

当前包边界如下：

| 包 | 内容 | SELinux policy |
| --- | --- | --- |
| `libcamera` | Caihong simple pipeline、simple IPA、GPU soft ISP、qcam、GStreamer、传感器 YAML | 未包含 |
| `plasma-camera` | Caihong Plasma Camera 前端，GNOME 会话中作为 Qt 应用运行 | 未包含 |
| `ffmpeg`（`ffmpeg-free` 等子包） | Fedora f44 `ffmpeg-free` 重建：修复 Iris V4L2 M2M 编码崩溃、补齐编码器 extradata，并开启 h264/hevc V4L2 M2M 硬件解码器 | 不适用 |
| `caihong-ssc` | FastRPC listener、SSC SensorProxy、SSC DSP 配置 | 未包含 |
| `caihong-device-support` | Pogo/触控板 udev、DMA heap、MAC、蓝牙、热点、手写笔、手电筒和启动服务 | 未包含 |
| `caihong-firmware` | ADSP/CDSP、GPU、Iris 视频编解码（OEM 签名 `vpu33_4v.mbn`）、WLAN/BT、触控和音频相关固件 | 不适用 |
| `caihong-audio` | UCM2 和 AudioReach topology | 不适用 |
| `caihong-qbootctl` | Android A/B 槽检查与标记工具 | 未包含 |
| `caihong-kernel-updater` | 当前槽识别、boot 分区写入和读回校验命令/服务 | 未包含 |
| `caihong-kernel-payload` | 具体 release 的 Image、DTB、boot 镜像和模块 | 未包含 |

除 `caihong-kernel-payload` 外，当前规格已在 Fedora 44 x86_64 构建容器中完成
`rpmbuild -ba` 验证；Copr 的 aarch64 构建仍是发布前的目标架构检查。SSC 中的
厂商 ELF 是预编译 payload，因此不生成 debugsource/debug 子包。

SELinux policy 暂时不打包。首个 Fedora 镜像应使用 permissive 启动，按 SSC、相机、
Pogo/pen、热点、MAC 和 kernel updater 分别收集 `ausearch -m AVC`，确认功能后再
建立小型 policy RPM。不要用一个全局 permissive domain 掩盖所有服务。

## 本地检查

需要 Fedora 44 构建环境和 `rpm-build`：

```sh
rpmspec -P --target=aarch64 SPECS/caihong-device-support.spec >/dev/null
rpmspec -P --target=aarch64 SPECS/caihong-ssc.spec >/dev/null
rpmspec -P --target=aarch64 SPECS/caihong-audio.spec >/dev/null
rpmspec -P --target=aarch64 SPECS/caihong-firmware.spec >/dev/null
rpmspec -P --target=aarch64 SPECS/caihong-qbootctl.spec >/dev/null
rpmspec -P --target=aarch64 SPECS/plasma-camera-caihong.spec >/dev/null
rpmspec -P --target=aarch64 SPECS/caihong-kernel-updater.spec >/dev/null
rpmspec -P --target=aarch64 SPECS/caihong-kernel-payload.spec >/dev/null
rpmspec -P --target=aarch64 SPECS/ffmpeg-caihong.spec >/dev/null
```

`caihong-kernel-payload` 需要先生成 release archive，目录必须包含：

```text
Image
caihong.dtb
boot-linux.img
boot-userdata.img
kernel-release
LICENSE
modules/<kernel-release>/
```

该 payload 不在普通 Copr 源码构建中生成；内核和 Android boot v2 镜像仍由内核
发布流水线提供，然后以 source archive 交给 Copr。

## Copr 顺序

先构建并发布 `libcamera`，再构建 `plasma-camera`；其余包可以并行。目标项目建议为
`caihong/fedora-44`，只启用 `aarch64`。设备镜像中必须先启用 Copr，再安装这些包。
官方 `libcamera` 和 `plasma-camera` 源版本由 DNF5 override 排除，避免忘记重建时
回退到 Fedora 包。

`ffmpeg` 同样永久压过 Fedora：`Epoch: 1`，并由 `libavcodec-free` 安装
`/etc/dnf/repos.override.d/99-caihong-ffmpeg.repo`，把 Fedora 的 `ffmpeg-free`、
`libav*-free`、`libsw*-free` 排除出 `fedora*`/`updates*`。DNF5 的 `excludepkgs`
是追加列表，和 libcamera 的 override 文件可以共存。

`SPECS/ffmpeg-caihong.spec` 和 `SOURCES/ffmpeg-*` 由 `scripts/sync-ffmpeg.py` 从
Fedora dist-git `rpms/ffmpeg` 的 f44 分支生成，不要手工编辑；Caihong 自己维护的只有
`SOURCES/ffmpeg-v4l2-*.patch`、`SOURCES/99-caihong-ffmpeg.repo` 和脚本里的配置
（补丁列表、额外解码器、`CAIHONG_RELEASE`）。补丁改了而 Fedora 没更新时，把
`CAIHONG_RELEASE` 加一后重新运行脚本。

`.github/workflows/sync-ffmpeg.yml` 每 6 小时检查一次 dist-git：有更新时重新生成
spec，在 Fedora 44 容器里用 `scripts/check-srpm.sh` 构建 SRPM 并执行 `%prep`
（校验 FFmpeg 签名、应用全部补丁），通过后提交、推送，并 POST 到仓库 secret
`COPR_FFMPEG_WEBHOOK` 触发 Copr 构建；失败时不推送，并开一个 issue。也可以在
Actions 页面手动运行，指定某个 dist-git commit。

`COPR_FFMPEG_WEBHOOK` 取自 Copr 项目里 `ffmpeg` 包的自定义 webhook
（`https://copr.fedorainfracloud.org/webhooks/custom/<id>/<uuid>/ffmpeg/`），该包
需配置为 SCM 源、spec 为 `SPECS/ffmpeg-caihong.spec`、SRPM 方式为 `make_srpm`。
如果项目已经用 GitHub push webhook 自动构建，可以不设置这个 secret，避免重复构建。

本地同步和检查：

```sh
scripts/sync-ffmpeg.py            # 最后一行输出 changed / unchanged
scripts/check-srpm.sh SPECS/ffmpeg-caihong.spec
```

直接上传本地 SRPM 即可触发 Copr 构建。Fedora 构建环境需要 `rpm-build` 和
`rpmdevtools`，先为一个 spec 生成 SRPM：

```sh
make srpm SPEC=SPECS/libcamera-caihong.spec
copr build --nowait <用户名>/fedora-44 .rpmbuild/SRPMS/*.src.rpm
```

然后按依赖顺序上传 `plasma-camera`，其余设备包可以并行上传。`caihong-kernel-payload`
需要先把对应的 `caihong-kernel-payload-<version>.tar.zst` 放进 `SOURCES/`，再生成
SRPM。直接上传 SRPM 的方式适合手动发布；本仓库也可作为 Copr SCM 的 Git 源。
Copr 只跟踪本仓库的提交，不会自动监视 spec 中固定的上游 commit。上游更新时需要
人工更新 spec 中的 commit、提交并推送，随后由 SCM webhook 触发构建。若只想临时
构建，也可以继续使用本地 SRPM 上传。

每个服务第一次启动都应记录：

```sh
getenforce
systemctl --failed
ausearch -m AVC -ts boot
journalctl -b -u caihong-ssc -u iio-sensor-proxy
```

本仓库不把 permissive 结果当成最终迁移完成；只有 policy RPM 补齐并恢复 enforcing
后，Fedora Workstation 44 设备适配才算完成。

## 上游致谢

本仓库的 RPM spec、Fedora Workstation 44 适配和设备打包由 FairyBand 维护。以下
项目提供了被打包的上游代码、资源或工具，版权和许可证归其原作者及贡献者所有：

- [Osilvfe/caihong-linux-rootfs](https://github.com/Osilvfe/caihong-linux-rootfs)
- [Osilvfe/libcamera](https://github.com/Osilvfe/libcamera)
- [Osilvfe/plasma-camera](https://github.com/Osilvfe/plasma-camera)
- [linux-msm/qbootctl](https://github.com/linux-msm/qbootctl)
- [FFmpeg](https://ffmpeg.org/) 与 Fedora [rpms/ffmpeg](https://src.fedoraproject.org/rpms/ffmpeg) 打包
