#!/usr/bin/env bash
set -euo pipefail

BYTES="${1:-1073741824}"
SEED="${SEED:-123}"
VARIANT="${VARIANT:-baseline}"
RNG_TEST="${RNG_TEST:-RNG_test}"

make -C c all >/dev/null
c/build/tricube stream --seed "$SEED" --bytes "$BYTES" --out - --variant "$VARIANT" \
  | "$RNG_TEST" stdin32 -tlmin 1KB -tlmax "$BYTES" -tf 2 -te 1
