%global commit 45c187e328793c05e15694aa5a3f653653c300f4
%global source_name plasma-camera-%{commit}

Name:           plasma-camera
Epoch:          1
Version:        26.08.1
Release:        100.caihong%{?dist}
Summary:        Camera application with Caihong libcamera integration
License:        GPL-3.0-or-later
URL:            https://github.com/Osilvfe/plasma-camera
Source0:        https://github.com/Osilvfe/plasma-camera/archive/%{commit}.tar.gz

BuildRequires:  cmake
BuildRequires:  desktop-file-utils
BuildRequires:  extra-cmake-modules
BuildRequires:  gettext
BuildRequires:  kf6-kconfig-devel
BuildRequires:  kf6-kcoreaddons-devel
BuildRequires:  kf6-ki18n-devel
BuildRequires:  kf6-kirigami-devel
BuildRequires:  libcamera-devel
BuildRequires:  pkgconfig(exiv2)
BuildRequires:  ninja-build
BuildRequires:  pkgconfig(Qt6Core)
BuildRequires:  pkgconfig(Qt6Gui)
BuildRequires:  pkgconfig(Qt6Multimedia)
BuildRequires:  pkgconfig(Qt6Quick)
BuildRequires:  pkgconfig(Qt6QuickControls2)
BuildRequires:  pkgconfig(Qt6Sensors)
BuildRequires:  pkgconfig(Qt6Svg)
BuildRequires:  pkgconfig(Qt6Widgets)
Requires:       libcamera%{?_isa} >= 1:0.7.2-100.caihong
Requires:       qt6-qtbase
Requires:       qt6-qtmultimedia

%description
The Qt/KDE Plasma Camera application built from the Caihong branch. It is
usable inside a GNOME session and keeps the validated Caihong autofocus,
flashlight and libcamera controls. This package contains no SELinux policy.

%prep
%setup -q -n %{source_name}

%build
%cmake -G Ninja
%cmake_build

%install
%cmake_install
chmod 0644 %{buildroot}%{_datadir}/applications/org.kde.plasma.camera.desktop
install -dpm 0755 %{buildroot}%{_datadir}/caihong
cat > %{buildroot}%{_datadir}/caihong/plasma-camera-build-info << EOF
build=caihong
version=%{version}+caihong
source_commit=%{commit}
backend=libcamera-direct
EOF

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/org.kde.plasma.camera.desktop

%files
%license LICENSES/GPL-3.0-or-later.txt
%{_bindir}/plasma-camera
%{_datadir}/applications/org.kde.plasma.camera.desktop
%{_metainfodir}/org.kde.plasma.camera.appdata.xml
%{_datadir}/locale/*/LC_MESSAGES/plasma-camera.mo
%dir %{_datadir}/caihong
%{_datadir}/caihong/plasma-camera-build-info

%changelog
* Fri Oct 16 2026 Caihong Maintainers <caihong@example.invalid> - 1:26.08.1-100.caihong
- Build the Caihong Plasma Camera branch against Caihong libcamera.
