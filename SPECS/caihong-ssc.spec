%global rootfs_commit de106319349c0a8575f5b4047c942fb025c29197
%global rootfs_name caihong-linux-rootfs-%{rootfs_commit}
%global debug_package %{nil}

Name:           caihong-ssc
Version:        0.1.0
Release:        101.caihong%{?dist}
Summary:        Caihong Qualcomm Sensor Subsystem userspace
License:        GPL-2.0-only
URL:            https://github.com/FairyBand/caihong-linux-rootfs
Source0:        https://github.com/FairyBand/caihong-linux-rootfs/archive/%{rootfs_commit}.tar.gz
Source1:        caihong-ssc.service
Source2:        90-caihong-ssc.rules
Source3:        iio-sensor-proxy.conf

BuildRequires:  systemd-rpm-macros
Requires:       iio-sensor-proxy
Requires:       systemd
%description
Board-specific Qualcomm Sensor Subsystem listener and SensorProxy backend for
the OnePlus Pad Pro Caihong. The binary payload is taken from the validated
Caihong SSC bundle and is intentionally kept separate from SELinux policy.

%prep
%setup -q -n %{rootfs_name}

%build
# The SSC payload is supplied as prebuilt vendor userspace and DSP support
# files. It is never executed during the RPM build.

%install
install -Dpm 0755 firmware-assets/caihong-ssc/bin/hexagonrpcd \
    %{buildroot}%{_libexecdir}/caihong-ssc/hexagonrpcd
install -Dpm 0755 firmware-assets/caihong-ssc/bin/iio-sensor-proxy \
    %{buildroot}%{_libexecdir}/caihong-ssc/iio-sensor-proxy
install -Dpm 0755 firmware-assets/caihong-ssc/lib/libhexagonrpc.so.0.5 \
    %{buildroot}%{_libdir}/caihong-ssc/libhexagonrpc.so.0.5
install -Dpm 0755 firmware-assets/caihong-ssc/lib/libssc.so.2 \
    %{buildroot}%{_libdir}/caihong-ssc/libssc.so.2
install -Dpm 0644 %{SOURCE1} \
    %{buildroot}%{_unitdir}/caihong-ssc.service
sed -i \
    -e 's#/usr/local/libexec/caihong-ssc#%{_libexecdir}/caihong-ssc#g' \
    -e 's#/usr/local/lib/caihong-ssc#%{_libdir}/caihong-ssc#g' \
    %{buildroot}%{_unitdir}/caihong-ssc.service
install -Dpm 0644 %{SOURCE2} \
    %{buildroot}%{_udevrulesdir}/90-caihong-ssc.rules
install -Dpm 0644 %{SOURCE3} \
    %{buildroot}%{_unitdir}/iio-sensor-proxy.service.d/caihong-ssc.conf
sed -i \
    -e 's#/usr/local/libexec/caihong-ssc#%{_libexecdir}/caihong-ssc#g' \
    -e 's#/usr/local/lib/caihong-ssc#%{_libdir}/caihong-ssc#g' \
    %{buildroot}%{_unitdir}/iio-sensor-proxy.service.d/caihong-ssc.conf
install -dpm 0755 %{buildroot}%{_sharedstatedir}/caihong-ssc/root
cp -a --no-preserve=ownership firmware-assets/caihong-ssc/root/. \
    %{buildroot}%{_sharedstatedir}/caihong-ssc/root/

%check
test -x %{buildroot}%{_libexecdir}/caihong-ssc/hexagonrpcd
test -x %{buildroot}%{_libexecdir}/caihong-ssc/iio-sensor-proxy
test -s %{buildroot}%{_libdir}/caihong-ssc/libssc.so.2

%post
%systemd_post caihong-ssc.service
udevadm control --reload-rules >/dev/null 2>&1 || :

%preun
%systemd_preun caihong-ssc.service

%postun
%systemd_postun_with_restart caihong-ssc.service
udevadm control --reload-rules >/dev/null 2>&1 || :

%files
%license LICENSE
%{_libexecdir}/caihong-ssc/hexagonrpcd
%{_libexecdir}/caihong-ssc/iio-sensor-proxy
%{_libdir}/caihong-ssc/libhexagonrpc.so.0.5
%{_libdir}/caihong-ssc/libssc.so.2
%{_unitdir}/caihong-ssc.service
%{_unitdir}/iio-sensor-proxy.service.d/caihong-ssc.conf
%{_udevrulesdir}/90-caihong-ssc.rules
%dir %{_sharedstatedir}/caihong-ssc
%{_sharedstatedir}/caihong-ssc/root/

%changelog
* Sun Oct 18 2026 fairyband <zl3004431@gmail.com> - 0.1.0-101.caihong
- Build from the FairyBand fork, fedora branch.
- Drop the %pre scriptlet: %systemd_pre does not exist and broke installation.

* Fri Oct 16 2026 Caihong Maintainers <caihong@example.invalid> - 0.1.0-100.caihong
- Package the validated Caihong SSC runtime without SELinux policy.
