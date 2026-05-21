# Optional Analysis Tooling

This folder contains small checks for optional external cryptanalysis and
statistical-testing tools. It does not vendor those tools and it does not
implement formal cryptanalysis.

The scripts are deliberately small:

- `check_tools.py` reports which optional tools are installed.
- `z3_smoke.py` verifies that the Python Z3 binding can solve a tiny
  bit-vector equation.
- `sage_smoke.py` verifies that SageMath can construct a small Boolean
  polynomial ring. Run it with Sage's Python.
- `solver_model_plan.md` lists the TriCube-specific modeling work still needed
  before solver results would mean anything.

## Commands

Check tool availability:

```bash
python tests/crypto_analysis/tooling/check_tools.py
```

Run the Z3 smoke test if `z3-solver` is installed:

```bash
python tests/crypto_analysis/tooling/z3_smoke.py
```

Run the SageMath smoke test if `sage` is installed:

```bash
sage -python tests/crypto_analysis/tooling/sage_smoke.py
```

Missing tools are reported as `NOT_INSTALLED`, not as repository failures.

## Boundary

These scripts only check plumbing. A real reduced-round analysis still needs a
verified TriCube model for the 32-lane state, tetrahedral schedule, edge
coupling, shell coupling, lane permutation, constants, absorb/finalize rules,
and output extraction.

