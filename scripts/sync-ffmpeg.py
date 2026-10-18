#!/usr/bin/python3 -I
# SPDX-License-Identifier: GPL-2.0-only
# Copyright (c) 2026 fairyband <zl3004431@gmail.com>
"""Regenerate the Caihong ffmpeg package from Fedora dist-git.

The spec is always rebuilt from Fedora's pristine rpms/ffmpeg spec, so running
this twice for the same dist-git commit produces identical files.  Caihong
changes are applied on top:

* Epoch 1 and a DNF5 override keep this build ahead of Fedora's ffmpeg-free.
* Patch100/Patch101 fix the Qualcomm Iris V4L2 M2M encoder.
* The h264/hevc V4L2 M2M hardware decoders are enabled.

Usage: scripts/sync-ffmpeg.py [--branch f44] [--commit SHA]
Prints "changed" or "unchanged" on the last line.
"""

import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request

DIST_GIT = "https://src.fedoraproject.org/rpms/ffmpeg.git"
LOOKASIDE = "https://src.fedoraproject.org/repo/pkgs/rpms/ffmpeg"
AUTHOR = "fairyband <zl3004431@gmail.com>"

# Bump when the Caihong patches change without a Fedora update.
CAIHONG_RELEASE = 1
EPOCH = 1
EXTRA_DECODERS = ["h264_v4l2m2m", "hevc_v4l2m2m"]
CAIHONG_PATCHES = [
    (100, "ffmpeg-v4l2-swframe-padding.patch",
     "Fix a source over-read when the driver pads the buffer height (1080->1088)."),
    (101, "ffmpeg-v4l2-enc-global-header.patch",
     "Provide extradata for global-header muxers (Matroska, OBS custom output)\n"
     "# and stop emitting picture-less header packets."),
]
OVERRIDE_FILE = "99-caihong-ffmpeg.repo"
OVERRIDE_SOURCE = 30

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES = os.path.join(ROOT, "SOURCES")
SPEC_OUT = os.path.join(ROOT, "SPECS", "ffmpeg-caihong.spec")


def fail(message):
    print(f"sync-ffmpeg: {message}", file=sys.stderr)
    sys.exit(1)


def run(*args, cwd=None):
    # rpm changelog dates must be English regardless of the caller's locale.
    env = dict(os.environ, LC_ALL="C")
    return subprocess.run(args, cwd=cwd, check=True, text=True, env=env,
                          stdout=subprocess.PIPE).stdout.strip()


def write_if_changed(path, data):
    mode = "wb" if isinstance(data, bytes) else "w"
    old = None
    if os.path.exists(path):
        with open(path, "rb" if mode == "wb" else "r") as f:
            old = f.read()
    if old == data:
        return False
    with open(path, mode) as f:
        f.write(data)
    return True


def fetch_lookaside(name, digest):
    url = f"{LOOKASIDE}/{name}/sha512/{digest}/{name}"
    with urllib.request.urlopen(url, timeout=60) as response:
        data = response.read()
    if hashlib.sha512(data).hexdigest() != digest:
        fail(f"lookaside checksum mismatch for {name}")
    return data


def add_decoders(text):
    lines = text.splitlines()
    for decoder in EXTRA_DECODERS:
        names = [line.split()[0] if line.strip() else "" for line in lines]
        if decoder in names:
            continue
        # Keep Fedora's order: insert after the last entry that sorts before us.
        index = 0
        for i, name in enumerate(names):
            if name and not name.startswith("#") and name < decoder:
                index = i + 1
        lines.insert(index, f"{decoder} # hardware")
    return "\n".join(lines) + "\n"


