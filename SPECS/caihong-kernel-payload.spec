%global payload_name caihong-kernel-payload-%{version}

Name:           caihong-kernel-payload
Version:        0.1.0
Release:        100.caihong%{?dist}
Summary:        Caihong kernel, DTB, boot images and modules payload
License:        GPL-2.0-only and Redistributable firmware
URL:            https://github.com/osilvfe/caihong-linux-rootfs
Source0:        %{payload_name}.tar.zst
Requires:       caihong-kernel-updater = %{version}-%{release}

%description
Release-specific payload consumed by caihong-kernel-updater. The source archive
must contain Image, caihong.dtb, boot-linux.img, boot-userdata.img,
kernel-release and modules/<kernel-release>. This package is intentionally
separate because the kernel build and Android boot image generation are not
part of the userspace Copr build.

%prep
%setup -q -n %{payload_name}

%build

%install
install -Dpm 0644 Image %{buildroot}%{_prefix}/lib/linux-caihong/Image
install -Dpm 0644 caihong.dtb %{buildroot}%{_prefix}/lib/linux-caihong/caihong.dtb
install -Dpm 0644 boot-linux.img %{buildroot}%{_prefix}/lib/linux-caihong/boot-linux.img
install -Dpm 0644 boot-userdata.img %{buildroot}%{_prefix}/lib/linux-caihong/boot-userdata.img
install -Dpm 0644 kernel-release %{buildroot}%{_prefix}/lib/linux-caihong/kernel-release
cp -a --no-preserve=ownership modules %{buildroot}%{_prefix}/lib/linux-caihong/

%check
test -s %{buildroot}%{_prefix}/lib/linux-caihong/Image
test -s %{buildroot}%{_prefix}/lib/linux-caihong/caihong.dtb
test -s %{buildroot}%{_prefix}/lib/linux-caihong/boot-linux.img
test -s %{buildroot}%{_prefix}/lib/linux-caihong/boot-userdata.img
test -s %{buildroot}%{_prefix}/lib/linux-caihong/kernel-release

%files
%license LICENSE
%{_prefix}/lib/linux-caihong/Image
%{_prefix}/lib/linux-caihong/caihong.dtb
%{_prefix}/lib/linux-caihong/boot-linux.img
%{_prefix}/lib/linux-caihong/boot-userdata.img
%{_prefix}/lib/linux-caihong/kernel-release
%{_prefix}/lib/linux-caihong/modules/

%changelog
* Fri Oct 16 2026 Caihong Maintainers <caihong@example.invalid> - 0.1.0-100.caihong
- Define the release-specific kernel payload consumed by the updater.
