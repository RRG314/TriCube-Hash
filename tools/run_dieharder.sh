#!/usr/bin/env bash
set -euo pipefail

BYTES="${1:-1073741824}"
SEED="${SEED:-123}"
DIEHARDER="${DIEHARDER:-dieharder}"

make -C c all >/dev/null
c/build/tricube stream --seed "$SEED" --bytes "$BYTES" --out - \
  | "$DIEHARDER" -g 200 -a

