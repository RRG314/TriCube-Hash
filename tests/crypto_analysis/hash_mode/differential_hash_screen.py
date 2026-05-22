#!/usr/bin/env python3
"""Black-box differential diffusion screen for TriCube hash mode."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any

from hash_common import (  # noqa: E402
    STATUS_FAIL,
    STATUS_PASS,
    STATUS_WARN,
    bytes_to_bits,
    environment,
    hash_digest,
    hamming_bytes,
    mean,
    message_from_seed,
    parse_implementations,
    rng_for,
    write_hash_screen_outputs,
    xor_bytes,
    xor_mask_into_message,
)


DELTA_CLASSES = {
    "single_bit": [1 << b for b in (0, 1, 7, 8, 31, 32, 63)],
    "single_byte": [0xFF << (8 * b) for b in (0, 1, 3, 7)],
    "single_64_word": [0xFFFFFFFFFFFFFFFF],
    "all_low_bit_mask": [0x0101010101010101],
    "checkerboard_mask": [0xAA55AA55AA55AA55, 0x55AA55AA55AA55AA],
    "high_bit_mask": [0x8080808080808080],
    "adjacent_bit_mask": [(1 << b) | (1 << (b + 1)) for b in (0, 1, 7, 15, 31, 47, 62)],
}


def status_for_diff(mean_bits: float, max_bias: float, repeated_top: int) -> str:
    if mean_bits < 96 or mean_bits > 160 or repeated_top > 4:
        return STATUS_FAIL
    if mean_bits < 112 or mean_bits > 144 or max_bias > 0.25 or repeated_top > 1:
        return STATUS_WARN
    return STATUS_PASS


def run_screen(implementations: list[str], samples: int, seed: int, message_len: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    rng = rng_for(seed ^ 0xD1FF)
    random_deltas = {
        "random_low_weight": [sum(1 << rng.randrange(64) for _ in range(3)) for _ in range(4)],
        "random_medium_weight": [rng.getrandbits(64) & rng.getrandbits(64) for _ in range(4)],
        "random_full_weight": [rng.getrandbits(64) or 1 for _ in range(4)],
    }
    all_classes = {**DELTA_CLASSES, **random_deltas}
    for implementation in implementations:
        for name, deltas in all_classes.items():
            distances: list[int] = []
            repeated = Counter()
            bit_flips = [0] * 256
            for idx in range(samples):
                base_seed = rng.getrandbits(64)
                base = message_from_seed(base_seed, message_len)
                offset = (idx * 17 + base_seed) % message_len
                delta = deltas[idx % len(deltas)] & 0xFFFFFFFFFFFFFFFF
                changed = xor_mask_into_message(base, delta, offset)
                a = hash_digest(implementation, base)
                b = hash_digest(implementation, changed)
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
                    "screen": "hash-mode black-box differential diffusion screen",
                    "implementation": implementation,
                    "delta_class": name,
                    "message_bytes": message_len,
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
    parser.add_argument("--implementations", default="baseline_hash")
    parser.add_argument("--samples", type=int, default=64)
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--message-bytes", type=int, default=64)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    implementations = parse_implementations(args.implementations)
    rows = run_screen(implementations, args.samples, args.seed, args.message_bytes)
    metadata = environment()
    metadata.update(
        {
            "implementations": implementations,
            "samples": args.samples,
            "seed": args.seed,
            "message_bytes": args.message_bytes,
        }
    )
    write_hash_screen_outputs(args.out, "differential_hash_screen", rows, metadata)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
