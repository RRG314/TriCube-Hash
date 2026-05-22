#!/usr/bin/env python3
"""Black-box rotational relation screen for TriCube hash mode."""

from __future__ import annotations

import argparse
import math
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
    rotate_words64,
    write_hash_screen_outputs,
    xor_bytes,
)


ROTATIONS = [1, 2, 3, 4, 5, 7, 8, 13, 16, 17, 31, 32, 33, 47, 63]


def run_screen(implementations: list[str], samples: int, seed: int, message_len: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    rng = rng_for(seed ^ 0xA55A)
    for implementation in implementations:
        for rotation in ROTATIONS:
            distances: list[int] = []
            exact = 0
            bit_flips = [0] * 256
            for _ in range(samples):
                base = message_from_seed(rng.getrandbits(64), message_len)
                rotated_message = rotate_words64(base, rotation)
                a = hash_digest(implementation, base)
                b = hash_digest(implementation, rotated_message)
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
                    "screen": "hash-mode black-box rotational relation screen",
                    "implementation": implementation,
                    "rotation": rotation,
                    "message_bytes": message_len,
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
    write_hash_screen_outputs(args.out, "rotational_hash_screen", rows, metadata)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
