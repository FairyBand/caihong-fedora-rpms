Name:           caihong-kernel-updater
Version:        0.1.0
Release:        101.caihong%{?dist}
Summary:        Safe A/B slot updater for the Caihong kernel payload
License:        GPL-2.0-only
URL:            https://github.com/FairyBand/caihong-linux-rootfs
Source0:        install-current-slot
Source1:        caihong-kernel-install.service
Source2:        LICENSE
BuildArch:      noarch
BuildRequires:  systemd-rpm-macros
Requires:       coreutils
Requires:       findutils
Requires:       kmod
Requires:       systemd
Requires:       util-linux

%description
Installs a separately packaged Caihong kernel payload into the currently
running Android A/B slot. The updater detects the root PARTLABEL, writes only
the matching boot partition and reads it back for verification. It is exposed
as an explicit systemd service; the RPM transaction never writes raw block
devices. SELinux policy is intentionally deferred until permissive-mode AVC
collection is complete.

%prep

%build

%install
install -Dpm 0755 %{SOURCE0} \
    %{buildroot}%{_prefix}/lib/linux-caihong/install-current-slot
install -Dpm 0644 %{SOURCE1} \
    %{buildroot}%{_unitdir}/caihong-kernel-install.service
install -Dpm 0644 %{SOURCE2} \
    %{buildroot}%{_datadir}/licenses/%{name}/LICENSE
install -Dpm 0755 /dev/null \
    %{buildroot}%{_sbindir}/caihong-kernel-install
cat > %{buildroot}%{_sbindir}/caihong-kernel-install <<'EOF'
#!/bin/sh
exec systemctl start --no-block caihong-kernel-install.service
EOF

%check
sh -n %{buildroot}%{_prefix}/lib/linux-caihong/install-current-slot
sh -n %{buildroot}%{_sbindir}/caihong-kernel-install

%post
%systemd_post caihong-kernel-install.service

%preun
%systemd_preun caihong-kernel-install.service

%postun
%systemd_postun_with_restart caihong-kernel-install.service

%files
%license %{_datadir}/licenses/%{name}/LICENSE
%{_prefix}/lib/linux-caihong/install-current-slot
%{_unitdir}/caihong-kernel-install.service
%{_sbindir}/caihong-kernel-install

%changelog
* Sun Oct 18 2026 fairyband <zl3004431@gmail.com> - 0.1.0-101.caihong
- Point the URL at the FairyBand fork.

* Fri Oct 16 2026 Caihong Maintainers <caihong@example.invalid> - 0.1.0-100.caihong
- Package explicit A/B kernel installation without SELinux policy.
