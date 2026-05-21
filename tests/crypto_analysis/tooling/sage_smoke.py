#!/usr/bin/env python3
"""Tiny SageMath smoke test for optional algebraic tooling.

Run with ``sage -python tests/crypto_analysis/tooling/sage_smoke.py``.
This does not analyze TriCube. It only verifies that Sage can construct a small
Boolean polynomial ring and compute a normal form.
"""

from __future__ import annotations

import json


def main() -> int:
    try:
        from sage.all import BooleanPolynomialRing  # type: ignore[import-not-found]
    except Exception as exc:
        print(json.dumps({"tool": "sage", "status": "NOT_INSTALLED", "detail": str(exc)}, indent=2))
        return 0

    ring = BooleanPolynomialRing(3, "x")
    x0, x1, x2 = ring.gens()
    poly = (x0 + x1) * (x1 + x2) + x0 * x2
    print(
        json.dumps(
            {
                "tool": "sage",
                "status": "PASS",
                "polynomial": str(poly),
                "degree": int(poly.degree()),
                "note": "Sage smoke test only; not TriCube cryptanalysis",
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

