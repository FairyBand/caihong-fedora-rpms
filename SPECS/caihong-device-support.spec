%global rootfs_commit de106319349c0a8575f5b4047c942fb025c29197
%global rootfs_name caihong-linux-rootfs-%{rootfs_commit}

Name:           caihong-device-support
Version:        0.1.0
Release:        101.caihong%{?dist}
Summary:        OnePlus Pad Pro Caihong device services and udev rules
License:        GPL-2.0-or-later
URL:            https://github.com/FairyBand/caihong-linux-rootfs
Source0:        https://github.com/FairyBand/caihong-linux-rootfs/archive/%{rootfs_commit}.tar.gz
Source1:        caihong-nvram-mac.c
Source2:        90-caihong-device-support.preset
Source3:        90-caihong-copr.repo

BuildRequires:  desktop-file-utils
BuildRequires:  systemd-rpm-macros
Requires:       bash
Requires:       bluez
Requires:       coreutils
Requires:       dnsmasq
Requires:       hostapd
Requires:       iw
Requires:       kmod
Requires:       NetworkManager
Requires:       caihong-qbootctl
Requires:       systemd
Requires:       util-linux
Requires:       v4l-utils
BuildRequires:  gcc
BuildRequires:  openssl-devel

%description
Device-specific userspace integration for the OnePlus Pad Pro Caihong Fedora
image: Pogo input rules, hardware MAC setup, Bluetooth startup, hotspot,
flashlight, pen pairing/charging, root filesystem growth and boot-slot tools.
SELinux policy is deliberately not included yet; the first Fedora image is
expected to collect AVC records in permissive mode.

%prep
%setup -q -n %{rootfs_name}

%build
%{__cc} %{optflags} %{?__global_ldflags} -o caihong-nvram-mac %{SOURCE1} -lcrypto

%install
install -Dpm 0755 caihong-nvram-mac %{buildroot}%{_prefix}/local/libexec/caihong-nvram-mac

for tool in \
    caihong-bluetooth-autostart caihong-flashlight caihong-hardware-mac \
    caihong-hotspot caihong-mark-boot-successful caihong-pen-autoconnect \
    caihong-pen-charge caihong-pen-pair caihong-slot; do
    install -Dpm 0755 rootfs/caihong/usr/local/sbin/$tool \
        %{buildroot}%{_prefix}/local/sbin/$tool
done

for unit in \
    caihong-bluetooth-autostart.service caihong-grow-rootfs.service \
    caihong-hardware-mac.service caihong-hotspot.service \
    caihong-mark-boot-successful.service caihong-pen-autoconnect.service \
    caihong-pen-autoconnect.timer caihong-pen-charge.service \
    caihong-pen-charge.timer caihong-pen-pair.service caihong-pen-pair.timer; do
    install -Dpm 0644 rootfs/caihong/etc/systemd/system/$unit \
        %{buildroot}%{_unitdir}/$unit
done

install -Dpm 0644 %{SOURCE3} \
    %{buildroot}%{_sysconfdir}/dnf/repos.override.d/90-caihong-copr.repo
install -Dpm 0644 %{SOURCE2} \
    %{buildroot}%{_prefix}/lib/systemd/system-preset/90-caihong-device-support.preset

for rule in 80-caihong-hotspot.rules 99-caihong-dma-heap.rules 99-caihong-pogo-input.rules; do
    install -Dpm 0644 rootfs/caihong/etc/udev/rules.d/$rule \
        %{buildroot}%{_udevrulesdir}/$rule
done

install -Dpm 0644 rootfs/caihong/etc/modules-load.d/caihong.conf \
    %{buildroot}%{_prefix}/lib/modules-load.d/caihong.conf
install -Dpm 0644 rootfs/caihong/etc/NetworkManager/conf.d/30-caihong-hotspot.conf \
    %{buildroot}%{_prefix}/lib/NetworkManager/conf.d/30-caihong-hotspot.conf
install -Dpm 0644 rootfs/caihong/etc/NetworkManager/conf.d/99-caihong-hardware-mac.conf \
    %{buildroot}%{_prefix}/lib/NetworkManager/conf.d/99-caihong-hardware-mac.conf
