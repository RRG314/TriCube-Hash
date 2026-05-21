#!/usr/bin/env python3
"""Availability screen for optional external statistical batteries."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from _bootstrap import ensure_import_path

ensure_import_path()

from common import STATUS_BLOCKED, STATUS_NOT_RUN, command_exists, parse_variants  # noqa: E402
from _output import screen_metadata, write_single_screen  # noqa: E402


TOOLS = [
    ("PractRand", "RNG_test", "PractRand 256 MiB quick screen"),
    ("SmokeRand", "smokerand", "SmokeRand express"),
    ("TestU01 SmallCrush", "testu01_stdin32", "SmallCrush stdin32 wrapper"),
    ("Dieharder", "dieharder", "Dieharder full battery"),
    ("NIST STS", "assess", "NIST STS assess binary"),
]


def run_screen(variants: list[str]) -> list[dict[str, Any]]:
    rows = []
    for variant in variants:
        for name, binary, purpose in TOOLS:
            exists = command_exists(binary)
            rows.append(
                {
                    "screen": "external statistical battery",
                    "variant": variant,
                    "tool": name,
                    "binary": binary,
                    "purpose": purpose,
                    "status": STATUS_NOT_RUN if exists else STATUS_BLOCKED,
                    "notes": "tool detected but not launched by this quick internal run" if exists else "external tool not installed or not on PATH",
                }
            )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variants", default="baseline,fast8x")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    variants = parse_variants(args.variants)
    rows = run_screen(variants)
    write_single_screen(args.out, "external_batteries", rows, screen_metadata(variants=variants))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

