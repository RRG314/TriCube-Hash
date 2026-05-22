# Testing

TriCube uses three different kinds of tests, and they should not be collapsed into one security claim. Unit tests check implementation behavior. Statistical batteries look for detectable non-randomness in output streams. The black-box probes in this repository are development gates: they can find obvious failures or warning patterns, but they do not replace white-box cryptanalysis.

The current public wording is intentionally conservative. A `PASS` means that no issue was detected under the stated test budget. It does not mean that TriCube is secure, collision resistant, preimage resistant, or safe for production cryptography.

## Local Implementation Tests

Run the C and Python checks before interpreting any statistical result:

```bash
make -C c test
python -m pip install -e ".[test]"
pytest -q
```

These tests cover deterministic behavior, output lengths, test-vector agreement, C/Python agreement, CLI behavior, domain separation, and package import behavior. They are implementation tests, not security tests.

## CLI Smoke Tests

```bash
c/build/tricube self-test
c/build/tricube hash --hex 616263
c/build/tricube xof --hex 616263 --bytes 64
c/build/tricube stream --seed 123 --bytes 1024 --out results/tmp/stream.bin
c/build/tricube stream --seed 123 --bytes 1024 --out results/tmp/stream-fast8x.bin --variant fast8x
c/build/tricube stream --seed 123 --bytes 1024 --out results/tmp/stream-fast8x1024mix.bin --variant fast8x1024mix
```

The default stream path is the released baseline. The `fast8x` and
`fast8x*mix` stream variants are experimental and must be requested explicitly.
The compact ablation record is in [tests/ablation_lab/](../tests/ablation_lab/).

## Status Labels

TriCube result tables use the following labels:

| Label | Meaning |
|---|---|
| `PASS` | No issue was detected under this test budget. |
| `WARN` | The result is suspicious or needs follow-up, but is not a conclusive failure. |
| `FAIL` | The test or tool reported a clear failure under its criteria. |
| `BLOCKED` | A missing tool, missing binary, input exhaustion, timeout, or harness issue prevented the test from completing. |
| `NOT_RUN` | The test was available in principle but was not attempted in that run. |

EOF, SIGPIPE, timeout, and input exhaustion are harness conditions. They must not be recorded as statistical `PASS` results.

## Testing Methodology and Limits

This section explains what each test family is normally meant to detect, what TriCube currently does, what it does not prove, and what stronger work would require.

### Avalanche and Diffusion Tests

Avalanche tests check whether small input changes produce broad output changes. The usual engineering target for a 256-bit digest is that flipping one input bit changes roughly half the output bits. This is related to the strict avalanche criterion introduced by Webster and Tavares.

TriCube currently measures output Hamming distance, output-bit flip probability, and bit-influence spread for selected message, seed, and stream perturbations. The current black-box diffusion screens are implemented in [tests/crypto_analysis/run_all_screens.py](../tests/crypto_analysis/run_all_screens.py). In the quick profile, each variant is checked with 64 samples for each selected delta class. The compact output is written to `differential_screen.csv`, `differential_screen.md`, `summary.json`, and `summary.md`.

This is a useful development check, but it does not model the round function internally. A stronger version would include per-round hooks, explicit difference-propagation models for the ARX layers, and reduced-round trail search.

### Differential Cryptanalysis vs. the Current Black-Box Differential Diffusion Probe

Differential cryptanalysis studies how input differences propagate through a primitive and searches for differential characteristics or trails with probabilities high enough to exploit. The classic Biham-Shamir DES work is the reference point for the term.

TriCube currently runs a **black-box differential diffusion probe**. It applies fixed and random seed deltas, then compares the first 32 bytes of deterministic stream output. The fixed delta classes are:

- single bit;
- single byte;
- single 64-bit word;
- all-low-bit mask;
- checkerboard mask;
- high-bit mask;
- adjacent-bit mask.

The random delta classes are low-weight, medium-weight, and full-weight deltas. The metrics are mean/min/max output Hamming distance, maximum output-bit bias, a chi-square score for bit flips, repeated output differences, and the top repeated difference count. The screen accepts variants such as `baseline` and `fast8x`, seeds, sample counts, and an output directory:

```bash
python tests/crypto_analysis/run_all_screens.py \
  --profile quick \
  --variants baseline,fast8x,fast8x1024mix \
  --out tests/crypto_analysis/results/quick-latest
```

