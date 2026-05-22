# TriCube

TriCube is an experimental hash, extendable-output function (XOF), and deterministic stream generator based on tetrahedral/cube-connected state evolution. The current implementation uses a 2048-bit state arranged as a cube-vertex grid plus shell lanes; each round mixes local tetrahedral groups, propagates across cube edges, couples shell lanes, and squeezes output from the evolved state.

TriCube is a cryptographic engineering research project, not a secure primitive. It is not production ready, not a replacement for SHA-2, SHA-3/SHAKE, BLAKE2, or BLAKE3, and should not be used for security-critical applications. The current evidence supports continued development and external review. It does not establish collision resistance, preimage resistance, pseudorandomness, or real-world security.

## Current Status

The repository contains a standalone C11 implementation, a Python reference package, fixed test vectors, CLI tools, benchmarks, reproducibility notes, external-battery run scripts, a result summary, and a manuscript.

The strongest current result is that TriCube now has a concrete geometric construction with reproducible C/Python vectors, nontrivial statistical-battery evidence, and opt-in C stream variants fast enough for larger external batteries. The main open issues are unresolved low-bit warnings in some variants, incomplete cryptanalysis, and hash-mode performance that is still below mature optimized hash implementations.

## Specification and Security Boundary

The primitive is specified in [docs/specification.md](docs/specification.md). That document gives the public baseline state size, lane layout, tetrahedral decomposition, round transformation, modes, padding, length encoding, domain tags, and test vectors.

The security boundary is in [docs/security-status.md](docs/security-status.md). TriCube has black-box development probes and statistical-battery results, but it does not have formal differential, rotational, algebraic, or reduced-round cryptanalysis. The terms used in this repository are deliberately narrow: a probe or screen is an engineering check for obvious failures, not a security proof.

The reproducible black-box screen suite is in
[tests/crypto_analysis/](tests/crypto_analysis/). It records the
exact command, branch, commit, machine, seed, byte count, and status labels for
each compact run. The same folder also contains a first white-box round-model
analyzer that checks word-level schedule dependency and coverage without
claiming formal cryptanalysis. Stream-output screens and hash-mode screens are
kept separate so stream results are not used as evidence for digest behavior.

## Quick Start

Build and test the C implementation:

```bash
git clone https://github.com/RRG314/tricube-hash.git
cd tricube-hash
make -C c test
```

Hash a message with the C CLI:

```bash
c/build/tricube hash --hex 616263
```

Install the Python package for local development:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[test]"
pytest -q
```

Use the Python API:

```python
import tricube

digest = tricube.hash(b"abc")
print(tricube.hexdigest(b"abc"))

