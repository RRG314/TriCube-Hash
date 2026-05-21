# TriCube Crypto-Analysis Screens

This folder contains the reproducible black-box development screens used to
triage TriCube stream variants. The screens are intentionally named probes and
screens because they are not formal cryptanalysis.

These tests are development gates. They can find obvious failures or warning
patterns, but they do not replace white-box cryptanalysis.

## What Runs Here

`run_all_screens.py` runs the compact internal suite:

- black-box differential diffusion probe;
- black-box rotational relation probe;
- small black-box algebraic degree screen;
- collision/birthday sanity check;
- near-collision sanity check;
- overlap/fork stream uniqueness screen;
- black-box state-recovery/predictability screen;
- low-bit diagnostic screen;
- white-box round-model schedule analysis;
- external-tool availability checks.

The suite compares the released baseline stream path and the experimental
`fast8x` stream variant through the same black-box interface: a seed maps to the
first 32 bytes of deterministic stream output. That is useful for comparing
stream variants, but it is not a substitute for hash-mode cryptanalysis.

## Commands

Quick profile:

```bash
python tests/crypto_analysis/run_all_screens.py \
  --profile quick \
  --variants baseline,fast8x \
  --out tests/crypto_analysis/results/quick-latest
```

## Individual Screens

The all-in-one runner calls the same screen modules listed below. Reviewers can
run any screen by itself when they want to inspect one method, one output table,
or one threshold policy.

| Screen | Command |
|---|---|
| Differential diffusion | `python tests/crypto_analysis/screens/differential_screen.py --variants baseline,fast8x --samples 64 --out tests/crypto_analysis/results/differential-latest` |
| Rotational relation | `python tests/crypto_analysis/screens/rotational_screen.py --variants baseline,fast8x --samples 64 --out tests/crypto_analysis/results/rotational-latest` |
| Algebraic degree | `python tests/crypto_analysis/screens/algebraic_degree_screen.py --variants baseline,fast8x --variables 8 --output-bits 32 --out tests/crypto_analysis/results/algebraic-latest` |
| Collision and birthday | `python tests/crypto_analysis/screens/collision_screen.py --variants baseline,fast8x --samples 512 --near-pairs 256 --out tests/crypto_analysis/results/collision-latest` |
| Overlap/fork uniqueness | `python tests/crypto_analysis/screens/overlap_fork_screen.py --variants baseline,fast8x --bytes 1048576 --out tests/crypto_analysis/results/overlap-latest` |
| State-recovery/predictability | `python tests/crypto_analysis/screens/state_recovery_screen.py --variants baseline,fast8x --bytes 1048576 --bm-bits 4096 --out tests/crypto_analysis/results/state-recovery-latest` |
| Low-bit diagnostics | `python tests/crypto_analysis/screens/low_bit_diagnostics.py --variants baseline,fast8x --bytes 16777216 --out tests/crypto_analysis/results/low-bit-latest` |
| White-box word-dependency model | `python tests/crypto_analysis/screens/whitebox_round_model.py --rounds 24 --out tests/crypto_analysis/results/whitebox-latest` |
| External battery availability | `python tests/crypto_analysis/screens/external_batteries.py --variants baseline,fast8x --out tests/crypto_analysis/results/external-latest` |

Low-bit diagnostics at 16 MiB per variant:

```bash
python tests/crypto_analysis/screens/low_bit_diagnostics.py \
  --variants baseline,fast8x \
  --bytes 16777216 \
  --out tests/crypto_analysis/results/low-bit-latest
```

White-box word-dependency model:

```bash
python tests/crypto_analysis/screens/whitebox_round_model.py \
  --rounds 24 \
  --out tests/crypto_analysis/results/whitebox-latest
```

Optional tool availability:

```bash
python tests/crypto_analysis/tooling/check_tools.py
```

Standard profile:

```bash
python tests/crypto_analysis/run_all_screens.py \
  --profile standard \
  --variants baseline,fast8x \
  --out tests/crypto_analysis/results/standard-latest
```

## Output Format

Each run writes:

- `summary.json` with metadata, exact command, branch, commit, machine, Python
  version, profile, seed, variants, and status counts;
- `summary.md` with compact interpreted tables;
- one CSV and one Markdown summary for each screen;
- `all_screens.csv` with every row in one compact table.

Large raw streams and external battery logs are not stored here. External tools
should write their own summaries under `results/` or a release artifact area.

## Status Labels

- `PASS`: no issue detected under this test budget.
- `WARN`: suspicious pattern or threshold breach that is not conclusive.
- `FAIL`: clear failure under the screen criteria.
- `BLOCKED`: missing tool, missing binary, or harness/runtime blocker.
- `NOT_RUN`: available test was not attempted in this run.

Do not treat `PASS` as a security claim. Do not treat EOF, SIGPIPE, timeout, or
input exhaustion as a statistical pass.

## Limits

The current screens are black-box tests over output bytes. They do not model
TriCube's tetrahedral ARX layer, modular-addition difference propagation, lane
schedules, constants, or output extraction symbolically. Formal work still
requires differential trail search, rotational propagation analysis,
SAT/SMT/MILP or Gröbner-style algebraic modeling, reduced-round attack
experiments, and independent review.

The white-box round model is a narrow exception: it does inspect the specified
lane schedule, but only at word-dependency granularity. It is useful for
checking coverage and schedule reachability. It is still not differential,
rotational, algebraic, or state-recovery cryptanalysis.

## Tooling and Models

The reusable TriCube schedule model is in `models/tricube_schedule.py`. It
generates the lane mapping, tetrahedra, edges, shell schedule, and lane
permutation used by the current specification. Solver-specific work should
build on that model rather than duplicating schedule rules in separate
scripts.

The `tooling/` folder contains optional setup checks for Z3, SageMath,
CryptoMiniSat, PractRand, Dieharder, TestU01 adapters, SmokeRand, and NIST STS.
Those checks do not vendor or run full external tools; they only report whether
the local machine is ready for deeper analysis.
