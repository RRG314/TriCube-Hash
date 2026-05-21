#!/usr/bin/env python3
"""Black-box differential diffusion probe for TriCube stream variants."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any

from _bootstrap import ensure_import_path

ensure_import_path()

from common import (  # noqa: E402
    STATUS_FAIL,
    STATUS_PASS,
    STATUS_WARN,
    bytes_to_bits,
    digest32,
    hamming_bytes,
    mean,
    parse_variants,
    rng_for,
    xor_bytes,
)
from config import DELTA_CLASSES  # noqa: E402
from _output import screen_metadata, write_single_screen  # noqa: E402


def status_for_diff(mean_bits: float, max_bias: float, repeated_top: int) -> str:
    if mean_bits < 96 or mean_bits > 160 or repeated_top > 4:
        return STATUS_FAIL
    if mean_bits < 112 or mean_bits > 144 or max_bias > 0.25 or repeated_top > 1:
        return STATUS_WARN
    return STATUS_PASS


def run_screen(variants: list[str], samples: int, seed: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    rng = rng_for(seed)
    random_deltas = {
        "random_low_weight": [sum(1 << rng.randrange(64) for _ in range(3)) for _ in range(4)],
        "random_medium_weight": [rng.getrandbits(64) & rng.getrandbits(64) for _ in range(4)],
        "random_full_weight": [rng.getrandbits(64) or 1 for _ in range(4)],
    }
    all_classes = {**DELTA_CLASSES, **random_deltas}
    for variant in variants:
        for name, deltas in all_classes.items():
            distances: list[int] = []
            repeated = Counter()
            bit_flips = [0] * 256
            for idx in range(samples):
                base_seed = rng.getrandbits(64)
                delta = deltas[idx % len(deltas)] & 0xFFFFFFFFFFFFFFFF
                a = digest32(variant, base_seed)
                b = digest32(variant, base_seed ^ delta)
                diff = xor_bytes(a, b)
                distances.append(hamming_bytes(a, b))
                repeated[diff] += 1
                for bit_idx, bit in enumerate(bytes_to_bits(diff)):
                    bit_flips[bit_idx] += bit
            max_bias = max(abs(count / samples - 0.5) for count in bit_flips)
            chi2 = sum(((count - samples / 2) ** 2) / (samples / 2) for count in bit_flips)
            top = repeated.most_common(1)[0][1] if repeated else 0
            m = mean([float(x) for x in distances])
            rows.append(
                {
                    "screen": "black-box differential diffusion probe",
                    "variant": variant,
                    "delta_class": name,
                    "samples": samples,
                    "mean_hamming": round(m, 4),
                    "min_hamming": min(distances),
                    "max_hamming": max(distances),
                    "max_bit_bias": round(max_bias, 6),
                    "chi_square_bit_flips": round(chi2, 3),
                    "repeated_output_differences": sum(v - 1 for v in repeated.values() if v > 1),
                    "top_repeated_difference_count": top,
                    "status": status_for_diff(m, max_bias, top),
                }
            )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variants", default="baseline,fast8x")
    parser.add_argument("--samples", type=int, default=64)
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    variants = parse_variants(args.variants)
    rows = run_screen(variants, args.samples, args.seed)
    write_single_screen(args.out, "differential_screen", rows, screen_metadata(variants=variants, samples=args.samples, seed=args.seed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

