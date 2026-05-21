# Analysis Tooling

TriCube should not grow a private cryptanalysis ecosystem when good public
tools already exist. The custom part is the TriCube model: the 32-lane state,
the 3 x 3 x 3 vertex mapping, tetrahedral schedule, edge coupling, shell
coupling, lane permutation, constants, modes, padding, and output extraction.
Once that model is correct, established solvers and statistical batteries can
be used for reduced-round searches and external screening.

This repository does not vendor solver frameworks or statistical batteries.
They must be installed separately and used under their own licenses. The local
scripts only check availability, run tiny smoke tests, or provide wrappers
around TriCube's stream output.

## Tool Status

| Area | Tool | Role | Current status | Needed TriCube-specific work |
|---|---|---|---|---|
| Statistical batteries | PractRand | Progressive random-stream testing through `RNG_test`. | Already used; optional external tool. | Keep stream wrapper commands, preserve warnings, and run multi-seed long profiles before promotion. |
| Statistical batteries | TestU01 | SmallCrush, Crush, and BigCrush empirical RNG batteries. | Already used through a local stdin adapter. | Keep adapter reproducible, separate EOF/harness failures from statistical failures, and record tool version. |
| Statistical batteries | Dieharder | Broad empirical RNG battery. | Already used; optional external tool. | Ensure enough stream input for full runs; report weak rows separately from failures. |
| Statistical batteries | SmokeRand | Independent stream battery with express/full modes. | Already used; optional external tool. | Document express/full commands and keep timeout separate from statistical failure. |
| Statistical batteries | NIST STS | SP 800-22 statistical test suite. | Already used as an optional external check. | Document sequence count, bit length, parse rules, and failed-proportion handling. |
| SMT | Z3 | Bit-vector model checking, reduced-round satisfiability, and bounded search. | Recommended next tooling; smoke check provided. | Build and validate a bit-exact reduced-round TriCube model before searching trails or collisions. |
| SAT | CryptoMiniSat | CNF/SAT experiments for reduced-round Boolean models. | Optional future tool. | Export a verified CNF model for reduced-round components and compare results against known vectors. |
| Algebraic | SageMath | Boolean polynomial rings, ANF experiments, and algebraic prototyping. | Recommended for small reduced-round algebraic experiments; smoke check provided. | Export reduced-round components small enough for exact ANF or polynomial experiments. |
| ARX analysis framework | CLAASP | Automated analysis of symmetric primitives, including MILP, SMT, algebraic, avalanche, and statistical modules. | Future investigation. | Determine whether TriCube's tetrahedral in-place schedule can be represented cleanly in CLAASP. |
| ARX analysis framework | CryptoSMT | SMT/SAT-based cryptanalysis framework for symmetric primitives. | Future investigation; likely useful only after model adaptation. | Adapt TriCube as a custom ARX/hash primitive and verify reduced-round outputs. |
| ARX analysis framework | ArxPy | SMT-based XOR differential, rotational-XOR, and impossible-differential work on ARX primitives. | Future investigation. | Determine whether TriCube's nonstandard state topology and shell lanes fit its primitive interface. |
| MILP / CP-SAT | OR-Tools | Constraint programming and integer optimization experiments. | Optional; not cryptanalysis-specific. | Use only if a clear MILP/CP-SAT formulation is defined and validated. |
| MILP / LP | PuLP / SciPy | Lightweight LP/MILP prototyping when a full cryptanalysis framework is not needed. | Optional; not a default dependency. | Use for small modeling experiments only; avoid presenting generic optimization as cryptanalysis. |

## What Must Be Custom

The open-source tools do not know TriCube. They cannot search meaningful
trails or equations until a TriCube-specific model exists. The required model
must encode:

- the 32-lane, 2048-bit state;
- the 27 vertex lanes and 5 shell/global lanes;
- the `3 x 3 x 3` vertex mapping and `2 x 2 x 2` cube cells;
- the 48 tetrahedral neighborhoods and their orientation schedule;
- the 54 grid-edge couplings;
- the shell/global lane coupling schedule;
- the global lane permutation;
- the round constants and rotation schedules;
- absorb, finalize, squeeze, stream seeding, length encoding, and domain tags;
- reduced-round hooks that can be checked against known vectors.

After that model is validated, external tools can be used to search for
reduced-round differential trails, rotational distinguishers, algebraic
low-degree relations, state-recovery equations, and reduced-round
collision/preimage examples. Until then, black-box probes and word-dependency
models are development gates, not cryptanalysis.

The reusable lane-schedule model is
[`tests/crypto_analysis/models/tricube_schedule.py`](../tests/crypto_analysis/models/tricube_schedule.py).
It verifies the current schedule counts: 27 vertex lanes, 5 shell lanes, 8 cube
cells, 48 tetrahedra, 54 edges, and a 32-lane permutation. It is useful
foundation code, but it is still a word-level schedule model rather than a
solver-ready attack model.

## Local Tool Checks

Optional tool availability can be checked without making those tools package
dependencies:

```bash
python tests/crypto_analysis/tooling/check_tools.py
```

Small solver smoke tests are available:

```bash
python tests/crypto_analysis/tooling/z3_smoke.py
sage -python tests/crypto_analysis/tooling/sage_smoke.py
```

These smoke tests only verify local setup. They do not analyze TriCube.

## References and License Notes

- Z3 is a Microsoft Research SMT solver distributed under the MIT License:
  <https://github.com/Z3Prover/z3>.
- SageMath is a GPL-licensed open-source mathematical software system:
  <https://www.sagemath.org/>.
- CryptoMiniSat is an open-source SAT solver; the upstream repository reports
  default MIT-licensed build material, with license caveats for optional
  integrations:
  <https://github.com/msoos/cryptominisat>.
- CLAASP is the Cryptographic Library for Automated Analysis of Symmetric
  Primitives; its PyPI metadata lists GPLv3:
  <https://pypi.org/project/claasp/> and <https://claasp.readthedocs.io/>.
- CryptoSMT is an SMT/SAT-based tool for cryptanalysis of symmetric primitives:
  <https://github.com/kste/cryptosmt>.
- ArxPy documents SMT-based XOR differential, rotational-XOR, and impossible
  differential work for ARX primitives: <https://ranea.github.io/ArxPy/>.
- TestU01 is described by L'Ecuyer and Simard, ACM TOMS 2007:
  <https://doi.org/10.1145/1268776.1268777>.
- PractRand documentation is at <https://pracrand.sourceforge.net/>.
- Dieharder documentation is at
  <https://rurban.github.io/dieharder/manual/dieharder.html>.
- NIST STS is documented in NIST SP 800-22 and on the NIST random-bit
  generation software page:
  <https://csrc.nist.gov/projects/random-bit-generation/documentation-and-software>.
- SmokeRand is referenced from its upstream repository:
  <https://github.com/alvoskov/SmokeRand>.
