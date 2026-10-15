%global rootfs_commit 4a343b670fcc5892be01857bc79cdb656a79787e
%global rootfs_name caihong-linux-rootfs-%{rootfs_commit}

Name:           caihong-firmware
Version:        0.1.0
Release:        100.caihong%{?dist}
Summary:        OnePlus Pad Pro Caihong firmware payloads
License:        Redistributable, no modification permitted
URL:            https://github.com/osilvfe/caihong-linux-rootfs
Source0:        https://github.com/osilvfe/caihong-linux-rootfs/archive/%{rootfs_commit}.tar.gz
BuildArch:      noarch

%description
Qualcomm ADSP/CDSP, GPU, WLAN/Bluetooth, display, touch, camera-support and
audio firmware for the OnePlus Pad Pro Caihong. Files are installed below
the Fedora firmware `updates` search path so the package does not claim files
owned by Fedora's linux-firmware package.

%prep
%setup -q -n %{rootfs_name}

%build

%install
install -dpm 0755 %{buildroot}%{_prefix}/lib/firmware/updates
cp -a --no-preserve=ownership firmware/. \
    %{buildroot}%{_prefix}/lib/firmware/updates/
rm -f %{buildroot}%{_prefix}/lib/firmware/updates/SHA256SUMS \
    %{buildroot}%{_prefix}/lib/firmware/updates/SOURCE.md
rm -f %{buildroot}%{_prefix}/lib/firmware/updates/regulatory.db \
    %{buildroot}%{_prefix}/lib/firmware/updates/regulatory.db.p7s

%check
test -s %{buildroot}%{_prefix}/lib/firmware/updates/qcom/sm8650/Oneplus/caihong/adsp.mbn
test -s %{buildroot}%{_prefix}/lib/firmware/updates/ath12k/WCN7850/hw2.0/caihong/amss.bin

%files
%license LICENSE
%{_prefix}/lib/firmware/updates/ath12k/
%{_prefix}/lib/firmware/updates/awinic/
%{_prefix}/lib/firmware/updates/novatek/
%{_prefix}/lib/firmware/updates/qca/
%{_prefix}/lib/firmware/updates/qcom/

%changelog
* Fri Oct 16 2026 Caihong Maintainers <caihong@example.invalid> - 0.1.0-100.caihong
- Package Caihong firmware under the firmware updates search path.
