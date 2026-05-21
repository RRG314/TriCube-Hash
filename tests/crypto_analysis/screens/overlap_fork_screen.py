#!/usr/bin/env python3
"""Overlap/fork stream uniqueness screen for TriCube stream variants."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from _bootstrap import ensure_import_path

ensure_import_path()

from common import STATUS_FAIL, STATUS_PASS, count_repeated_blocks, hamming_bytes, parse_variants, stream_bytes  # noqa: E402
from _output import screen_metadata, write_single_screen  # noqa: E402


def run_screen(variants: list[str], stream_size: int, seed: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seed_set = [seed, seed + 1, seed ^ 1, seed ^ (1 << 63)]
    for variant in variants:
        streams = {s: stream_bytes(variant, s, stream_size) for s in seed_set}
        for block_size in (16, 32, 64):
            within = sum(count_repeated_blocks(data, block_size) for data in streams.values())
            cross = 0
            same_position = 0
            seen_by_seed: dict[bytes, int] = {}
            for s, data in streams.items():
                for pos in range(0, len(data) - block_size + 1, block_size):
                    block = data[pos : pos + block_size]
                    if block in seen_by_seed and seen_by_seed[block] != s:
                        cross += 1
                    else:
                        seen_by_seed[block] = s
            first = streams[seed]
            second = streams[seed + 1]
            for pos in range(0, min(len(first), len(second)) - block_size + 1, block_size):
                if first[pos : pos + block_size] == second[pos : pos + block_size]:
                    same_position += 1
            prefix_hamming = hamming_bytes(first[:1024], second[:1024])
            status = STATUS_FAIL if within or cross or same_position else STATUS_PASS
            rows.append(
                {
                    "screen": "overlap/fork stream uniqueness screen",
                    "variant": variant,
                    "stream_bytes_per_seed": stream_size,
                    "seeds": ",".join(str(s) for s in seed_set),
                    "block_size": block_size,
                    "within_stream_repeated_blocks": within,
                    "cross_stream_overlaps": cross,
                    "same_position_equal_blocks": same_position,
                    "adjacent_seed_prefix_hamming_1024B": prefix_hamming,
                    "status": status,
                }
            )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variants", default="baseline,fast8x")
    parser.add_argument("--bytes", type=int, default=1 << 20)
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    variants = parse_variants(args.variants)
    rows = run_screen(variants, args.bytes, args.seed)
    write_single_screen(args.out, "overlap_fork_screen", rows, screen_metadata(variants=variants, bytes=args.bytes, seed=args.seed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