This is not formal differential cryptanalysis. It does not search trails, compute maximum differential probability, build a white-box propagation model, or establish resistance to differential attacks. A real differential program for TriCube would need to model modular addition, XOR, rotation, tetrahedral lane schedules, constants, and output extraction, then search reduced-round trails and estimate attack complexity.

### Rotational Cryptanalysis vs. the Current Black-Box Rotational Relation Probe

Rotational cryptanalysis studies whether rotations of input words propagate through ARX systems in a structured way. Khovratovich and Nikolic's ARX work is the relevant reference family.

TriCube currently runs a **black-box rotational relation probe**. It tests rotations `1, 2, 3, 4, 5, 7, 8, 13, 16, 17, 31, 32, 33, 47, 63`. For each rotation, it rotates the seed, generates the first 32 bytes of stream output, and compares that output against a word-rotated version of the unrotated output. The metrics are exact rotational relation count, mean rotational distance, min/max distance, maximum output-bit bias, and a z-score for mean distance.

This is not formal rotational cryptanalysis. It does not prove resistance to rotational distinguishers. A stronger version would need a white-box model of how rotations move through modular additions, xors, constants, lane schedules, shell/global lanes, and output extraction.

### Algebraic Analysis vs. the Current Small Black-Box Algebraic Degree Screen

Algebraic analysis represents a primitive as Boolean or finite-field equations and searches for low-degree structure, invariants, or solvable systems. Serious algebraic work can involve full ANF extraction, SAT/SMT/MILP encodings, Gröbner-basis methods, or invariant searches.

TriCube currently runs a **small black-box algebraic degree screen**. The screen varies selected input bits, evaluates selected output bits, applies a Möbius transform over the sampled truth table, and reports min/mean/max ANF degree plus the number of low-degree output bits. The quick profile uses 8 variables and 32 output bits; the standard profile uses 10 variables and 64 output bits. The code refuses variable counts above 12 because the cost is exponential.

This screen is deliberately small. It can catch obvious low-degree black-box behavior, but it is not full algebraic cryptanalysis. A stronger version would require a verified symbolic model of the TriCube round function and a search for exploitable relations or invariants.

### Collision, Birthday, and Near-Collision Checks

Collision resistance is a cryptographic property. Small collision tests cannot validate it, but they can catch gross defects such as accidental truncation, repeated outputs, broken domain separation, or poor prefix behavior.

TriCube currently runs a **collision/birthday sanity check** and a **near-collision sanity check**. The collision screen samples deterministic outputs, checks full 256-bit digest repeats, and compares prefix collision counts for 16, 24, 32, 40, 48, and 64-bit prefixes against birthday expectations. The near-collision screen samples output pairs and records Hamming-distance summaries.

The quick profile uses 512 outputs and 256 sampled pairs. The standard profile uses 4096 outputs and 2048 sampled pairs. These counts are far below cryptographic collision-resistance validation. Larger campaigns would need much larger samples, careful memory-efficient counting, multi-seed coverage, and independent reproduction.

### Overlap/Fork Stream Uniqueness Screen

Fork and overlap tests look for repeated blocks within one stream or across related streams. They are useful for stream-mode engineering because repeated blocks or same-position equality across adjacent seeds can indicate a catastrophic state or counter bug.

TriCube currently runs an **overlap/fork stream uniqueness screen**. It checks adjacent seeds, low-weight seed differences, and a high-bit seed difference. It evaluates 16, 32, and 64-byte block sizes. The quick profile uses 1 MiB per seed; the standard profile uses 16 MiB per seed. The metrics are repeated blocks within a stream, overlaps across streams, same-position equality, and adjacent-seed prefix Hamming distance over the first 1024 bytes.

This screen does not prove stream independence or pseudorandomness. A stronger version would expand seed classes, stream sizes, and block-position analysis, then combine it with PractRand seed-target modes or a custom white-box related-seed study.

### State-Recovery and Predictability Screen

State-recovery attacks exploit knowledge of a transition or output function to recover internal state. A black-box prediction test is much weaker.

TriCube currently runs a **black-box state-recovery/predictability screen**. It splits generated bytes into train and test halves, then evaluates a next-byte frequency predictor, a one-byte-context predictor, bit-position majority accuracy, and Berlekamp-Massey linear complexity on selected bit streams. The quick profile uses 1 MiB total stream data and 4096 bits per selected bit stream; the standard profile uses 16 MiB and 16,384 bits.

