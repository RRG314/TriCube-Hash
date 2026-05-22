# TriCube Crypto-Analysis Screens

This folder contains reproducible development screens for TriCube stream
variants. They are named probes and screens because they are engineering gates
for obvious failures and warning patterns, not formal cryptanalysis.

## Shared Test Model

The stream screens use the C CLI as the system under test. If `c/build/tricube`
is not present, the helper layer builds it with `make -C c all`. Each black-box
stream screen then asks the CLI for deterministic stream bytes:

```text
c/build/tricube stream --seed SEED --bytes N --out - [--variant fast8x1024mix]
```

For short-output screens, the tested function is:

```text
F_variant(seed) = first 32 bytes of TriCube stream output for that 64-bit seed
```

The suite compares the released baseline stream path and any named experimental
stream variants through that same interface. This gives a clean side-by-side
test of stream initialization, stream stepping, output extraction, and variant
domain separation. It does not test the hash API directly, and it does not
inspect bit-level internal ARX propagation except in the separate white-box
schedule model.

Hash-mode screens live in `hash_mode/`. They use the same C CLI but exercise
the public digest path instead:

```text
c/build/tricube hash --hex MESSAGE_HEX
```

Those screens are intentionally separate so stream results are not used as
evidence for hash-mode behavior. The current public hash implementation is
listed as `baseline_hash`; faster hash prototypes should only be added after
they have fixed vectors, specification text, and external battery results.

The quick and standard profiles use the following budgets.

| Parameter | Quick | Standard |
|---|---:|---:|
| Differential/rotational samples per case | 64 | 256 |
| Algebraic variables | 8 | 10 |
| Algebraic output bits | 32 | 64 |
| Collision samples | 512 | 4096 |
| Near-collision sampled pairs | 256 | 2048 |
| Stream bytes per variant for stream screens | 1 MiB | 16 MiB |
| Berlekamp-Massey bytes sampled per selected bit stream | 4096 | 16384 |

The scripts use deterministic pseudorandom sampling from the command seed
(`--seed`, default `123`) so reviewers can rerun the same cases.

## What Runs Here

`run_all_screens.py` runs the compact suite and writes one combined
summary. Each screen is also a separate script so reviewers can inspect and run
one method at a time.

## Commands

Quick profile:

```bash
python tests/crypto_analysis/run_all_screens.py \
  --profile quick \
  --variants baseline,fast8x,fast8x1024mix \
  --out tests/crypto_analysis/results/quick-latest
```

Standard profile:

```bash
python tests/crypto_analysis/run_all_screens.py \
  --profile standard \
  --variants baseline,fast8x,fast8x1024mix \
  --out tests/crypto_analysis/results/standard-latest
```

Hash-mode quick profile:

```bash
python tests/crypto_analysis/hash_mode/run_hash_screens.py \
  --profile quick \
  --implementations baseline_hash \
  --out tests/crypto_analysis/results/hash-quick-latest
```

## Screen Methods

### Black-Box Differential Diffusion Probe

File: `screens/differential_screen.py`

This probe asks whether selected seed differences produce output differences
that look broadly diffused in the first 256 output bits. For each variant,
delta class, and sample, the script chooses a base seed, generates
`F(seed)`, generates `F(seed xor delta)`, and analyzes the xor difference of
the two 32-byte outputs.

The fixed delta classes are:

- single-bit masks at positions `0, 1, 7, 8, 31, 32, 63`;
- single-byte masks in byte positions `0, 1, 3, 7`;
- all-ones 64-bit word mask;
- low-bit-per-byte mask `0x0101010101010101`;
- checkerboard masks `0xAA55...` and `0x55AA...`;
- high-bit-per-byte mask `0x8080808080808080`;
- adjacent-bit masks near byte, word, and high-bit boundaries.

The script also adds deterministic random low-weight, medium-weight, and
full-weight deltas. It records mean/min/max output Hamming distance, per-output
bit flip counts, maximum output-bit bias away from 0.5, a chi-square score for
bit flips, repeated output differences, and the top repeated-difference count.

