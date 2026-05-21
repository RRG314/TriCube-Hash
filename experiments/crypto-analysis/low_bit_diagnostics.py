#!/usr/bin/env python3
"""Run TriCube low-bit diagnostics only."""

from __future__ import annotations

import argparse
from pathlib import Path

from common import environment, group_by_status, parse_variants, write_csv, write_json, write_summary_md
from run_all_screens import low_bit_screen


def main() -> int:
    parser = argparse.ArgumentParser(description="Run low-bit diagnostics for TriCube stream variants.")
    parser.add_argument("--variants", default="baseline,fast8x")
    parser.add_argument("--bytes", type=int, default=16_777_216)
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    variants = parse_variants(args.variants)
    rows = low_bit_screen(variants, args.bytes, args.seed)
    args.out.mkdir(parents=True, exist_ok=True)
    metadata = environment()
    metadata.update({"variants": variants, "seed": args.seed, "bytes": args.bytes})
    write_json(args.out / "summary.json", {"metadata": metadata, "status_counts": group_by_status(rows), "low_bit_diagnostics": rows})
    write_csv(args.out / "low_bit_diagnostics.csv", rows)
    write_summary_md(
        args.out / "low_bit_diagnostics.md",
        "Low-Bit Diagnostic Screen",
        "Internal low-bit diagnostics are weaker than PractRand. If these diagnostics miss a PractRand warning, PractRand remains the stronger signal.",
        rows,
    )
    write_summary_md(
        args.out / "summary.md",
        "TriCube Low-Bit Diagnostic Summary",
        "This standalone run checks low-bit behavior only. It is a development screen, not a replacement for PractRand or formal analysis.",
        rows,
    )
    print(f"wrote {args.out}")
    print(group_by_status(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
