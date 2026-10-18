#!/bin/sh
# SPDX-License-Identifier: GPL-2.0-only
# Copyright (c) 2026 fairyband <zl3004431@gmail.com>
#
# Build the SRPM for one spec and run its %prep stage, which verifies source
# signatures and applies every patch.  Build dependencies are not installed,
# so this checks packaging inputs, not compilation.
set -eu

spec=${1:?usage: scripts/check-srpm.sh SPECS/name.spec}
repo=$(cd -- "$(dirname -- "$0")/.." && pwd)
topdir="$repo/.rpmbuild"

make -C "$repo" srpm SPEC="$spec"
srpm=$(find "$topdir/SRPMS" -maxdepth 1 -type f -name '*.src.rpm' -print -quit)
[ -n "$srpm" ] || { echo "no SRPM produced for $spec" >&2; exit 1; }

rpmbuild -rp --nodeps --define "_topdir $topdir" "$srpm"
echo "prep ok: $(basename "$srpm")"
