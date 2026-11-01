%global commit b297636af143a0080a9a05db3eef17e1e279e36e

Name:           libcamera
Epoch:          1
Version:        0.7.2
Release:        103.caihong%{?dist}
Summary:        Camera support library with OnePlus Pad Pro hardware ISP

License:        LGPL-2.1-or-later
URL:            https://github.com/Osilvfe/libcamera/tree/caihong-camera
Source0:        https://github.com/Osilvfe/libcamera/archive/%{commit}/libcamera-%{commit}.tar.gz
Source1:        70-libcamera.rules
Source2:        qcam.desktop
Source3:        qcam.metainfo.xml
Source4:        99-caihong-libcamera.repo

# Keep the Fedora package name so Fedora applications continue to resolve the
# normal libcamera SONAME and RPM provides.  The custom release is higher than
# Fedora 44's current 0.7.2-2 build.
Provides:       libcamera-caihong = %{epoch}:%{version}-%{release}
Obsoletes:      libcamera-ipa < 1:0.7.2-103.caihong

BuildRequires:  gcc-c++
BuildRequires:  desktop-file-utils
BuildRequires:  meson
BuildRequires:  ninja-build
BuildRequires:  openssl
BuildRequires:  openssl-devel
BuildRequires:  pkgconfig(glib-2.0)
BuildRequires:  pkgconfig(gstreamer-video-1.0)
BuildRequires:  pkgconfig(gstreamer-allocators-1.0)
BuildRequires:  gnutls-devel
BuildRequires:  libatomic
BuildRequires:  libevent-devel
BuildRequires:  libjpeg-turbo-devel
BuildRequires:  libyaml-devel
BuildRequires:  pkgconfig(Qt6Core)
BuildRequires:  pkgconfig(Qt6Gui)
BuildRequires:  pkgconfig(Qt6OpenGL)
BuildRequires:  pkgconfig(Qt6OpenGLWidgets)
BuildRequires:  pkgconfig(Qt6Widgets)
BuildRequires:  pkgconfig(egl)
BuildRequires:  pkgconfig(glesv2)
BuildRequires:  systemd-devel
BuildRequires:  python3-jinja2
BuildRequires:  python3-pyyaml
BuildRequires:  python3-ply

%description
libcamera built from the Caihong hardware ISP branch for the OnePlus Pad Pro.
The simple pipeline drives qcom-camss capture into Camera ICP/BPS and does not
build a software ISP or simple IPA.

%package devel
Summary:        Development files for %{name}
Requires:       %{name}%{?_isa} = %{?epoch:%{epoch}:}%{version}-%{release}

%description devel
Development files for applications using libcamera.

%package gstreamer
Summary:        GStreamer plugin for %{name}
Requires:       %{name}%{?_isa} = %{?epoch:%{epoch}:}%{version}-%{release}

%description gstreamer
GStreamer integration for libcamera.

%package qcam
Summary:        QCam application for %{name}
Requires:       %{name}%{?_isa} = %{?epoch:%{epoch}:}%{version}-%{release}

%description qcam
The Qt QCam diagnostic application for libcamera.

%package tools
Summary:        Command-line tools for %{name}
Requires:       %{name}%{?_isa} = %{?epoch:%{epoch}:}%{version}-%{release}

%description tools
The cam and libcamera-bug-report utilities.

%prep
%autosetup -n libcamera-%{commit}

%build
# Hardware ISP options match upstream install-caihong-libcamera-rootfs.sh.
# ipas is empty and softisp-gpu is disabled; AE/AWB run in the simple pipeline.
%meson \
    -Dandroid=disabled \
    -Dapps-output-dng=disabled \
    -Dcam=enabled \
    -Dcam-output-kms=disabled \
    -Dcam-output-sdl2=disabled \
    -Ddocumentation=disabled \
    -Dgstreamer=enabled \
    -Dipas= \
    -Dlc-compliance=disabled \
    -Dlibdw=disabled \
    -Dlibunwind=disabled \
    -Dpipelines=simple \
    -Dpycamera=disabled \
    -Dqcam=enabled \
    -Drpi-awb-nn=disabled \
    -Dsoftisp-gpu=disabled \
    -Dtest=false \
    -Dtracing=disabled \
    -Dudev=enabled \
    -Dv4l2=disabled \
    -Dwerror=false
%meson_build

%install
%meson_install

install -Dpm 0644 %{SOURCE1} %{buildroot}%{_udevrulesdir}/70-libcamera.rules
install -Dpm 0644 %{SOURCE2} %{buildroot}%{_datadir}/applications/qcam.desktop
install -Dpm 0644 %{SOURCE3} %{buildroot}%{_metainfodir}/qcam.metainfo.xml
install -Dpm 0644 %{SOURCE4} %{buildroot}%{_sysconfdir}/dnf/repos.override.d/99-caihong-libcamera.repo

