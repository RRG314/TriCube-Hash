from __future__ import annotations

import argparse
import os
import time

import tricube


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark TriCube Python reference throughput.")
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--bytes", type=int, default=1_048_576)
    args = parser.parse_args()
    data = os.urandom(65_536 if args.quick else args.bytes)
    repeat = 2 if args.quick else 5
    start = time.perf_counter()
    for _ in range(repeat):
        tricube.hash(data)
    elapsed = time.perf_counter() - start
    mib = len(data) * repeat / (1024 * 1024)
    print(f"tricube_python_reference,{len(data)},{repeat},{elapsed:.6f},{mib / elapsed:.3f} MiB/s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