This stresses seed injection, stream initialization, per-block stream update,
and output extraction. The pass threshold expects the mean 256-bit output
difference to stay in `[112, 144]`, maximum bit bias to stay at or below
`0.25`, and no repeated difference pattern beyond the tested budget. A hard
failure is recorded for very low or high diffusion (`<96` or `>160` changed
bits on average) or repeated difference concentration.

This is not trail-based differential cryptanalysis. It does not model how
differences propagate through modular addition, tetrahedral mixing, edge
coupling, shell lanes, or lane permutation.

### Black-Box Rotational Relation Probe

File: `screens/rotational_screen.py`

This probe checks for obvious rotational symmetry between related seeds and
outputs. For each rotation in:

```text
1, 2, 3, 4, 5, 7, 8, 13, 16, 17, 31, 32, 33, 47, 63
```

the script generates `F(seed)`, rotates the 64-bit seed left by that amount,
generates `F(rotl64(seed, r))`, rotates each 64-bit output word of `F(seed)` by
the same amount, and compares that rotated output to the related-seed output.

The metrics are exact rotational relation count, mean/min/max rotational
distance, maximum output-bit bias in the relation difference, and a z-score for
the mean distance around the 128-bit expectation. The screen fails if any exact
rotational relation appears. It warns when mean distance leaves `[112, 144]` or
maximum bit bias exceeds `0.25`.

This stresses whether the seed-to-stream map preserves simple word rotations
through the output path. It does not prove resistance to rotational
distinguishers, and it does not model rotational trails inside the ARX round
function.

### Small Black-Box Algebraic Degree Screen

File: `screens/algebraic_degree_screen.py`

This screen estimates whether small slices of the seed-to-output map have
obviously low Boolean degree. It selects seed bit positions:

```text
position_i = (13 * i) mod 64
```

for `i = 0 .. variables-1`. It enumerates all `2^variables` assignments,
xors the selected seed bits into the base seed, evaluates `F(seed)`, and builds
truth tables for the requested output bits. It then applies a Möbius transform
to each truth table and reports the algebraic normal form (ANF) degree.

The quick profile uses 8 variables and 32 output bits. The standard profile
uses 10 variables and 64 output bits. The script refuses more than 12 variables
because this black-box method is exponential. It reports min/mean/max degree
and counts output bits whose degree is at least two below the variable count.
A warning is recorded if any sampled output bit is low-degree or if the maximum
degree is below `variables - 1`.

This stresses whether selected seed bits reach sampled output bits through a
high-degree-looking black-box map. It is not full algebraic cryptanalysis. It
does not construct the Boolean equations of the round function, search
invariants, run SAT/SMT/MILP, or compute useful full-state ANF degree.

### Collision, Birthday, and Near-Collision Screens

File: `screens/collision_screen.py`

This script samples `F(seed)` for deterministic random 64-bit seeds. It first
counts exact repeated 256-bit outputs. It then truncates those outputs to
prefix lengths:

```text
16, 24, 32, 40, 48, 64 bits
```

and compares observed prefix collision pairs with the birthday expectation:

```text
samples * (samples - 1) / (2 * 2^prefix_bits)
```

For prefix tests with expected count at least 10, the screen warns when the
observed count is more than `max(5 sigma, 10)` from expectation. For very small
expected counts, it warns only on large excess collision counts. The same
script also samples output pairs and reports min/mean/max Hamming distance as a
near-collision sanity check; it warns if the minimum sampled distance drops
below 80 bits.

This stresses gross collision defects, bad prefix distribution, and unusually
close sampled output pairs. The sample sizes are intentionally practical and
are far below cryptographic collision-resistance validation.

### Overlap/Fork Stream Uniqueness Screen

File: `screens/overlap_fork_screen.py`

This screen checks whether related stream seeds produce repeated blocks within
one stream or overlapping blocks across streams. For each variant, it generates
streams for:

```text
seed
seed + 1
seed xor 1
seed xor 2^63
```

It tests block sizes of 16, 32, and 64 bytes. For each block size it reports:

- repeated blocks within each stream;
- blocks that appear in more than one stream;
- same-position equality between `seed` and `seed + 1`;
- Hamming distance between the first 1024 bytes of adjacent-seed streams.