out = tricube.xof(b"abc", 64)
stream = tricube.stream(seed=123, n=1024)
```

## Build and CLI

The C implementation is the primary implementation path. It is standalone C11 and does not require Python at runtime.

```bash
c/build/tricube self-test
c/build/tricube vectors
c/build/tricube hash --hex 616263
c/build/tricube hash --hex 616263 --variant hashfast1024
c/build/tricube hash path/to/file.bin
c/build/tricube xof --hex 616263 --bytes 64
c/build/tricube xof --hex 616263 --bytes 64 --variant hashfast1024
c/build/tricube stream --seed 123 --bytes 1048576 --out stream.bin
c/build/tricube stream --seed 123 --bytes 1048576 --out stream.bin --variant fast8x
c/build/tricube stream --seed 123 --bytes 1048576 --out stream.bin --variant fast8x1024mix
```

The public C header is [c/include/tricube.h](c/include/tricube.h). It exposes fixed 256-bit digest mode, XOF mode, context-style update/finalize/squeeze functions, deterministic stream generation, and self-test support.

The experimental hash variants `hashfast1024` and `hashfast1024r6` are
available through explicit C API and CLI variant selection. They use a wider
1024-byte absorb group to improve long-message throughput, but they do not
replace the baseline hash/XOF path.

The experimental `fast8x` stream entry points are kept visible in
[c/src/tricube_fast8x.c](c/src/tricube_fast8x.c). Newer feedback-mixed stream
candidates are available through the generic stream variant API and CLI. The
shared permutation and all stream profiles live in [c/src/tricube.c](c/src/tricube.c),
so the optimized paths remain named TriCube stream variants rather than forked
second implementations.

The Python CLI is available after installation:

```bash
python -m tricube hash --hex 616263
python -m tricube xof --hex 616263 --bytes 64
python -m tricube stream --seed 123 --bytes 1024 --out stream.bin
tricube self-test
```

## Design Summary

TriCube uses 32 lanes of 64 bits each. Twenty-seven lanes correspond to a 3 x 3 x 3 vertex grid; the remaining lanes act as shell/global lanes. The eight cube cells of the 2 x 2 x 2 block are each decomposed into six tetrahedra. A round applies orientation-dependent tetrahedral ARX mixing, edge coupling over adjacent vertices, shell coupling, and a global lane permutation.

Input bytes are absorbed with domain separation and length encoding. Digest mode squeezes 32 bytes. XOF mode squeezes an arbitrary number of bytes. Stream mode initializes from a seed and emits deterministic blocks for statistical testing.

The diagrams in [docs/specification.md](docs/specification.md) show the state
layout, tetrahedral decomposition, and round flow. The diagrams are explanatory;
the tables and pseudocode in the specification are the normative source.

The candidate novelty is the cube/tetrahedral state evolution and propagation schedule. It is not the use of hashing, XOFs, ARX operations, or sponge-like absorb/squeeze structure, all of which are established design families.

See [docs/specification.md](docs/specification.md) for the exact construction and [docs/design.md](docs/design.md) for a shorter design overview.

## Main Results

The following tables summarize the May 2026 validation evidence. These are engineering and statistical-screening results, not security proofs.

The default stream path remains the released baseline. The repository also
includes opt-in experimental stream variants for external statistical testing:
`fast8x`, `fast8x384mix`, `fast8x512mix`, `fast8x768mix`, and
`fast8x1024mix`. They are domain-separated from the baseline and must be
requested explicitly with `--variant`. The ablation evidence and current
ranking are summarized in [tests/ablation_lab/](tests/ablation_lab/).

### Statistical Batteries

| Evaluation | Result | Notes |
|---|---:|---|
| SmokeRand express | PASS, 7/7 | 83,971,072 bytes processed; all seven express tests reported `Ok`. |
| NIST STS standard check | PASS | 10 sequences x 1,000,000 bits; 188 parsed rows, 0 starred rows, 0 failed-proportion rows. |
| TestU01 SmallCrush | PASS, 15/15 | TestU01 1.2.3 reported all SmallCrush tests passed. |
| TestU01 Crush | PASS, 144/144 | Full Crush completed in about 26 min CPU time and reported all tests passed. |
| Dieharder battery | 109 PASS / 2 WEAK / 0 FAIL | Two weak p-values occurred in STS serial rows; no failures. Weak rows are expected occasionally and require reruns, not triumphal interpretation. |
| PractRand core to 512 MiB | WARN / no escalation | One early 16 KiB unusual result; no anomalies from 32 KiB through 512 MiB. |
| PractRand expanded to 1 GiB | WARN | Final 1 GiB level reported no anomalies in 2050 results, but earlier low-bit NS3 warnings require follow-up. |

### Structural Probes

| Probe | Result | Notes |
|---|---:|---|
| Truncated birthday collision checks | PASS | 16/24/32/48/64-bit prefix collision counts were close to birthday expectation under practical sample sizes. |
| Full-digest collision smoke | PASS | 0 full digest collisions and 0 prefix64 collisions over 20,000 sampled messages. |
| Message-bit diffusion | PASS | 16-round mean changed bits: 127.819 of 256 over 8,192 samples. |
| Black-box differential diffusion probe | PASS | Across tested deltas and rounds, mean changed bits stayed near 128; no repeated output differences were observed. |
| Black-box rotational relation probe | PASS | No exact rotational relation was observed; mean rotational distances stayed near 128 bits. |
| Domain/tweak separation | PASS | 5/5 unique digests; minimum hamming distance from default case was 121 bits. |
| Black-box state-recovery/predictability screen | PASS | Next-byte prediction accuracy 0.00396061, near the random baseline of 1/256. |
| Overlap/fork stream uniqueness screen | PASS | 0 repeated 32-byte block overlaps across 4 streams and 262,144 tested blocks. |

These probes are development gates. They do not search differential trails, bound differential probabilities, prove resistance to rotational distinguishers, perform SAT/MILP or Gröbner-basis analysis, or prove state-recovery resistance. See [docs/testing.md](docs/testing.md) for the exact meaning of each probe.

### Throughput

Stream throughput is usable for external batteries; hash throughput is still the main engineering weakness. Values below are from May 2026 runs on an Apple M4 Pro Mac mini unless noted.

| Implementation / mode | Throughput |
|---|---:|
| Experimental C `fast8x1024mix` stream variant | ~375.7 MiB/s |
| Experimental C `fast8x768mix` stream variant | ~316.2 MiB/s, but PractRand low-bit watch |
| Experimental C `fast8x512mix` stream variant | ~238.3 MiB/s |
| Experimental C `fast8x` stream variant | ~150.0 MiB/s in latest local run; ~132.7 MiB/s in earlier ablation run |
| Released C baseline stream in the latest local run | ~80.0 MiB/s |
| `tricube_tc256_xof_fast` stream candidate | ~80.2 MiB/s |
| `tricube_geo256_chain_fast` stream candidate | ~62.3 MiB/s |
| `tricube_tetra_block256_chain_fast` stream candidate | ~57.3 MiB/s |
| Current standalone C TriCube stream | ~51.5 MiB/s in refresh run; ~53.1 MiB/s in package smoke run |
| `sha256_counter_chain` Python harness control | ~51.3 MiB/s |
| Current standalone C TriCube hash, 1024-byte messages, 16 rounds | ~18.2 MiB/s in latest local C API run; earlier refresh measured ~14.7 MiB/s |
| Experimental C `hashfast1024` hash, 16 MiB messages | ~273.2 MiB/s; digest-concatenation PractRand WARN |
| Experimental C `hashfast1024r6` hash, 16 MiB messages | ~343.0 MiB/s; stronger digest-concatenation low-bit warning |

These numbers are not a claim of competitiveness with optimized SHA-2, SHA-3, BLAKE2, or BLAKE3 libraries. The faster rows are opt-in experimental candidates only; the default baseline remains separate.

### Interpretation

TriCube now has a concrete geometric state model, a C implementation, a Python interface, fixed vectors, battery results, structural probes, and reproducible commands. The strongest positive evidence is the TestU01 Crush pass, the Dieharder result with no failures, the absence of obvious structural failures in the current probes, and the fact that the C stream path is fast enough for longer batteries.

The strongest negative evidence is also clear: PractRand flagged low-bit behavior, cryptanalysis is incomplete, and hash throughput is not yet competitive. The responsible conclusion is that TriCube deserves further review and hardening, not security use.

The full public evidence summary is [results/consolidated-results-2026-05-19.md](results/consolidated-results-2026-05-19.md).

## Reproducing Results

Quick checks:

```bash
make -C c test
python -m pip install -e ".[test]"
pytest -q
python benchmarks/bench_stream.py --bytes 1048576
python tests/crypto_analysis/hash_mode/run_hash_screens.py --profile quick --implementations baseline_hash,hashfast1024,hashfast1024r6 --out /tmp/tricube-hash-quick
```

External batteries are run from the C stream path:

```bash
make -C c all
tools/run_practrand.sh 1073741824
tools/run_dieharder.sh 1073741824
tools/run_testu01.sh smallcrush 1073741824
python benchmarks/bench_stream.py --bytes 268435456 --variants baseline,fast8x,fast8x512mix,fast8x768mix,fast8x1024mix --skip-python
```

See [tools/run_stat_batteries.md](tools/run_stat_batteries.md), [docs/testing.md](docs/testing.md), and [docs/reproducibility.md](docs/reproducibility.md) before interpreting results.

## Third-Party Tools

TriCube does not bundle SmokeRand, PractRand, Dieharder, TestU01, NIST STS, or
third-party hash implementations. The scripts in `tools/` assume those
programs are installed separately and used under their own upstream licenses.
See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for the public notice table.

## Analysis Tooling

TriCube uses standard external statistical batteries where possible, and the
next layer of formal analysis should use established solver and algebra systems
rather than custom ad hoc replacements. Z3, SageMath, CryptoMiniSat,
CLAASP/CryptoSMT-style frameworks, and related tooling are useful only after a
verified TriCube reduced-round model exists. The custom work is the TriCube
model; the search and solving machinery should come from well-understood tools.

The tool plan and optional setup checks are in [docs/tooling.md](docs/tooling.md).
The current probe definitions and limits are in [docs/testing.md](docs/testing.md).

## Security Limitations

TriCube is research-only. It still lacks independent cryptanalysis, formal reduced-round analysis, side-channel review, and complete long-run multi-seed battery campaigns. Statistical batteries and development probes are useful evidence, but they are not a security proof. See [docs/security-status.md](docs/security-status.md) and [docs/limitations.md](docs/limitations.md) for the full boundary.

## Paper and Citation

The source manuscript is [paper/manuscript.md](paper/manuscript.md). It explains where TriCube came from, the current construction, the available evidence, and the analysis still required before stronger claims would be responsible. Generated PDF and DOCX exports should be attached to releases rather than tracked as source files.

If you use this repository in research, cite [CITATION.cff](CITATION.cff).

## Funding, Conflicts, and Assistance

This work received no external funding. The author reports no external financial conflict of interest related to this repository.

AI assistance was used to help organize code, documentation, tests, and manuscript material. The design, claims, limitations, and interpretation remain the responsibility of the author.

## License

TriCube is released under the MIT License. See [LICENSE](LICENSE).
