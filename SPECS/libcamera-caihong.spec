%global commit 38ca4ecae71f3a35e14345b18359a19df27a6b80

Name:           libcamera
Epoch:          1
Version:        0.7.2
Release:        101.caihong%{?dist}
Summary:        Camera support library with OnePlus Pad Pro Caihong support

License:        LGPL-2.1-or-later
URL:             https://github.com/FairyBand/libcamera/tree/caihong-camera
Source0:        https://github.com/FairyBand/libcamera/archive/%{commit}/libcamera-%{commit}.tar.gz
Source1:        70-libcamera.rules
Source2:        qcam.desktop
Source3:        qcam.metainfo.xml
Source4:        99-caihong-libcamera.repo

# Keep the Fedora package name so Fedora applications continue to resolve the
# normal libcamera SONAME and RPM provides.  The custom release is higher than
# Fedora 44's current 0.7.2-2 build.
Provides:       libcamera-caihong = %{epoch}:%{version}-%{release}

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
libcamera built from the Caihong branch for the OnePlus Pad Pro. This build
keeps the simple pipeline, Caihong sensor tuning, GPU software ISP, GStreamer
plugin, qcam and signed IPA modules required by the device.

%package devel
Summary:        Development files for %{name}
Requires:       %{name}%{?_isa} = %{?epoch:%{epoch}:}%{version}-%{release}

%description devel
Development files for applications using libcamera.

%package ipa
Summary:        ISP IPA plugins for %{name}
Requires:       %{name}%{?_isa} = %{?epoch:%{epoch}:}%{version}-%{release}

%description ipa
The Caihong simple pipeline IPA module, proxy and sensor tuning data.

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
# Keep these options aligned with scripts/install-caihong-libcamera-rootfs.sh.
%meson \
    -Dandroid=disabled \
    -Dapps-output-dng=disabled \
    -Dcam=enabled \
    -Dcam-output-kms=disabled \
    -Dcam-output-sdl2=disabled \
    -Ddocumentation=disabled \
    -Dgstreamer=enabled \
    -Dipas=simple \
    -Dlc-compliance=disabled \
    -Dlibdw=disabled \
    -Dlibunwind=disabled \
    -Dpipelines=simple \
    -Dpycamera=disabled \
    -Dqcam=enabled \
    -Drpi-awb-nn=disabled \
    -Dsoftisp-gpu=enabled \
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
ipas=simple
softisp_gpu=enabled
lens_shading=dynamic
lens_shading_calibration=nvmem-per-device
awb_calibration=nvmem-per-device
auto_contrast=dynamic
ae_controls=full
awb_controls=full
autofocus=contrast-detect
noise_reduction=dynamic
sharpness=dynamic
camera_flash=dual-v4l2
camera_flash_sync=frame-start-request-queue
camera_flash_torch_stop=led-mode
sensor_control_sync=raw-sof-timestamp
software_isp_startup_controls=enabled
frame_duration_limits=vblank-dynamic
ae_convergence=bounded-ratio
default_max_frame_duration_us=100000
digital_gain_max=1.0
gstreamer_camera_controls=flash-nr-cct
gstreamer=enabled
qcam=enabled
EOF
chmod 0644 %{buildroot}%{_datadir}/caihong/libcamera-build-info

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

%files ipa
%license LICENSES/LGPL-2.1-or-later.txt LICENSES/BSD-2-Clause.txt
%{_datadir}/libcamera/
%{_libdir}/libcamera/
%{_libexecdir}/libcamera/

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
* Wed Oct 21 2026 Caihong Maintainers <caihong@example.invalid> - 1:0.7.2-101.caihong
- Recover ControlInfoMap handles by ControlIdMap in the control serializer,
  fixing the software ISP proxy worker abort that left PipeWire camera nodes
  unconfigured.
- Build from https://github.com/FairyBand/libcamera/tree/caihong-camera.
* Thu Oct 15 2026 Caihong Maintainers <caihong@example.invalid> - 1:0.7.2-100.caihong
- Build libcamera with OnePlus Pad Pro Caihong camera support.