This is not state-recovery cryptanalysis. A real state-recovery attempt would exploit the exact transition function, output extraction, state size, and round schedule, then quantify work factor or demonstrate recovery on reduced-round variants.

### Low-Bit Diagnostic Screen

Low-bit diagnostics matter because the May 2026 PractRand run reported low-bit NS3 warnings. Internal diagnostics are weaker than PractRand, but they are useful for isolating likely failure modes before long battery runs.

TriCube currently runs a **low-bit diagnostic screen**. It measures:

- lowest bit of each byte;
- lowest bit of each 32-bit word;
- lowest bit of each 64-bit word;
- low-nibble distribution;
- bit-position frequency over all 64 bit positions;
- low-bit transition counts;
- lag-1 correlation for low and high bit streams.

The standalone low-bit command is:

```bash
python tests/crypto_analysis/screens/low_bit_diagnostics.py \
  --variants baseline,fast8x,fast8x1024mix \
  --bytes 16777216 \
  --out tests/crypto_analysis/results/low-bit-latest
```

If this screen misses a PractRand warning, PractRand takes priority. The local diagnostic is a microscope, not a replacement for a battery.

### White-Box Round-Model Analysis

The black-box probes above observe output bytes. The repository also
contains a first white-box schedule analyzer:

```bash
python tests/crypto_analysis/screens/whitebox_round_model.py \
  --rounds 24 \
  --out tests/crypto_analysis/results/whitebox-latest
```

This script implements the specified tetrahedron, edge, shell, and permutation
schedule directly. It tracks which original 64-bit lanes can influence each
later 64-bit lane after each modeled round, and it records schedule-coverage
facts such as tetrahedron count, edge count, shell-lane coverage, and rotation
constant coverage.

The latest local run found that word-level dependency reaches all 32 modeled
source lanes by round 2 for the tracked state lanes and for the first 32 output
bytes. That is useful structural information, but it is not a security bound.
It does not model bit-level differential probability, rotational trails,
algebraic degree, SAT/SMT/MILP constraints, or attack complexity.

## Current Screen Suite

The reproducible screen suite lives in [tests/crypto_analysis/](../tests/crypto_analysis/). It records date, branch, commit, machine, OS, Python version, command line, variants, seeds, sample counts, bytes generated, output paths, and status counts.

Profiles are intentionally modest so they can run on a laptop:

| Profile | Samples | Algebraic variables | Algebraic output bits | Collision samples | Near pairs | Stream bytes per variant | BM bits |
|---|---:|---:|---:|---:|---:|---:|---:|
| `quick` | 64 | 8 | 32 | 512 | 256 | 1 MiB | 4096 |
| `standard` | 256 | 10 | 64 | 4096 | 2048 | 16 MiB | 16384 |

Run the quick suite:

```bash
python tests/crypto_analysis/run_all_screens.py \
  --profile quick \
  --variants baseline,fast8x,fast8x1024mix \
  --out tests/crypto_analysis/results/quick-latest
```

Run the standard suite when runtime allows:

```bash
python tests/crypto_analysis/run_all_screens.py \
  --profile standard \
  --variants baseline,fast8x,fast8x1024mix \
  --out tests/crypto_analysis/results/standard-latest
```

Each run writes `summary.json`, `summary.md`, one CSV and Markdown table per screen, and `all_screens.csv`. It does not store large raw streams.

Each screen can also be run on its own from `tests/crypto_analysis/screens/`.
The individual entry points are:

| Screen | Script |
|---|---|
| Black-box differential diffusion probe | `tests/crypto_analysis/screens/differential_screen.py` |
| Black-box rotational relation probe | `tests/crypto_analysis/screens/rotational_screen.py` |
| Small black-box algebraic degree screen | `tests/crypto_analysis/screens/algebraic_degree_screen.py` |
| Collision/birthday and near-collision sanity checks | `tests/crypto_analysis/screens/collision_screen.py` |
| Overlap/fork stream uniqueness screen | `tests/crypto_analysis/screens/overlap_fork_screen.py` |
| Black-box state-recovery/predictability screen | `tests/crypto_analysis/screens/state_recovery_screen.py` |
| Low-bit diagnostic screen | `tests/crypto_analysis/screens/low_bit_diagnostics.py` |
| White-box word-dependency model | `tests/crypto_analysis/screens/whitebox_round_model.py` |
| External battery availability check | `tests/crypto_analysis/screens/external_batteries.py` |

