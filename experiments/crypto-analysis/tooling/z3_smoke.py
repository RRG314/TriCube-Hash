#!/usr/bin/env python3
"""Tiny Z3 smoke test for optional solver setup.

This is not TriCube cryptanalysis. It only verifies that the Python Z3 binding
can solve a fixed-width bit-vector equation on the local machine.
"""

from __future__ import annotations

import json


def main() -> int:
    try:
        import z3  # type: ignore[import-not-found]
    except Exception as exc:
        print(json.dumps({"tool": "z3", "status": "NOT_INSTALLED", "detail": str(exc)}, indent=2))
        return 0

    x = z3.BitVec("x", 64)
    solver = z3.Solver()
    solver.add(((x + z3.BitVecVal(0x9E3779B97F4A7C15, 64)) ^ z3.RotateLeft(x, 17)) == 0x123456789ABCDEF0)
    status = solver.check()
    model_value = None
    if status == z3.sat:
        model_value = hex(solver.model()[x].as_long())
    print(
        json.dumps(
            {
                "tool": "z3",
                "status": "PASS" if status == z3.sat else "WARN",
                "solver_status": str(status),
                "model_x": model_value,
                "note": "solver smoke test only; not TriCube cryptanalysis",
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

