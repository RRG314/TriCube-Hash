from __future__ import annotations

import argparse
import hashlib
import os
import time

import tricube


def _rate(label: str, func, data: bytes, repeat: int) -> tuple[str, int, float, float]:
    start = time.perf_counter()
    for _ in range(repeat):
        func(data)
    elapsed = time.perf_counter() - start
    mib = (len(data) * repeat) / (1024 * 1024)
    return label, len(data), elapsed, mib / elapsed if elapsed else 0.0


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark TriCube hash throughput by input size.")
    parser.add_argument("--quick", action="store_true", help="use a short benchmark")
    args = parser.parse_args()
    sizes = [0, 3, 64, 1024, 65536]
    repeat = 3 if args.quick else 20
    rng = os.urandom
    rows = []
    for size in sizes:
        data = rng(size)
        rows.append(_rate("tricube", tricube.hash, data, repeat))
        rows.append(_rate("sha256", lambda b: hashlib.sha256(b).digest(), data, repeat))
        rows.append(_rate("sha3_256", lambda b: hashlib.sha3_256(b).digest(), data, repeat))
    print("algorithm,size_bytes,elapsed_s,mib_per_s")
    for row in rows:
        print(f"{row[0]},{row[1]},{row[2]:.6f},{row[3]:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