install -dpm 0755 %{buildroot}%{_datadir}/caihong
cat > %{buildroot}%{_datadir}/caihong/libcamera-build-info << EOF
build=caihong
version=%{version}+caihong
source_commit=%{commit}
libdir=lib64
pipelines=simple
ipas=none
isp_backend=qcom-camera-icp-bps
isp_output=nv12m
isp_statistics=output-luma-chroma-sampling
isp_pipeline=raw10-demosaic-white-balance-ccm-nv12m
color_correction=sensor-profile-ccm
gamma=deferred-until-pre-gamma-white-balance
module_abi=qcom-camera-icp-bps-matched-build
isp_validation=front-3264x2448-rear-4208x3120
validated_camera_sensors=sc820cs,sc1320cs
sensor_controls=closed-loop-exposure-gain
software_isp=disabled
software_isp_linkage=omitted
software_isp_fallback=disabled
softisp_gpu=disabled
ae_controls=unavailable
auto_exposure=output-luma-closed-loop
awb_controls=v4l2-red-blue-balance-q10
white_balance=sensor-profile-plus-adaptive
auto_white_balance=output-chroma-closed-loop
autofocus=manual-position
camera_flash=dual-v4l2
camera_flash_sync=frame-start-request-queue
camera_flash_torch_stop=led-mode
gstreamer=enabled
qcam=enabled
EOF
chmod 0644 %{buildroot}%{_datadir}/caihong/libcamera-build-info

# A hardware ISP build must not ship software ISP payloads. Empty directories
# must not become unpackaged files.
rm -f %{buildroot}%{_libdir}/libcamera/ipa/ipa_soft_simple.so \
    %{buildroot}%{_libdir}/libcamera/ipa/ipa_soft_simple.so.sign \
    %{buildroot}%{_libexecdir}/libcamera/soft_ipa_proxy \
    %{buildroot}%{_datadir}/libcamera/ipa/simple/sc820cs.yaml \
    %{buildroot}%{_datadir}/libcamera/ipa/simple/sc1320cs.yaml
find %{buildroot}%{_libdir}/libcamera %{buildroot}%{_libexecdir}/libcamera \
    %{buildroot}%{_datadir}/libcamera -depth -type d -empty -delete 2>/dev/null || :

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/qcam.desktop

%files
%license COPYING.rst LICENSES/LGPL-2.1-or-later.txt
%{_libdir}/libcamera*.so.0.7
%{_libdir}/libcamera*.so.%{version}
%{_udevrulesdir}/70-libcamera.rules
%config(noreplace) %{_sysconfdir}/dnf/repos.override.d/99-caihong-libcamera.repo
%dir %{_datadir}/caihong
%{_datadir}/caihong/libcamera-build-info

%files devel
%{_includedir}/libcamera/
%{_libdir}/libcamera*.so
%{_libdir}/pkgconfig/libcamera-base.pc
%{_libdir}/pkgconfig/libcamera.pc

%files gstreamer
%{_libdir}/gstreamer-1.0/libgstlibcamera.so

%files qcam
%license LICENSES/GPL-2.0-or-later.txt LICENSES/MIT.txt
%{_bindir}/qcam
%{_datadir}/applications/qcam.desktop
%{_metainfodir}/qcam.metainfo.xml

%files tools
%license LICENSES/GPL-2.0-or-later.txt LICENSES/GPL-2.0-only.txt
%{_bindir}/cam
%{_bindir}/libcamera-bug-report

%changelog
* Sun Nov 01 2026 fairyband <zl3004431@gmail.com> - 1:0.7.2-103.caihong
- Rebuild from Osilvfe/libcamera b297636af143 for the hardware Camera ICP/BPS
  path. Disable simple IPA and the GPU software ISP, and obsolete libcamera-ipa.
  qcam remains a subpackage but the Fedora image still does not install it.
* Thu Oct 22 2026 Caihong Maintainers <caihong@example.invalid> - 1:0.7.2-102.caihong
- Serialize ControlLists without a ControlIdMap as libcamera controls, fixing
  the soft ISP worker abort on Camera::start() from PipeWire, and drop the
  ControlIdMap lookup fallback of 101, which crashed the PipeWire daemon.
- Grant the active seat user access to /dev/dma_heap/system so the software
  ISP works in the desktop session without the video group.
* Wed Oct 21 2026 Caihong Maintainers <caihong@example.invalid> - 1:0.7.2-101.caihong
- Recover ControlInfoMap handles by ControlIdMap in the control serializer,
  fixing the software ISP proxy worker abort that left PipeWire camera nodes
  unconfigured.
- Build from https://github.com/FairyBand/libcamera/tree/caihong-camera.
* Thu Oct 15 2026 Caihong Maintainers <caihong@example.invalid> - 1:0.7.2-100.caihong
- Build libcamera with OnePlus Pad Pro Caihong camera support.
