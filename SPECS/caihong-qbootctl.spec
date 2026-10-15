%global commit 39a6e6daaf029fb0a083777679a15ea2c18f72de
%global source_name qbootctl-%{commit}

Name:           caihong-qbootctl
Version:        0.1.0
Release:        100.caihong%{?dist}
Summary:        Android boot image slot control utility for Caihong
License:        GPL-2.0-or-later
URL:            https://github.com/linux-msm/qbootctl
Source0:        https://github.com/linux-msm/qbootctl/archive/%{commit}.tar.gz
BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  meson
BuildRequires:  ninja-build
BuildRequires:  pkgconfig(blkid)
BuildRequires:  systemd-devel
Provides:       qbootctl = %{version}-%{release}

%description
The qbootctl utility used by Caihong to inspect Android boot v2 slot metadata
and mark the currently running slot successful. It does not change the active
slot during normal Fedora boot.

%prep
%setup -q -n %{source_name}

%build
%meson --prefix=%{_prefix}/local --bindir=sbin
%meson_build

%install
%meson_install

%check
test -x %{buildroot}%{_prefix}/local/sbin/qbootctl

%files
%license LICENSE
%{_prefix}/local/sbin/qbootctl

%changelog
* Fri Oct 16 2026 Caihong Maintainers <caihong@example.invalid> - 0.1.0-100.caihong
- Package qbootctl for Caihong A/B slot integration.