Any repeated, overlapping, or same-position equal block is a failure. This
stresses seed separation, fork behavior, and obvious stream overlap. It does
not prove stream independence.

### Black-Box State-Recovery/Predictability Screen

File: `screens/state_recovery_screen.py`

This screen treats stream output as a sequence to be predicted without internal
state access. It generates one stream, splits it into train and test halves, and
evaluates deliberately simple predictors:

- most-common-byte predictor from the training half;
- one-byte-context next-byte predictor from training transitions;
- global majority-bit predictor;
- Berlekamp-Massey binary linear complexity for bit positions `0`, `1`, and
  `7` over the first `--bm-bits` bytes.

The `--bm-bits` flag name is historical; the current implementation slices
that many bytes from the stream and then extracts one bit position from each
byte.

The reported baselines include the random next-byte rate `1/256` and expected
bit accuracy near `0.5`. The screen warns if next-byte or one-byte-context
accuracy exceeds `0.02`, or if bit accuracy differs from `0.5` by more than
`0.02`.

This stresses obvious black-box predictability and low-complexity bit streams.
It is not a state-recovery attack. A real state-recovery attack would model the
internal state transition or output function.

### Low-Bit Diagnostic Screen

File: `screens/low_bit_diagnostics.py`

This screen exists because low-bit warnings have been the most important
external-battery concern. It generates stream bytes and separately measures:

- lowest bit of every byte;
- lowest bit of every 32-bit little-endian word;
- lowest bit of every 64-bit little-endian word;
- low-nibble distribution over 16 values;
- bit-position counts across 64-bit output words;
- low-bit transition counts `00`, `01`, `10`, `11`;
- lag-1 correlation of byte low bits;
- lag-1 correlation of byte high bits for comparison.

The screen uses z-scores for one-count balance, chi-square for low nibbles, and
Pearson lag-1 correlation for bit transitions. It warns when the maximum
balance z-score exceeds `6.0`, low-nibble chi-square exceeds `45.0`, or
absolute low-bit lag-1 correlation exceeds `0.01`.

This stresses exactly the part of the output where PractRand warnings appeared.
It is weaker than PractRand and can miss patterns that PractRand catches, but
it gives a fast local diagnostic while developing variants.

### White-Box Word-Dependency Model

Files:

- `screens/whitebox_round_model.py`
- `models/tricube_schedule.py`

This is the one screen that is not purely black-box. It imports a TriCube
schedule model that generates the 27 vertex lanes, 5 shell lanes, 8 cube cells,
48 tetrahedra, 54 positive-axis grid edges, shell targets, and 32-lane
permutation. The model validates those counts before analysis.

The dependency model starts with each state lane depending only on itself. For
each modeled round it applies the same schedule shape as the specification:

1. each tetrahedron merges the dependency sets of its four lanes;
2. each grid edge merges the dependency sets of its two endpoint lanes;
3. each shell lane merges with a scheduled vertex lane, and a scheduled
   opposite vertex receives that shell/vertex dependency;
4. the lane permutation moves dependency sets to their destination lanes.

The output model then checks the lanes read for the first four output words
(the first 32 output bytes). The report records per-round minimum, mean, and
maximum dependency size, how many lanes depend on all 32 initial lanes, and
when the first 32 output bytes reach full word-lane dependency.

This screen tests schedule reachability and coverage: whether every lane can
influence every other lane at 64-bit word granularity under the current
tetrahedron/edge/shell/permutation schedule. It does not model bit-level ARX
probabilities, modular-addition carries, rotational trails, algebraic degree,
or attack cost.

### External Battery Availability Screen

File: `screens/external_batteries.py`

The all-in-one quick run does not launch long external batteries. Instead, this
screen checks whether expected binaries are on `PATH`:

- PractRand `RNG_test`;
- SmokeRand `smokerand`;
- TestU01 stdin adapter `testu01_stdin32`;
- Dieharder `dieharder`;
- NIST STS `assess`.

If a tool is detected, the row is `NOT_RUN` because the quick suite did not
launch it. If the tool is absent, the row is `BLOCKED`. This avoids confusing a
missing local battery install with a statistical pass or failure.

## Individual Commands

The all-in-one runner calls the same screen modules listed below. Reviewers can
run any screen by itself when they want to inspect one method, one output table,
or one threshold policy.

