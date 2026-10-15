SHELL := /bin/bash

.PHONY: srpm

# Copr invokes this target as:
#   make -f .copr/Makefile srpm outdir=... spec=...
srpm:
	@set -euo pipefail; \
		test -n "$(outdir)"; \
		test -n "$(spec)"; \
		dnf -y install rpm-build rpmdevtools; \
		spec_path="$$(realpath "$(spec)")"; \
		test -f "$$spec_path"; \
		topdir="$$(mktemp -d)"; \
		trap 'rm -rf "$$topdir"' EXIT; \
		mkdir -p "$$topdir"/{BUILD,BUILDROOT,RPMS,SOURCES,SPECS,SRPMS}; \
		cp SOURCES/* "$$topdir/SOURCES/" 2>/dev/null || :; \
		spec_name="$$(basename "$$spec_path")"; \
		cp "$$spec_path" "$$topdir/SPECS/$$spec_name"; \
		spectool -g -C "$$topdir/SOURCES" "$$topdir/SPECS/$$spec_name"; \
		rpmbuild -bs --define "_topdir $$topdir" "$$topdir/SPECS/$$spec_name"; \
		find "$$topdir/SRPMS" -maxdepth 1 -type f -name '*.src.rpm' -exec cp -p {} "$(outdir)/" \;
