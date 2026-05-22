#!/usr/bin/env python3
"""Write concatenated TriCube hash digests for external battery input."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from hash_common import hash_digest, message_from_seed, parse_implementations


def output_handle(path: str):
    if path == "-":
        return sys.stdout.buffer, False
    file = open(path, "wb")
    return file, True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--implementation", default="baseline_hash")
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--messages", type=int, required=True)
    parser.add_argument("--message-bytes", type=int, default=64)
    parser.add_argument("--out", default="-")
    args = parser.parse_args()

    implementation = parse_implementations(args.implementation)[0]
    if args.messages < 0:
        raise ValueError("--messages must be non-negative")
    if args.message_bytes <= 0:
        raise ValueError("--message-bytes must be positive")

    handle, should_close = output_handle(args.out)
    try:
        for idx in range(args.messages):
            message = message_from_seed(args.seed + idx, args.message_bytes)
            handle.write(hash_digest(implementation, message))
    finally:
        if should_close:
            handle.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
