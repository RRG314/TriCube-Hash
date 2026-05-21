#!/usr/bin/env python3
"""Small black-box algebraic degree screen for TriCube stream variants."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from _bootstrap import ensure_import_path

ensure_import_path()

from common import STATUS_PASS, STATUS_WARN, anf_degree, digest32, mean, parse_variants  # noqa: E402
from _output import screen_metadata, write_single_screen  # noqa: E402


def run_screen(variants: list[str], variable_count: int, output_bits: int, seed: int) -> list[dict[str, Any]]:
    if variable_count > 12:
        raise ValueError("variable_count above 12 is intentionally blocked for this black-box screen")
    rows: list[dict[str, Any]] = []
    positions = [((i * 13) % 64) for i in range(variable_count)]
    assignments = 1 << variable_count
    for variant in variants:
        outputs = []
        for mask in range(assignments):
            s = seed
            for i, pos in enumerate(positions):
                if (mask >> i) & 1:
                    s ^= 1 << pos
            outputs.append(digest32(variant, s))
        degrees: list[int] = []
        for bit_idx in range(output_bits):
            table = []
            byte_idx = bit_idx // 8
            bit_in_byte = bit_idx % 8
            for out in outputs:
                table.append((out[byte_idx] >> bit_in_byte) & 1)
            degrees.append(anf_degree(table))
        low = sum(1 for d in degrees if d <= max(0, variable_count - 2))
        max_degree = max(degrees) if degrees else 0
        status = STATUS_WARN if low > 0 or max_degree < variable_count - 1 else STATUS_PASS
        rows.append(
            {
                "screen": "small black-box algebraic degree screen",
                "variant": variant,
                "variables": variable_count,
                "assignments": assignments,
                "output_bits": output_bits,
                "variable_positions": ",".join(str(p) for p in positions),
                "min_degree": min(degrees) if degrees else 0,
                "mean_degree": round(mean([float(x) for x in degrees]), 4),
                "max_degree": max_degree,
                "low_degree_outputs": low,
                "status": status,
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variants", default="baseline,fast8x")
    parser.add_argument("--variables", type=int, default=8)
    parser.add_argument("--output-bits", type=int, default=32)
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    variants = parse_variants(args.variants)
    rows = run_screen(variants, args.variables, args.output_bits, args.seed)
    write_single_screen(
        args.out,
        "algebraic_degree_screen",
        rows,
        screen_metadata(variants=variants, variables=args.variables, output_bits=args.output_bits, seed=args.seed),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

