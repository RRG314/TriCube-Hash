from __future__ import annotations

import argparse
import subprocess
import time
from pathlib import Path

import tricube


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark TriCube stream generation.")
    parser.add_argument("--bytes", type=int, default=1_048_576)
    parser.add_argument("--seed", type=int, default=123)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    cli = root / "c" / "build" / "tricube"
    if cli.exists():
        start = time.perf_counter()
        subprocess.run(
            [str(cli), "stream", "--seed", str(args.seed), "--bytes", str(args.bytes), "--out", "-"],
            stdout=subprocess.DEVNULL,
            check=True,
        )
        elapsed = time.perf_counter() - start
        mib = args.bytes / (1024 * 1024)
        print(f"tricube_c_stream,{args.bytes},{elapsed:.6f},{mib / elapsed:.3f} MiB/s")
    start = time.perf_counter()
    tricube.stream(args.seed, args.bytes)
    elapsed = time.perf_counter() - start
    mib = args.bytes / (1024 * 1024)
    print(f"tricube_python_stream,{args.bytes},{elapsed:.6f},{mib / elapsed:.3f} MiB/s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

