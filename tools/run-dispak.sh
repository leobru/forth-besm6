#!/bin/sh
# Run dispak with an isolated HOME (build/home) and the private image disk
# (build/disk) ahead of the system volumes.  Usage: tools/run-dispak.sh ARGS...
set -eu
root=$(cd "$(dirname "$0")/.." && pwd)
mkdir -p "$root/build/home/.besm6" "$root/build/disk"
HOME="$root/build/home"
export HOME
unset BESM6_PATH BESM6_SMALL_DISKS || true
exec "${DISPAK:-dispak}" --path="$root/build/disk:${SYSTEM_DISKS:-/usr/local/share/besm6}" "$@"
