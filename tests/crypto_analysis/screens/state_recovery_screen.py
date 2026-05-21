#!/usr/bin/env python3
"""Black-box state-recovery and predictability screen for TriCube streams."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from _bootstrap import ensure_import_path

ensure_import_path()

from common import (  # noqa: E402
    STATUS_PASS,
    STATUS_WARN,
    berlekamp_massey_binary,
    bytes_to_bits,
    mean,
    parse_variants,
    stream_bytes,
)
from _output import screen_metadata, write_single_screen  # noqa: E402


def run_screen(variants: list[str], stream_size: int, bm_bits: int, seed: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for variant in variants:
        data = stream_bytes(variant, seed, stream_size)
        half = len(data) // 2
        train = data[:half]
        test = data[half:]
        most_common_byte = Counter(train).most_common(1)[0][0]
        next_byte_acc = sum(1 for b in test if b == most_common_byte) / len(test)
        transitions: dict[int, Counter[int]] = defaultdict(Counter)
        for a, b in zip(train, train[1:]):
            transitions[a][b] += 1
        hits = 0
        total = 0
        for a, b in zip(test, test[1:]):
            pred = transitions.get(a)
            if pred:
                hits += pred.most_common(1)[0][0] == b
            total += 1
        ngram_acc = hits / total if total else 0.0
        train_bits = bytes_to_bits(train)
        test_bits = bytes_to_bits(test)
        majority = 1 if sum(train_bits) >= len(train_bits) / 2 else 0
        bit_acc = sum(bit == majority for bit in test_bits) / len(test_bits) if test_bits else 0.0
        lc_ratios = []
        for bit_pos in (0, 1, 7):
            seq = [((byte >> bit_pos) & 1) for byte in data[:bm_bits]]
            lc_ratios.append(berlekamp_massey_binary(seq) / len(seq))
        status = STATUS_WARN if next_byte_acc > 0.02 or ngram_acc > 0.02 or abs(bit_acc - 0.5) > 0.02 else STATUS_PASS
        rows.append(
            {
                "screen": "black-box state-recovery/predictability screen",
                "variant": variant,
                "train_bytes": len(train),
                "test_bytes": len(test),
                "next_byte_accuracy": round(next_byte_acc, 6),
                "ngram1_accuracy": round(ngram_acc, 6),
                "random_next_byte_baseline": round(1 / 256, 6),
                "bit_accuracy": round(bit_acc, 6),
                "berlekamp_massey_lc_ratio_min": round(min(lc_ratios), 6),
                "berlekamp_massey_lc_ratio_mean": round(mean(lc_ratios), 6),
                "berlekamp_massey_lc_ratio_max": round(max(lc_ratios), 6),
                "status": status,
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variants", default="baseline,fast8x")
    parser.add_argument("--bytes", type=int, default=1 << 20)
    parser.add_argument("--bm-bits", type=int, default=4096)
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    variants = parse_variants(args.variants)
    rows = run_screen(variants, args.bytes, args.bm_bits, args.seed)
    write_single_screen(
        args.out,
        "state_recovery_screen",
        rows,
        screen_metadata(variants=variants, bytes=args.bytes, bm_bits=args.bm_bits, seed=args.seed),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

