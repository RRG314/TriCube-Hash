from __future__ import annotations

import tricube


def main() -> int:
    print("xof:", tricube.xof(b"TriCube example", 64).hex())
    print("stream:", tricube.stream(seed=123, n=64).hex())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

