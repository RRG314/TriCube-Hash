from __future__ import annotations

import argparse
from pathlib import Path

import tricube


def main() -> int:
    parser = argparse.ArgumentParser(description="Hash a file with TriCube.")
    parser.add_argument("path", help="file to hash")
    args = parser.parse_args()
    data = Path(args.path).read_bytes()
    print(tricube.hexdigest(data))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

