#!/usr/bin/env python3
"""Black-box rotational relation probe for TriCube stream variants."""

from __future__ import annotations

import argparse
import math
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
    rotate_words64,
    rotl64,
    xor_bytes,
)
from config import ROTATIONS  # noqa: E402
from _output import screen_metadata, write_single_screen  # noqa: E402


def run_screen(variants: list[str], samples: int, seed: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    rng = rng_for(seed ^ 0xA55A)
    for variant in variants:
        for rotation in ROTATIONS:
            distances: list[int] = []
            exact = 0
            bit_flips = [0] * 256
            for _ in range(samples):
                base_seed = rng.getrandbits(64)
                a = digest32(variant, base_seed)
                b = digest32(variant, rotl64(base_seed, rotation))
                expected = rotate_words64(a, rotation)
                diff = xor_bytes(expected, b)
                if diff == b"\0" * len(diff):
                    exact += 1
                distances.append(hamming_bytes(expected, b))
                for bit_idx, bit in enumerate(bytes_to_bits(diff)):
                    bit_flips[bit_idx] += bit
            m = mean([float(x) for x in distances])
            max_bias = max(abs(count / samples - 0.5) for count in bit_flips)
            status = STATUS_FAIL if exact else (STATUS_WARN if m < 112 or m > 144 or max_bias > 0.25 else STATUS_PASS)
            rows.append(
                {
                    "screen": "black-box rotational relation probe",
                    "variant": variant,
                    "rotation": rotation,
                    "samples": samples,
                    "mean_rotational_distance": round(m, 4),
                    "min_distance": min(distances),
                    "max_distance": max(distances),
                    "max_bit_bias": round(max_bias, 6),
                    "exact_rotational_relations": exact,
                    "z_score_mean_distance": round((m - 128.0) / math.sqrt(256 * 0.25 / samples), 4),
                    "status": status,
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
    write_single_screen(args.out, "rotational_screen", rows, screen_metadata(variants=variants, samples=args.samples, seed=args.seed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