def transform_spec(spec, commit, branch, commit_date):
    out = []
    patch_lines = []
    seen = {"release": False, "s20": False, "s21": False,
            "install": False, "files": False, "changelog": False}

    for line in spec.splitlines():
        m = re.match(r"^Release:(\s+)(\S+)%\{\?dist\}\s*$", line)
        if m:
            out.append(f"{'Epoch:':<{len('Release:') + len(m.group(1))}}{EPOCH}")
            out.append(f"Release:{m.group(1)}{m.group(2)}%{{?dist}}.caihong{CAIHONG_RELEASE}")
            seen["release"] = True
            continue

        m = re.match(r"^(Source2[01]):(\s+)(enable_(?:de|en)coders)\s*$", line)
        if m:
            key = "s20" if m.group(1) == "Source20" else "s21"
            out.append(f"{m.group(1)}:{m.group(2)}ffmpeg-{m.group(3)}")
            seen[key] = True
            continue

        m = re.match(r"^(Patch\d+):(\s+)(\S+)\s*$", line)
        if m:
            target = m.group(3)
            if "://" in target:
                # Fedora keeps URL patches in dist-git too; spectool would hit
                # the gitweb bot check page, so use the committed file.
                local = target.rsplit("#/", 1)[-1] if "#/" in target else target.rsplit("/", 1)[-1]
                out.append(f"# {target}")
                out.append(f"{m.group(1)}:{m.group(2)}{local}")
                patch_lines.append(local)
            else:
                out.append(line)
                patch_lines.append(target)
            continue

        # Our Epoch must be part of the exact inter-subpackage dependencies.
        line = line.replace("= %{version}-%{release}", "= %{epoch}:%{version}-%{release}")

        if line.startswith("%make_install") and not seen["install"]:
            out.append(line)
            out.append(f"install -Dpm 0644 %{{SOURCE{OVERRIDE_SOURCE}}} "
                       f"%{{buildroot}}%{{_sysconfdir}}/dnf/repos.override.d/{OVERRIDE_FILE}")
            seen["install"] = True
            continue

        if line == "%files -n libavcodec%{?pkg_suffix}":
            out.append(line)
            out.append(f"%config(noreplace) %{{_sysconfdir}}/dnf/repos.override.d/{OVERRIDE_FILE}")
            seen["files"] = True
            continue

        if line == "%changelog":
            out.append(line)
            out.append(f"* {commit_date} {AUTHOR} - {EPOCH}:%{{version}}-%{{release}}")
            out.append(f"- Caihong rebuild of Fedora rpms/ffmpeg {branch} {commit[:12]}")
            out.append("- fix V4L2 M2M encoder crash with driver-padded buffer heights")
            out.append("- provide V4L2 M2M encoder extradata for global-header muxers")
            out.append("- enable h264_v4l2m2m and hevc_v4l2m2m hardware decoders")
            out.append("- keep Fedora's ffmpeg-free out of DNF with Epoch 1 and a repo override")
            out.append("")
            seen["changelog"] = True
            continue

        out.append(line)

    missing = [key for key, ok in seen.items() if not ok]
    if missing:
        fail(f"Fedora spec layout changed, could not apply: {', '.join(missing)}")

    # Insert the Caihong sources and patches after the last Fedora patch.
    last_patch = max(i for i, line in enumerate(out) if re.match(r"^Patch\d+:", line))
    block = ["",
             "# Caihong: DNF5 override that keeps Fedora's ffmpeg-free out of the solver.",
             f"Source{OVERRIDE_SOURCE}:       {OVERRIDE_FILE}",
             "",
             "# Caihong: Qualcomm Iris (qcom-iris) V4L2 M2M encoder fixes."]
    for number, name, comment in CAIHONG_PATCHES:
        if any(re.match(rf"^Patch{number}:", line) for line in out):
            fail(f"Fedora now uses Patch{number}, renumber the Caihong patches")
        block.append(f"# {comment}")
        block.append(f"Patch{number}:       {name}")
    out[last_patch + 1:last_patch + 1] = block

    header = [
        "# Generated by scripts/sync-ffmpeg.py; do not edit by hand.",
        f"# caihong-sync: fedora-dist-git {branch} {commit}",
    ]
    return "\n".join(header + out) + "\n", patch_lines


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--branch", default="f44")
    parser.add_argument("--commit")
    args = parser.parse_args()
    if not re.fullmatch(r"f\d+|rawhide", args.branch):
        fail(f"unexpected branch name: {args.branch}")
    if args.commit and not re.fullmatch(r"[0-9a-f]{7,40}", args.commit):
        fail(f"commit must be a hexadecimal SHA: {args.commit}")

    for _, name, _ in CAIHONG_PATCHES:
        if not os.path.isfile(os.path.join(SOURCES, name)):
            fail(f"missing Caihong patch SOURCES/{name}")
    if not os.path.isfile(os.path.join(SOURCES, OVERRIDE_FILE)):
        fail(f"missing SOURCES/{OVERRIDE_FILE}")

    with tempfile.TemporaryDirectory() as work:
        dist = os.path.join(work, "ffmpeg")
        run("git", "clone", "-q", "-b", args.branch, DIST_GIT, dist)
        if args.commit:
            run("git", "checkout", "-q", args.commit, cwd=dist)
        commit = run("git", "rev-parse", "HEAD", cwd=dist)
        commit_date = run("git", "log", "-1", "--date=format:%a %b %d %Y",
                          "--format=%cd", cwd=dist)
        # Fedora changelogs write single-digit days without a leading zero.
        commit_date = re.sub(r" 0(\d) ", r" \1 ", commit_date)

        with open(os.path.join(dist, "ffmpeg.spec")) as f:
            spec, patches = transform_spec(f.read(), commit, args.branch, commit_date)

        changed = write_if_changed(SPEC_OUT, spec)

        for name in patches:
            src = os.path.join(dist, name)
            if not os.path.isfile(src):
                fail(f"dist-git commit {commit} lacks patch file {name}")
            if not name.startswith("ffmpeg"):
                fail(f"patch {name} would collide in the shared SOURCES directory")
            with open(src, "rb") as f:
                changed |= write_if_changed(os.path.join(SOURCES, name), f.read())

        for kind in ("decoders", "encoders"):
            with open(os.path.join(dist, f"enable_{kind}")) as f:
                text = f.read()
            if kind == "decoders":
                text = add_decoders(text)
            changed |= write_if_changed(os.path.join(SOURCES, f"ffmpeg-enable_{kind}"), text)

        # Tarball and signature come from ffmpeg.org through spectool; only the
        # keyring has to come from the lookaside cache.
        with open(os.path.join(dist, "sources")) as f:
            for line in f:
                m = re.match(r"^SHA512 \((\S+)\) = ([0-9a-f]{128})$", line.strip())
                if not m:
                    continue
                name, digest = m.groups()
                if name.endswith(".tar.xz") or name.endswith(".asc"):
                    continue
                path = os.path.join(SOURCES, name)
                if os.path.exists(path):
                    with open(path, "rb") as existing:
                        if hashlib.sha512(existing.read()).hexdigest() == digest:
                            continue
                changed |= write_if_changed(path, fetch_lookaside(name, digest))

    print("changed" if changed else "unchanged")


if __name__ == "__main__":
    main()
