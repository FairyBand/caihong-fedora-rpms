SPECS := $(wildcard SPECS/*.spec)

.PHONY: spec-check
spec-check:
	@set -eu; for spec in $(SPECS); do \
		rpmspec -P "$$spec" >/dev/null; \
		done
	@echo "all specs parse"
