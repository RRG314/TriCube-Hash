#!/usr/bin/env bash
set -euo pipefail

BATTERY="${1:-smallcrush}"
BYTES="${2:-1073741824}"
SEED="${SEED:-123}"
VARIANT="${VARIANT:-baseline}"
TESTU01_STDIN="${TESTU01_STDIN:-testu01_stdin32}"

make -C c all >/dev/null
c/build/tricube stream --seed "$SEED" --bytes "$BYTES" --out - --variant "$VARIANT" \
  | "$TESTU01_STDIN" "$BATTERY"
