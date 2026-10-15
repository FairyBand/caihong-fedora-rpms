SPECS := $(wildcard SPECS/*.spec)
TOPDIR ?= $(CURDIR)/.rpmbuild

.PHONY: spec-check srpm
spec-check:
	@set -eu; for spec in $(SPECS); do \
		rpmspec -P "$$spec" >/dev/null; \
		done
	@echo "all specs parse"

# Build one uploadable SRPM.  spectool fetches URL-based sources into the
# temporary SOURCES directory; local payload archives can be pre-staged there.
srpm:
	@test -n "$(SPEC)" || { echo 'usage: make srpm SPEC=SPECS/name.spec' >&2; exit 2; }
	@test -f "$(SPEC)"
	@command -v spectool >/dev/null || { echo 'spectool is required (install rpmdevtools)' >&2; exit 127; }
	@command -v rpmbuild >/dev/null || { echo 'rpmbuild is required (install rpm-build)' >&2; exit 127; }
	@set -eu; \
		spec="$$(basename "$(SPEC)")"; \
		rm -rf "$(TOPDIR)"; \
		mkdir -p "$(TOPDIR)"/{SOURCES,SPECS,BUILD,BUILDROOT,RPMS,SRPMS}; \
		cp SOURCES/* "$(TOPDIR)/SOURCES/"; \
		cp "$(SPEC)" "$(TOPDIR)/SPECS/$$spec"; \
		spectool -g -C "$(TOPDIR)/SOURCES" "$(TOPDIR)/SPECS/$$spec"; \
		rpmbuild -bs --define "_topdir $(TOPDIR)" "$(TOPDIR)/SPECS/$$spec"; \
		printf 'SRPM: '; find "$(TOPDIR)/SRPMS" -maxdepth 1 -type f -name '*.src.rpm' -print -quit
