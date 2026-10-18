%global rootfs_commit de106319349c0a8575f5b4047c942fb025c29197
%global rootfs_name caihong-linux-rootfs-%{rootfs_commit}

Name:           caihong-audio
Version:        0.1.0
Release:        101.caihong%{?dist}
Summary:        Caihong Qualcomm AudioReach topology and UCM data
License:        Redistributable, no modification permitted
URL:            https://github.com/FairyBand/caihong-linux-rootfs
Source0:        https://github.com/FairyBand/caihong-linux-rootfs/archive/%{rootfs_commit}.tar.gz
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
install -Dpm 0644 rootfs/caihong/usr/share/alsa/ucm2/Qualcomm/sm8650/Caihong/HiFi.conf \
    %{buildroot}%{_datadir}/alsa/ucm2/Qualcomm/sm8650/Caihong/HiFi.conf
install -Dpm 0644 rootfs/caihong/usr/share/alsa/ucm2/conf.d/sm8650/SM8650-MTP.conf \
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
* Sun Oct 18 2026 fairyband <zl3004431@gmail.com> - 0.1.0-101.caihong
- Build from the FairyBand fork, fedora branch.

* Fri Oct 16 2026 Caihong Maintainers <caihong@example.invalid> - 0.1.0-100.caihong
- Package Caihong UCM2 and AudioReach topology data.
