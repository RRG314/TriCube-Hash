#!/usr/bin/env bash
set -uo pipefail

BATTERY="${1:-express}"
BYTES="${2:-536870912}"
SEED="${SEED:-123}"
VARIANT="${VARIANT:-baseline}"
SMOKERAND="${SMOKERAND:-smokerand}"
UNBOUNDED="${UNBOUNDED:-0}"

make -C c all >/dev/null
if [[ "$UNBOUNDED" == "1" ]]; then
  c/build/tricube stream --seed "$SEED" --unbounded --out - --variant "$VARIANT" \
    | "$SMOKERAND" "$BATTERY" stdin64
else
  c/build/tricube stream --seed "$SEED" --bytes "$BYTES" --out - --variant "$VARIANT" \
    | "$SMOKERAND" "$BATTERY" stdin64
fi
exit "${PIPESTATUS[1]}"
