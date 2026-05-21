from __future__ import annotations

import argparse
import csv
import subprocess
import time
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark TriCube stream generation.")
    parser.add_argument("--bytes", type=int, default=1_048_576)
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--variants", default="baseline,fast8x", help="comma-separated C stream variants")
    parser.add_argument("--csv", type=Path, help="optional CSV output path")
    parser.add_argument("--skip-python", action="store_true", help="skip the slower pure-Python reference stream")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    cli = root / "c" / "build" / "tricube"
    rows: list[dict[str, str | int | float]] = []
    if cli.exists():
        for variant in [item.strip() for item in args.variants.split(",") if item.strip()]:
            start = time.perf_counter()
            subprocess.run(
                [
                    str(cli),
                    "stream",
                    "--seed",
                    str(args.seed),
                    "--bytes",
                    str(args.bytes),
                    "--out",
                    "-",
                    "--variant",
                    variant,
                ],
                stdout=subprocess.DEVNULL,
                check=True,
            )
            elapsed = time.perf_counter() - start
            mib = args.bytes / (1024 * 1024)
            rows.append(
                {
                    "implementation": f"tricube_c_stream_{variant}",
                    "bytes": args.bytes,
                    "elapsed_s": elapsed,
                    "mib_per_s": mib / elapsed,
                }
            )
            print(f"tricube_c_stream_{variant},{args.bytes},{elapsed:.6f},{mib / elapsed:.3f} MiB/s")
    if not args.skip_python:
        import tricube

        start = time.perf_counter()
        tricube.stream(args.seed, args.bytes)
        elapsed = time.perf_counter() - start
        mib = args.bytes / (1024 * 1024)
        rows.append(
            {
                "implementation": "tricube_python_stream",
                "bytes": args.bytes,
                "elapsed_s": elapsed,
                "mib_per_s": mib / elapsed,
            }
        )
        print(f"tricube_python_stream,{args.bytes},{elapsed:.6f},{mib / elapsed:.3f} MiB/s")
    if args.csv:
        args.csv.parent.mkdir(parents=True, exist_ok=True)
        with args.csv.open("w", newline="") as fp:
            writer = csv.DictWriter(fp, fieldnames=["implementation", "bytes", "elapsed_s", "mib_per_s"])
            writer.writeheader()
            writer.writerows(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
