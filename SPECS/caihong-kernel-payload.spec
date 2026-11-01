%global payload_name caihong-kernel-payload-%{version}

Name:           caihong-kernel-payload
# The version is the kernel release, with the characters rpm rejects in a
# version segment replaced.  The rootfs repository builds the source archive
# under exactly this name and publishes it on the rolling kernel-payload release
# tag.  Because the version names the kernel, dnf can never pair a new module
# tree with an old boot image, and two kernels never look like the same package.
Version:        7.3.0_gad6d37f6d42a
Release:        1.caihong%{?dist}
Summary:        Caihong kernel, DTB, boot images and modules payload
License:        GPL-2.0-only and Redistributable firmware
URL:            https://github.com/FairyBand/caihong-linux-rootfs
Source0:        https://github.com/FairyBand/caihong-linux-rootfs/releases/download/kernel-payload/%{payload_name}.tar.zst
BuildArch:      noarch
# No version constraint: the updater is the same for every payload, and pinning
# its version here would make an unrelated updater rebuild block kernel updates.
Requires:       caihong-kernel-updater
Requires:       findutils
Requires:       kmod
Requires:       util-linux

%description
Release-specific payload consumed by caihong-kernel-updater. The source archive
must contain Image, caihong.dtb, boot-linux.img, boot-userdata.img,
kernel-release and modules/<kernel-release>. This package is intentionally
separate because the kernel build and Android boot image generation are not
part of the userspace Copr build.

Installing it only stages the new payload under %{_prefix}/lib/linux-caihong.
No scriptlet writes to a raw block device: caihong-kernel-install flashes the
staged payload to the running slot, so an RPM transaction can never leave the
device unbootable.

%prep
# The payload tar stores files at its root. -c creates %{payload_name} first.
# kernel-release and the module directory keep the booted uname -r, including
# the dash that RPM cannot put in Version.
%setup -q -c -n %{payload_name}

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

# RPM Version replaces every character Version cannot contain. The marker and
# the single module directory must reverse to that Version and must stay the
# string uname -r will report, or the updater installs modules where the
# running kernel cannot see them.
release=$(cat %{buildroot}%{_prefix}/lib/linux-caihong/kernel-release)
test "$(printf '%%s' "$release" | sed 's/[^[:alnum:].+]/_/g')" = "%{version}"
test -d "%{buildroot}%{_prefix}/lib/linux-caihong/modules/$release"
test "$(find %{buildroot}%{_prefix}/lib/linux-caihong/modules -mindepth 1 -maxdepth 1 -type d | wc -l)" = 1
test -n "$(find "%{buildroot}%{_prefix}/lib/linux-caihong/modules/$release" -name '*.ko*' -print -quit)"

%files
%license LICENSE
%{_prefix}/lib/linux-caihong/Image
%{_prefix}/lib/linux-caihong/caihong.dtb
%{_prefix}/lib/linux-caihong/boot-linux.img
%{_prefix}/lib/linux-caihong/boot-userdata.img
%{_prefix}/lib/linux-caihong/kernel-release
%{_prefix}/lib/linux-caihong/modules/

%changelog
* Sun Nov 01 2026 fairyband <zl3004431@gmail.com> - 7.3.0_gad6d37f6d42a-1.caihong
- Point the payload at caihong-v7.3 ad6d37f6d42a, including Camera ICP/BPS.
  Unpack the flat archive and keep the module directory equal to uname -r.
* Thu Oct 22 2026 fairyband <zl3004431@gmail.com> - 7.2.0_00055_g8ad1569fc902-1.caihong
- Version the package by kernel release and fetch the source archive from the
  rolling kernel-payload release asset in the rootfs repository, so the payload
  is rebuilt by the Copr build instead of by hand.
- Check in %check that the marker, the archive directory and the package
  version all name the same kernel.

* Sun Oct 18 2026 fairyband <zl3004431@gmail.com> - 0.1.0-101.caihong
- Point the URL at the FairyBand fork.

* Fri Oct 16 2026 Caihong Maintainers <caihong@example.invalid> - 0.1.0-100.caihong
- Define the release-specific kernel payload consumed by the updater.
