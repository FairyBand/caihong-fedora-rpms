%global rootfs_commit 4a343b670fcc5892be01857bc79cdb656a79787e
%global rootfs_name caihong-linux-rootfs-%{rootfs_commit}

Name:           caihong-audio
Version:        0.1.0
Release:        100.caihong%{?dist}
Summary:        Caihong Qualcomm AudioReach topology and UCM data
License:        Redistributable, no modification permitted
URL:            https://github.com/osilvfe/caihong-linux-rootfs
Source0:        https://github.com/osilvfe/caihong-linux-rootfs/archive/%{rootfs_commit}.tar.gz
BuildArch:      noarch
Requires:       alsa-lib
Requires:       alsa-ucm

%description
Device-specific ALSA UCM2 and Qualcomm AudioReach topology data for the
OnePlus Pad Pro Caihong audio card. The topology is a runtime firmware asset;
it is not generated in the RPM build and is kept separate from SELinux policy.

%prep
%setup -q -n %{rootfs_name}

%build

%install
install -Dpm 0644 firmware/qcom/sm8650/SM8650-MTP-tplg.bin \
    %{buildroot}%{_prefix}/lib/firmware/updates/qcom/sm8650/SM8650-MTP-tplg.bin
install -Dpm 0644 rootfs/archlinuxarm/usr/share/alsa/ucm2/Qualcomm/sm8650/Caihong/HiFi.conf \
    %{buildroot}%{_datadir}/alsa/ucm2/Qualcomm/sm8650/Caihong/HiFi.conf
install -Dpm 0644 rootfs/archlinuxarm/usr/share/alsa/ucm2/conf.d/sm8650/SM8650-MTP.conf \
    %{buildroot}%{_datadir}/alsa/ucm2/conf.d/sm8650/SM8650-MTP.conf

%check
test -s %{buildroot}%{_prefix}/lib/firmware/updates/qcom/sm8650/SM8650-MTP-tplg.bin
test -s %{buildroot}%{_datadir}/alsa/ucm2/Qualcomm/sm8650/Caihong/HiFi.conf

%files
%license LICENSE
%{_prefix}/lib/firmware/updates/qcom/sm8650/SM8650-MTP-tplg.bin
%{_datadir}/alsa/ucm2/Qualcomm/sm8650/Caihong/HiFi.conf
%{_datadir}/alsa/ucm2/conf.d/sm8650/SM8650-MTP.conf

%changelog
* Fri Oct 16 2026 Caihong Maintainers <caihong@example.invalid> - 0.1.0-100.caihong
- Package Caihong UCM2 and AudioReach topology data.
