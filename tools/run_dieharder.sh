#!/usr/bin/env bash
set -euo pipefail

BYTES="${1:-1073741824}"
SEED="${SEED:-123}"
VARIANT="${VARIANT:-baseline}"
DIEHARDER="${DIEHARDER:-dieharder}"

make -C c all >/dev/null
c/build/tricube stream --seed "$SEED" --bytes "$BYTES" --out - --variant "$VARIANT" \
  | "$DIEHARDER" -g 200 -a
