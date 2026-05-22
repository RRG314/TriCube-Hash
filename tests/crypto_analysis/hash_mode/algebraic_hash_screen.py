#!/usr/bin/env python3
"""Small black-box algebraic degree screen for TriCube hash mode."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from hash_common import (  # noqa: E402
    STATUS_PASS,
    STATUS_WARN,
    anf_degree,
    environment,
    flip_bit_in_message,
    hash_digest,
    mean,
    message_from_seed,
    parse_implementations,
    write_hash_screen_outputs,
)


def run_screen(
    implementations: list[str],
    variable_count: int,
    output_bits: int,
    seed: int,
    message_len: int,
) -> list[dict[str, Any]]:
    if variable_count > 12:
        raise ValueError("variable_count above 12 is intentionally blocked for this black-box screen")
    rows: list[dict[str, Any]] = []
    positions = [((i * 13) % (message_len * 8)) for i in range(variable_count)]
    assignments = 1 << variable_count
    base = message_from_seed(seed, message_len)
    for implementation in implementations:
        outputs = []
        for mask in range(assignments):
            message = base
            for i, pos in enumerate(positions):
                if (mask >> i) & 1:
                    message = flip_bit_in_message(message, pos)
            outputs.append(hash_digest(implementation, message))
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
                "screen": "hash-mode small black-box algebraic degree screen",
                "implementation": implementation,
                "message_bytes": message_len,
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
    parser.add_argument("--implementations", default="baseline_hash")
    parser.add_argument("--variables", type=int, default=8)
    parser.add_argument("--output-bits", type=int, default=32)
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--message-bytes", type=int, default=64)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    implementations = parse_implementations(args.implementations)
    rows = run_screen(implementations, args.variables, args.output_bits, args.seed, args.message_bytes)
    metadata = environment()
    metadata.update(
        {
            "implementations": implementations,
            "variables": args.variables,
            "output_bits": args.output_bits,
            "seed": args.seed,
            "message_bytes": args.message_bytes,
        }
    )
    write_hash_screen_outputs(args.out, "algebraic_hash_screen", rows, metadata)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