The all-in-one runner imports these same modules. There is no second hidden
implementation of the screens.

## Hash-Mode Screen Suite

The stream screens above do not test the hash API. Hash-mode screens live in
[`tests/crypto_analysis/hash_mode/`](../tests/crypto_analysis/hash_mode/) and
exercise the public C digest path:

```bash
c/build/tricube hash --hex MESSAGE_HEX
```

The current implementations are `baseline_hash`, `hashfast1024`, and
`hashfast1024r6`. These names are deliberately separate from stream variants
such as `fast8x` and `fast8x1024mix`. The `hashfast` entries are experimental
opt-in candidates with separate domain tags and fixed C vectors; they do not
replace the baseline hash/XOF path.

Run the hash-mode quick profile:

```bash
python tests/crypto_analysis/hash_mode/run_hash_screens.py \
  --profile quick \
  --implementations baseline_hash,hashfast1024,hashfast1024r6 \
  --out tests/crypto_analysis/results/hash-quick-latest
```

The hash-mode quick profile checks deterministic 64-byte messages. It runs
digest-path versions of the differential diffusion, rotational relation,
small algebraic degree, collision/birthday, near-collision, and low-bit
screens. The low-bit screen concatenates many 32-byte digests; this is useful
for digest-output diagnostics, but it is not the same as testing native XOF or
stream output.

For external batteries over concatenated digests, use:

```bash
c/build/tricube digest-stream \
  --variant hashfast1024 \
  --seed 123 \
  --messages 524288 \
  --message-bytes 64 \
  --out -
```

Any PractRand, TestU01, Dieharder, SmokeRand, or NIST STS run fed by this
helper should be labeled as a digest-concatenation test. It should not be
presented as a native XOF or stream test.

## From Screens to Proper Cryptanalysis

The current screens are useful because they are cheap, reproducible, and good
at catching obvious mistakes. They are not enough for a cryptographic primitive
claim. The next level is to build a verified TriCube model and run bounded
white-box searches with established tooling.

| Current screen | What it catches | Proper next test | Suggested open-source tooling |
|---|---|---|---|
| Black-box differential diffusion probe | Bad avalanche, repeated output differences, output-bit bias under selected deltas. | Reduced-round differential trail search with modular-addition difference modeling and probability estimates. | Z3, MILP tooling, CLAASP, CryptoSMT, ArxPy if the TriCube schedule can be represented cleanly. |
| Black-box rotational relation probe | Obvious preserved word rotations in stream output. | White-box rotational trail search through constants, additions, rotations, shell lanes, and output extraction. | Z3 or another SMT solver with a custom ARX model; ArxPy-style methods if adaptable. |
| Small black-box algebraic degree screen | Trivial low-degree behavior under a small sampled input space. | Symbolic algebraic-degree growth, invariant search, and reduced-round equation systems. | SageMath, SAT solvers, SMT solvers, Gröbner-style tooling where appropriate. |
| Collision/birthday sanity check | Gross digest repetition, broken truncation, and prefix-count anomalies at practical sample sizes. | Reduced-round collision or preimage search with validated constraints and expected-cost reporting. | Z3, CryptoMiniSat, CLAASP/CryptoSMT-style encodings. |
| Overlap/fork stream uniqueness screen | Repeated stream blocks and related-seed overlap bugs. | Related-seed or related-state analysis over the reduced-round transition and output layer. | Z3/SAT plus a custom related-seed model. |
| Black-box state-recovery/predictability screen | Simple next-byte, bit-majority, n-gram, and linear-complexity predictability. | Reduced-round state-recovery equations and output-inversion experiments. | SMT/SAT solvers and a bit-exact reduced-round model. |
| Low-bit diagnostic screen | Local low-bit frequency, transition, lag, and byte-position anomalies. | Targeted reduced-round low-bit propagation model and multi-seed external battery campaign. | Z3, SageMath, custom ARX model, PractRand, TestU01, Dieharder. |

The practical path is:

