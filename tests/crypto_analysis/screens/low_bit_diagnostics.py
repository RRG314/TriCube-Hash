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
    parse_variants,
    stream_bytes,
    zscore_ones,
)
from _output import screen_metadata, write_single_screen  # noqa: E402


def lag_correlation_from_transitions(transitions: Counter[tuple[int, int]]) -> float:
    n_pairs = sum(transitions.values())
    if n_pairs <= 0:
        return 0.0
    sum_x = transitions[(1, 0)] + transitions[(1, 1)]
    sum_y = transitions[(0, 1)] + transitions[(1, 1)]
    sum_xy = transitions[(1, 1)]
    mx = sum_x / n_pairs
    my = sum_y / n_pairs
    cov = sum_xy - (sum_x * sum_y / n_pairs)
    var_x = sum_x - n_pairs * mx * mx
    var_y = sum_y - n_pairs * my * my
    den = math.sqrt(var_x * var_y)
    return cov / den if den else 0.0


def run_screen(variants: list[str], stream_size: int, seed: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for variant in variants:
        data = stream_bytes(variant, seed, stream_size)
        n_bytes = len(data)
        word32_count = n_bytes // 4
        word64_count = n_bytes // 8
        byte_lsb = 0
        word32_lsb = 0
        word64_lsb = 0
        low_nibbles: Counter[int] = Counter()
        byte_position_values = [[0] * 256 for _ in range(8)]
        low_transitions: Counter[tuple[int, int]] = Counter()
        high_transitions: Counter[tuple[int, int]] = Counter()
        prev_low: int | None = None
        prev_high: int | None = None
        counted_word_bytes = word64_count * 8
        for idx, byte in enumerate(data):
            low = byte & 1
            high = (byte >> 7) & 1
            byte_lsb += low
            low_nibbles[byte & 0x0F] += 1
            if idx % 4 == 0 and idx // 4 < word32_count:
                word32_lsb += low
            if idx % 8 == 0 and idx // 8 < word64_count:
                word64_lsb += low
            if idx < counted_word_bytes:
                byte_position_values[idx & 7][byte] += 1
            if prev_low is not None:
                low_transitions[(prev_low, low)] += 1
                high_transitions[(prev_high if prev_high is not None else 0, high)] += 1
            prev_low = low
            prev_high = high
        expected_nibble = n_bytes / 16
        nibble_chi2 = sum(((low_nibbles[i] - expected_nibble) ** 2) / expected_nibble for i in range(16))
        bit_counts = [0] * 64
        for byte_pos in range(8):
            counts = byte_position_values[byte_pos]
            for value, count in enumerate(counts):
                if count:
                    base = byte_pos * 8
                    for bit in range(8):
                        bit_counts[base + bit] += count * ((value >> bit) & 1)
        bit_z = [abs(zscore_ones(count, word64_count)) for count in bit_counts]
        low_lag1 = lag_correlation_from_transitions(low_transitions)
        high_lag1 = lag_correlation_from_transitions(high_transitions)
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
                "low_bit_transition_00": low_transitions[(0, 0)],
                "low_bit_transition_01": low_transitions[(0, 1)],
                "low_bit_transition_10": low_transitions[(1, 0)],
                "low_bit_transition_11": low_transitions[(1, 1)],
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