| Screen | Command |
|---|---|
| Differential diffusion | `python tests/crypto_analysis/screens/differential_screen.py --variants baseline,fast8x,fast8x1024mix --samples 64 --out tests/crypto_analysis/results/differential-latest` |
| Rotational relation | `python tests/crypto_analysis/screens/rotational_screen.py --variants baseline,fast8x,fast8x1024mix --samples 64 --out tests/crypto_analysis/results/rotational-latest` |
| Algebraic degree | `python tests/crypto_analysis/screens/algebraic_degree_screen.py --variants baseline,fast8x,fast8x1024mix --variables 8 --output-bits 32 --out tests/crypto_analysis/results/algebraic-latest` |
| Collision and birthday | `python tests/crypto_analysis/screens/collision_screen.py --variants baseline,fast8x,fast8x1024mix --samples 512 --near-pairs 256 --out tests/crypto_analysis/results/collision-latest` |
| Overlap/fork uniqueness | `python tests/crypto_analysis/screens/overlap_fork_screen.py --variants baseline,fast8x,fast8x1024mix --bytes 1048576 --out tests/crypto_analysis/results/overlap-latest` |
| State-recovery/predictability | `python tests/crypto_analysis/screens/state_recovery_screen.py --variants baseline,fast8x,fast8x1024mix --bytes 1048576 --bm-bits 4096 --out tests/crypto_analysis/results/state-recovery-latest` |
| Low-bit diagnostics | `python tests/crypto_analysis/screens/low_bit_diagnostics.py --variants baseline,fast8x,fast8x1024mix --bytes 16777216 --out tests/crypto_analysis/results/low-bit-latest` |
| White-box word-dependency model | `python tests/crypto_analysis/screens/whitebox_round_model.py --rounds 24 --out tests/crypto_analysis/results/whitebox-latest` |
| External battery availability | `python tests/crypto_analysis/screens/external_batteries.py --variants baseline,fast8x --out tests/crypto_analysis/results/external-latest` |

Hash-mode screens are in `hash_mode/` and can be run together or individually.
They are separate because their input source is a sequence of messages and
their output source is `tricube_hash()`, not stream bytes.

| Hash-mode screen | Command |
|---|---|
| All hash-mode screens | `python tests/crypto_analysis/hash_mode/run_hash_screens.py --profile quick --implementations baseline_hash --out tests/crypto_analysis/results/hash-quick-latest` |
| Hash differential diffusion | `python tests/crypto_analysis/hash_mode/differential_hash_screen.py --implementations baseline_hash --samples 64 --out tests/crypto_analysis/results/hash-differential-latest` |
| Hash rotational relation | `python tests/crypto_analysis/hash_mode/rotational_hash_screen.py --implementations baseline_hash --samples 64 --out tests/crypto_analysis/results/hash-rotational-latest` |
| Hash algebraic degree | `python tests/crypto_analysis/hash_mode/algebraic_hash_screen.py --implementations baseline_hash --variables 8 --output-bits 32 --out tests/crypto_analysis/results/hash-algebraic-latest` |
| Hash collision and birthday | `python tests/crypto_analysis/hash_mode/collision_hash_screen.py --implementations baseline_hash --samples 512 --near-pairs 256 --out tests/crypto_analysis/results/hash-collision-latest` |
| Hash low-bit diagnostics | `python tests/crypto_analysis/hash_mode/low_bit_hash_screen.py --implementations baseline_hash --samples 4096 --out tests/crypto_analysis/results/hash-low-bit-latest` |

Low-bit diagnostics at 16 MiB per variant:

```bash
python tests/crypto_analysis/screens/low_bit_diagnostics.py \
  --variants baseline,fast8x,fast8x1024mix \
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

## Output Format

Each run writes:

- `summary.json` with metadata, exact command, branch, commit, machine, Python
  version, profile, seed, variants, and status counts;
- `summary.md` with compact interpreted tables;
- one CSV and one Markdown summary for each screen;
- `all_screens.csv` with every row in one compact table.

Large raw streams and external battery logs are not stored here. External tools
should write their summaries under `results/` or another documented results
location.

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
