Name:           obs-studio-plugin-v4l2m2m
Version:        0.1.0
Release:        1.caihong%{?dist}
Summary:        OBS Studio hardware H.264/HEVC encoders for V4L2 M2M devices
License:        GPL-2.0-or-later
URL:            https://github.com/FairyBand/caihong-fedora-rpms
Source0:        obs-v4l2m2m.c
Source1:        obs-v4l2m2m-CMakeLists.txt
Source2:        obs-v4l2m2m-en-US.ini
Source3:        obs-v4l2m2m-zh-CN.ini
Source4:        obs-v4l2m2m-COPYING

BuildRequires:  cmake
BuildRequires:  gcc
BuildRequires:  kernel-headers
BuildRequires:  obs-studio-devel
BuildRequires:  pkgconfig(libavcodec)
BuildRequires:  pkgconfig(libavutil)

Requires:       obs-studio%{?_isa}
# The Caihong ffmpeg rebuild fixes the padded-height frame copy crash and
# provides the global stream header that OBS outputs need.
Requires:       libavcodec-free%{?_isa} >= 1:8.1.3

%description
Adds "V4L2 M2M H.264 (Hardware)" and "V4L2 M2M HEVC (Hardware)" to the OBS
Studio encoder list (Settings > Output in Advanced mode).  The encoders use
libavcodec's h264_v4l2m2m and hevc_v4l2m2m wrappers to drive stateful V4L2
memory-to-memory encoders such as the Qualcomm Iris video unit of the OnePlus
Pad Pro Caihong.  An encoder is only offered when a matching device exists.

%prep
%setup -q -c -T
cp -p %{SOURCE0} obs-v4l2m2m.c
cp -p %{SOURCE1} CMakeLists.txt
cp -p %{SOURCE4} COPYING
install -Dpm 0644 %{SOURCE2} data/locale/en-US.ini
install -Dpm 0644 %{SOURCE3} data/locale/zh-CN.ini

%build
%cmake
%cmake_build

%install
%cmake_install

%check
nm -D --defined-only %{buildroot}%{_libdir}/obs-plugins/obs-v4l2m2m.so | grep -q ' obs_module_load$'

%files
%license COPYING
%{_libdir}/obs-plugins/obs-v4l2m2m.so
%{_datadir}/obs/obs-plugins/obs-v4l2m2m/

%changelog
* Sun Oct 18 2026 fairyband <zl3004431@gmail.com> - 0.1.0-1.caihong
- Initial package: V4L2 M2M H.264/HEVC encoders for OBS Studio.
