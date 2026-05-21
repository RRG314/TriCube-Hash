#!/usr/bin/env python3
"""Low-bit diagnostic screen for TriCube stream variants."""

from __future__ import annotations

import argparse
from collections import Counter
import math
from pathlib import Path
from typing import Any

from _bootstrap import ensure_import_path

ensure_import_path()

from common import (  # noqa: E402
    STATUS_PASS,
    STATUS_WARN,
    bit_position_counts64,
    mean,
    parse_variants,
    stream_bytes,
    zscore_ones,
)
from _output import screen_metadata, write_single_screen  # noqa: E402


def lag_correlation(bits: list[int]) -> float:
    if len(bits) < 2:
        return 0.0
    xs = bits[:-1]
    ys = bits[1:]
    mx = mean([float(x) for x in xs])
    my = mean([float(y) for y in ys])
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    denx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    deny = math.sqrt(sum((y - my) ** 2 for y in ys))
    return num / (denx * deny) if denx and deny else 0.0


def run_screen(variants: list[str], stream_size: int, seed: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for variant in variants:
        data = stream_bytes(variant, seed, stream_size)
        n_bytes = len(data)
        byte_lsb = sum(byte & 1 for byte in data)
        word32_count = n_bytes // 4
        word64_count = n_bytes // 8
        word32_lsb = sum(int.from_bytes(data[i * 4 : i * 4 + 4], "little") & 1 for i in range(word32_count))
        word64_lsb = sum(int.from_bytes(data[i * 8 : i * 8 + 8], "little") & 1 for i in range(word64_count))
        low_nibbles = Counter(byte & 0x0F for byte in data)
        expected_nibble = n_bytes / 16
        nibble_chi2 = sum(((low_nibbles[i] - expected_nibble) ** 2) / expected_nibble for i in range(16))
        bit_counts = bit_position_counts64(data[: word64_count * 8])
        bit_z = [abs(zscore_ones(count, word64_count)) for count in bit_counts]
        low_bits = [(byte & 1) for byte in data]
        transitions = Counter((low_bits[i], low_bits[i + 1]) for i in range(len(low_bits) - 1))
        high_bits = [(byte >> 7) & 1 for byte in data]
        low_lag1 = lag_correlation(low_bits)
        high_lag1 = lag_correlation(high_bits)
        max_z = max(
            abs(zscore_ones(byte_lsb, n_bytes)),
            abs(zscore_ones(word32_lsb, word32_count)),
            abs(zscore_ones(word64_lsb, word64_count)),
            max(bit_z) if bit_z else 0.0,
        )
        status = STATUS_WARN if max_z > 6.0 or nibble_chi2 > 45.0 or abs(low_lag1) > 0.01 else STATUS_PASS
        rows.append(
            {
                "screen": "low-bit diagnostic screen",
                "variant": variant,
                "bytes": n_bytes,
                "byte_lsb_fraction": round(byte_lsb / n_bytes, 8),
                "byte_lsb_z": round(zscore_ones(byte_lsb, n_bytes), 4),
                "word32_lsb_fraction": round(word32_lsb / word32_count, 8),
                "word32_lsb_z": round(zscore_ones(word32_lsb, word32_count), 4),
                "word64_lsb_fraction": round(word64_lsb / word64_count, 8),
                "word64_lsb_z": round(zscore_ones(word64_lsb, word64_count), 4),
                "low_nibble_chi_square": round(nibble_chi2, 4),
                "max_bit_position_z64": round(max(bit_z), 4),
                "low_bit_transition_00": transitions[(0, 0)],
                "low_bit_transition_01": transitions[(0, 1)],
                "low_bit_transition_10": transitions[(1, 0)],
                "low_bit_transition_11": transitions[(1, 1)],
                "low_bit_lag1_corr": round(low_lag1, 8),
                "high_bit_lag1_corr": round(high_lag1, 8),
                "status": status,
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variants", default="baseline,fast8x")
    parser.add_argument("--bytes", type=int, default=16_777_216)
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    variants = parse_variants(args.variants)
    rows = run_screen(variants, args.bytes, args.seed)
    write_single_screen(args.out, "low_bit_diagnostics", rows, screen_metadata(variants=variants, seed=args.seed, bytes=args.bytes))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