1. keep the black-box screens as regression gates;
2. keep using external statistical batteries for stream output;
3. build a bit-exact reduced-round TriCube model from the specification;
4. validate that model against known vectors and reduced-round reference
   outputs;
5. use Z3, SageMath, SAT, MILP, or cryptanalysis frameworks to search bounded
   reduced-round problems;
6. report solver results with assumptions, round counts, constraints, and
   failure conditions.

The tooling plan is in [docs/tooling.md](tooling.md). The first reusable
TriCube-specific schedule model is
[`tests/crypto_analysis/models/tricube_schedule.py`](../tests/crypto_analysis/models/tricube_schedule.py).

## External Statistical Batteries

External batteries are separate from the black-box development probes. They are stronger empirical statistical screens, but they still do not prove cryptographic security.

TriCube does not bundle PractRand, Dieharder, TestU01, SmokeRand, NIST STS, or their binaries. Install each tool from its upstream source or package manager and follow that tool's license. The repository notice table is [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md), and command templates are in [tools/run_stat_batteries.md](../tools/run_stat_batteries.md).

The recommended profiles are:

| Profile | Purpose | Suggested checks |
|---|---|---|
| Quick | Catch obvious regressions before longer runs. | Internal screens, PractRand 256 MiB, SmokeRand express, TestU01 SmallCrush. |
| Standard | Produce a useful development evidence snapshot. | PractRand 1-10 GiB, Dieharder full, TestU01 Crush, NIST STS documented run. |
| Long | Look for slow-forming statistical problems and multi-seed instability. | PractRand 100 GiB+, TestU01 BigCrush, SmokeRand full, multi-seed campaign. |

Harness failures must be separated from statistical failures. EOF, SIGPIPE, input exhaustion, and timeout should be recorded as `BLOCKED` unless the downstream tool reports a valid statistical result before the harness stops.

## What the Probes Are Not

The black-box differential diffusion probe does not model differential propagation through the round function. It does not search trails. It does not compute or bound maximum differential probability. It does not replace differential cryptanalysis.

The black-box rotational relation probe does not prove resistance to rotational distinguishers. It only checks selected rotations for obvious preserved relations.

The small black-box algebraic degree screen does not perform SAT, SMT, MILP, Gröbner-basis, full ANF, invariant, or integral cryptanalysis. It only samples small black-box algebraic behavior for selected variables and output bits.

The collision/birthday sanity check is not collision-resistance evidence. The sample sizes are practical engineering checks, not cryptographic-scale searches.

The overlap/fork stream uniqueness screen does not prove stream independence or safe related-seed behavior.

The black-box state-recovery/predictability screen is not a state-recovery proof. It does not model or recover the internal state.

Passing these probes means no obvious failure was detected under the tested budget. It does not establish security.

## Terminology Correction

Earlier project notes used phrases such as "differential probes," "rotational probes," and "algebraic screens." These are intentionally named probes/screens because they are not formal cryptanalysis. They are black-box development checks meant to find obvious failures before deeper analysis. Formal differential, rotational, and algebraic cryptanalysis remains future work.

## Method References

The documentation style and limits above are based on standard cryptographic and statistical-testing references:

- Biham and Shamir, "Differential Cryptanalysis of DES-like Cryptosystems," *Journal of Cryptology*, 1991, DOI: https://doi.org/10.1007/BF00630563.
- Khovratovich and Nikolic, "Rotational Cryptanalysis of ARX," FSE 2010, IACR PDF: https://www.iacr.org/archive/fse2010/61470339/61470339.pdf.
- Courtois and Pieprzyk, "Cryptanalysis of Block Ciphers with Overdefined Systems of Equations," ASIACRYPT 2002, ePrint: https://eprint.iacr.org/2002/044.
- NIST SP 800-22 Rev. 1a, "A Statistical Test Suite for Random and Pseudorandom Number Generators for Cryptographic Applications": https://csrc.nist.gov/projects/random-bit-generation/documentation-and-software.
- L'Ecuyer and Simard, "TestU01: A C Library for Empirical Testing of Random Number Generators," ACM TOMS 2007, DOI: https://doi.org/10.1145/1268776.1268777.
- PractRand documentation: https://pracrand.sourceforge.net/.
- Dieharder manual: https://rurban.github.io/dieharder/manual/dieharder.html.
- SmokeRand repository: https://github.com/alvoskov/SmokeRand.
