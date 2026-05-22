#!/usr/bin/env python3
"""Collision, birthday, and near-collision screens for TriCube hash mode."""

from __future__ import annotations

import argparse
from collections import Counter
import math
from pathlib import Path
from typing import Any

from hash_common import (  # noqa: E402
    STATUS_FAIL,
    STATUS_PASS,
    STATUS_WARN,
    choose2,
    environment,
    hash_digest,
    hamming_bytes,
    mean,
    message_from_seed,
    parse_implementations,
    rng_for,
    write_hash_screen_outputs,
)


PREFIX_BITS = [16, 24, 32, 40, 48, 64]


def run_screen(
    implementations: list[str],
    samples: int,
    near_pairs: int,
    seed: int,
    message_len: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    rng = rng_for(seed ^ 0xC0111510)
    for implementation in implementations:
        outputs = [hash_digest(implementation, message_from_seed(rng.getrandbits(64), message_len)) for _ in range(samples)]
        full_counts = Counter(outputs)
        full_collisions = sum(choose2(c) for c in full_counts.values() if c > 1)
        rows.append(
            {
                "screen": "hash-mode collision/birthday sanity check",
                "implementation": implementation,
                "kind": "full_digest",
                "message_bytes": message_len,
                "samples": samples,
                "prefix_bits": 256,
                "observed_collision_pairs": full_collisions,
                "expected_collision_pairs": "near 0",
                "observed_expected_ratio": "",
                "status": STATUS_FAIL if full_collisions else STATUS_PASS,
            }
        )
        for bits in PREFIX_BITS:
            prefix_bytes = (bits + 7) // 8
            shift = prefix_bytes * 8 - bits
            prefixes = []
            for out in outputs:
                value = int.from_bytes(out[:prefix_bytes], "big")
                prefixes.append(value >> shift if shift else value)
            counts = Counter(prefixes)
            observed = sum(choose2(c) for c in counts.values() if c > 1)
            expected = samples * (samples - 1) / (2 * (2**bits))
            ratio = observed / expected if expected else 0.0
            if expected >= 10:
                sigma = math.sqrt(expected)
                status = STATUS_WARN if abs(observed - expected) > max(5.0 * sigma, 10.0) else STATUS_PASS
            else:
                status = STATUS_WARN if observed > max(10, expected * 10.0) else STATUS_PASS
            rows.append(
                {
                    "screen": "hash-mode collision/birthday sanity check",
                    "implementation": implementation,
                    "kind": "prefix",
                    "message_bytes": message_len,
                    "samples": samples,
                    "prefix_bits": bits,
                    "observed_collision_pairs": observed,
                    "expected_collision_pairs": round(expected, 4),
                    "observed_expected_ratio": round(ratio, 4) if expected else "",
                    "status": status,
                }
            )
        distances = []
        for _ in range(near_pairs):
            a, b = rng.sample(outputs, 2)
            distances.append(hamming_bytes(a, b))
        rows.append(
            {
                "screen": "hash-mode near-collision sanity check",
                "implementation": implementation,
                "kind": "sampled_pair_hamming",
                "message_bytes": message_len,
                "samples": near_pairs,
                "prefix_bits": "",
                "observed_collision_pairs": "",
                "expected_collision_pairs": "",
                "observed_expected_ratio": "",
                "min_hamming": min(distances),
                "mean_hamming": round(mean([float(x) for x in distances]), 4),
                "max_hamming": max(distances),
                "status": STATUS_WARN if min(distances) < 80 else STATUS_PASS,
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--implementations", default="baseline_hash")
    parser.add_argument("--samples", type=int, default=512)
    parser.add_argument("--near-pairs", type=int, default=256)
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--message-bytes", type=int, default=64)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    implementations = parse_implementations(args.implementations)
    rows = run_screen(implementations, args.samples, args.near_pairs, args.seed, args.message_bytes)
    metadata = environment()
    metadata.update(
        {
            "implementations": implementations,
            "samples": args.samples,
            "near_pairs": args.near_pairs,
            "seed": args.seed,
            "message_bytes": args.message_bytes,
        }
    )
    write_hash_screen_outputs(args.out, "collision_hash_screen", rows, metadata)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
