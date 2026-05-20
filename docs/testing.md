# Testing

TriCube uses several layers of testing. Each layer answers a different question.

Unit tests verify deterministic behavior, output lengths, vector agreement, CLI behavior, and basic stream separation. They do not evaluate security.

Project statistical checks measure byte entropy, bit balance, serial correlation, chi-square behavior, block entropy, avalanche response, throughput, and simple repetition/cycle smoke checks. These are useful for finding obvious flaws.

External batteries such as PractRand, Dieharder, TestU01, SmokeRand, and NIST STS are stronger statistical screens. They can identify suspicious output structure, but they still do not prove cryptographic security.

Those external batteries are not bundled with TriCube. Install them separately
from their upstream sources or your package manager, and follow their licenses.
The repository notice table is [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md).

Cryptanalytic analysis is a separate requirement. TriCube still needs formal reduced-round attacks, differential trail work, rotational-distinguisher analysis, algebraic analysis, collision-search campaigns, fork/overlap studies, and state-recovery studies.

## Local Tests

```bash
make -C c test
python -m pip install -e ".[test]"
pytest -q
```

## CLI Smoke Tests

```bash
c/build/tricube self-test
c/build/tricube hash --hex 616263
c/build/tricube xof --hex 616263 --bytes 64
c/build/tricube stream --seed 123 --bytes 1024 --out results/tmp/stream.bin
c/build/tricube stream --seed 123 --bytes 1024 --out results/tmp/stream-fast8x.bin --variant fast8x
```

The default stream path is the released baseline. The `fast8x` stream variant is
experimental and must be requested explicitly. It was added because the ablation
lab found it to be the cleanest optimized stream candidate tested so far. The
compact public record is in [experiments/ablation-lab/](../experiments/ablation-lab/).

## Current Development Probes

The project uses a small set of black-box probes as development gates. They are
intended to catch obvious failures before deeper review. They are not formal
cryptanalysis.

### Black-box differential probe

The current public result records selected input differences across reduced
round counts `1, 2, 4, 8, 12, 16`. The measured outputs are compared by Hamming
distance, output-bit balance, and repeated output differences. The May 2026
summary reports no repeated output differences and mean changed bits near 128
of 256 under the tested budget.

This is not trail-based differential cryptanalysis. It does not enumerate
differential trails, estimate or bound maximum differential probability, or
prove resistance to differential attacks.

TODO: clean and publish the exact probe script with its sample count, delta
set, input distribution, and pass/fail thresholds.

### Black-box rotational probe

The current public result records rotations `1, 7, 8, 13, 16, 32` across reduced
round counts `1, 2, 4, 8, 12, 16`. The measured quantities are rotational
distance and exact preserved-relation counts. The May 2026 summary reports no
exact rotational relation and mean distances near 128 bits under the tested
budget.

This is not formal rotational cryptanalysis. It only checks selected rotations
for obvious preserved relations in a black-box setting.

TODO: clean and publish the exact rotational-probe script with its sample count,
message generation rule, and threshold policy.

### Small black-box algebraic screen

The current public result records a small sampled algebraic-normal-form screen.
It samples selected variables and output bits and reports that the sampled
10-variable cases reached degree 10 across the tested rounds.

This is not algebraic cryptanalysis. It does not run SAT, MILP, Gröbner-basis
analysis, full ANF extraction, invariant search, or integral analysis.

TODO: clean and publish the exact algebraic-screen script with variable
selection, output-bit selection, sample budget, and degree-computation method.

### Overlap/fork stream screen

The current public result checks related streams for repeated 32-byte blocks.
The May 2026 summary reports `0` repeated 32-byte overlaps across 4 streams and
262,144 tested blocks.

This screen can catch obvious stream overlap or fork mistakes. It does not prove
stream independence or resistance to state compromise.

### State-recovery screen

The current public result reports a next-byte prediction accuracy of
`0.00396061`, bit accuracy of `0.500095`, and a linear-complexity ratio of
`0.5`. These values are close to simple random baselines under the recorded
screen.

This screen is not a state-recovery proof. It does not model the internal state,
solve for state words, or rule out stronger predictors.

TODO: clean and publish the exact predictor model, train/test split, input
features, sample count, and random baseline calculation.

### Collision and birthday screens

The current public birthday screen compares truncated prefix collision counts
against expectation at 16, 24, 32, 48, and 64 bits. The recorded counts were:

| Prefix | Observed | Expected |
|---:|---:|---:|
| 16 bit | 19,278 | 19,073 |
| 24 bit | 295 | 298 |
| 32 bit | 2 | 1.16 |
| 48 bit | 0 | near 0 |
| 64 bit | 0 | near 0 |

The full-digest smoke check reports `0` full digest collisions over 20,000
sampled messages. These are small engineering checks, not cryptographic
collision-resistance evidence.

## What the Probes Are Not

The black-box differential probe does not model differential propagation through
the round function. It does not search trails. It does not compute or bound
maximum differential probability. It does not replace differential
cryptanalysis.

The black-box rotational probe does not prove resistance to rotational
distinguishers. It only checks selected rotations for obvious preserved
relations.

The small black-box algebraic screen does not perform SAT, MILP, Gröbner-basis,
full ANF, or invariant cryptanalysis. It only samples small black-box algebraic
behavior for selected variables and output bits.

The state-recovery screen is not a state-recovery proof. It is a predictor
sanity check under one limited setup.

Passing these probes means no obvious failure was detected under the tested
budget. It does not establish security.

## Terminology Correction

Earlier project notes used phrases such as differential probes, rotational
probes, and algebraic screens. These are intentionally probes/screens because
they are not formal cryptanalysis. They are black-box development checks meant
to find obvious failures before deeper analysis. Formal differential,
rotational, and algebraic cryptanalysis remains future work.

## Interpreting Failures

A unit-test failure is an implementation failure. A statistical battery failure may indicate a structural weakness, a stream-format problem, a test-harness problem, or a reduced-quality region that needs diagnosis. A timeout is not a randomness failure; it is a performance or harness blocker.

Passing statistical batteries should be recorded as evidence of no detected failure under those conditions, not as a security claim.