install -Dpm 0644 rootfs/caihong/etc/bluetooth/main.conf \
    %{buildroot}%{_sysconfdir}/bluetooth/main.conf
install -Dpm 0644 rootfs/caihong/etc/caihong-hotspot.conf \
    %{buildroot}%{_sysconfdir}/caihong-hotspot.conf
install -Dpm 0600 rootfs/caihong/etc/caihong-pen.json \
    %{buildroot}%{_sysconfdir}/caihong-pen.json
install -Dpm 0644 rootfs/caihong/usr/share/applications/caihong-switch-to-android.desktop \
    %{buildroot}%{_datadir}/applications/caihong-switch-to-android.desktop

%check
for tool in caihong-bluetooth-autostart caihong-flashlight caihong-hardware-mac \
    caihong-hotspot caihong-mark-boot-successful caihong-pen-autoconnect \
    caihong-pen-charge caihong-pen-pair caihong-slot; do
    test -x %{buildroot}%{_prefix}/local/sbin/$tool
done
desktop-file-validate %{buildroot}%{_datadir}/applications/caihong-switch-to-android.desktop

%post
%systemd_post caihong-bluetooth-autostart.service
%systemd_post caihong-grow-rootfs.service
%systemd_post caihong-hardware-mac.service
%systemd_post caihong-hotspot.service
%systemd_post caihong-mark-boot-successful.service
%systemd_post caihong-pen-autoconnect.service
%systemd_post caihong-pen-autoconnect.timer
%systemd_post caihong-pen-charge.service
%systemd_post caihong-pen-charge.timer
%systemd_post caihong-pen-pair.service
%systemd_post caihong-pen-pair.timer
udevadm control --reload-rules >/dev/null 2>&1 || :

%preun
%systemd_preun caihong-bluetooth-autostart.service
%systemd_preun caihong-grow-rootfs.service
%systemd_preun caihong-hardware-mac.service
%systemd_preun caihong-hotspot.service
%systemd_preun caihong-mark-boot-successful.service
%systemd_preun caihong-pen-autoconnect.service
%systemd_preun caihong-pen-autoconnect.timer
%systemd_preun caihong-pen-charge.service
%systemd_preun caihong-pen-charge.timer
%systemd_preun caihong-pen-pair.service
%systemd_preun caihong-pen-pair.timer

%postun
%systemd_postun_with_restart caihong-bluetooth-autostart.service
%systemd_postun_with_restart caihong-hardware-mac.service
%systemd_postun_with_restart caihong-hotspot.service
udevadm control --reload-rules >/dev/null 2>&1 || :

%files
%license LICENSE
%{_prefix}/local/libexec/caihong-nvram-mac
%{_prefix}/local/sbin/caihong-*
%{_unitdir}/caihong-*
%{_prefix}/lib/systemd/system-preset/90-caihong-device-support.preset
%{_udevrulesdir}/80-caihong-hotspot.rules
%{_udevrulesdir}/99-caihong-dma-heap.rules
%{_udevrulesdir}/99-caihong-pogo-input.rules
%{_prefix}/lib/modules-load.d/caihong.conf
%{_prefix}/lib/NetworkManager/conf.d/30-caihong-hotspot.conf
%{_prefix}/lib/NetworkManager/conf.d/99-caihong-hardware-mac.conf
%config(noreplace) %{_sysconfdir}/bluetooth/main.conf
%config(noreplace) %{_sysconfdir}/dnf/repos.override.d/90-caihong-copr.repo
%config(noreplace) %{_sysconfdir}/caihong-hotspot.conf
%config(noreplace) %{_sysconfdir}/caihong-pen.json
%{_datadir}/applications/caihong-switch-to-android.desktop

%changelog
* Sun Oct 18 2026 fairyband <zl3004431@gmail.com> - 0.1.0-101.caihong
- Build from the FairyBand fork, fedora branch (rootfs/caihong).
- Give the Caihong Copr repository priority 10 so its packages always win over
  same-named Fedora packages.

* Fri Oct 16 2026 Caihong Maintainers <caihong@example.invalid> - 0.1.0-100.caihong
- Package non-SELinux Caihong device services and udev integration.
