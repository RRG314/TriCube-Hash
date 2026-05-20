# TriCube

TriCube is an experimental hash, extendable-output function (XOF), and deterministic stream generator based on tetrahedral/cube-connected state evolution. The current implementation uses a 2048-bit state arranged as a cube-vertex grid plus shell lanes; each round mixes local tetrahedral groups, propagates across cube edges, couples shell lanes, and squeezes output from the evolved state.

TriCube is a cryptographic engineering research project, not a secure primitive. It is not production ready, not a replacement for SHA-2, SHA-3/SHAKE, BLAKE2, or BLAKE3, and should not be used for security-critical applications. The current evidence supports continued development and external review. It does not establish collision resistance, preimage resistance, pseudorandomness, or real-world security.

## Current Status

The repository contains a standalone C11 implementation, a Python reference package, fixed test vectors, CLI tools, benchmarks, reproducibility notes, external-battery run scripts, a cleaned result summary, and a manuscript draft.

The strongest current result is that TriCube now has a concrete geometric construction with reproducible C/Python vectors and nontrivial statistical-battery evidence. The main open issues are low-bit PractRand warnings, incomplete cryptanalysis, and performance that is still below mature optimized hash implementations.

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
c/build/tricube hash path/to/file.bin
c/build/tricube xof --hex 616263 --bytes 64
c/build/tricube stream --seed 123 --bytes 1048576 --out stream.bin
c/build/tricube stream --seed 123 --bytes 1048576 --out stream.bin --variant fast8x
```

The public C header is [c/include/tricube.h](c/include/tricube.h). It exposes fixed 256-bit digest mode, XOF mode, context-style update/finalize/squeeze functions, deterministic stream generation, and self-test support.

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

The candidate novelty is the cube/tetrahedral state evolution and propagation schedule. It is not the use of hashing, XOFs, ARX operations, or sponge-like absorb/squeeze structure, all of which are established design families.

See [docs/design.md](docs/design.md) for the construction details.

## Main Results

The following tables summarize the May 2026 validation evidence. These are engineering and statistical-screening results, not security proofs.

The default stream path remains the released baseline. This branch also adds an
experimental `fast8x` stream variant for external statistical testing. It is
domain-separated from the baseline and must be requested explicitly with
`--variant fast8x`. The ablation evidence for that choice is summarized in
[experiments/ablation-lab/](experiments/ablation-lab/).

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
| Differential probes | PASS | Across tested deltas and rounds, mean changed bits stayed near 128; no repeated output differences were observed. |
| Rotational probes | PASS | No exact rotational relation was observed; mean rotational distances stayed near 128 bits. |
| Domain/tweak separation | PASS | 5/5 unique digests; minimum hamming distance from default case was 121 bits. |
| State-recovery screen | PASS | Next-byte prediction accuracy 0.00396061, near the random baseline of 1/256. |
| Overlap/fork stream test | PASS | 0 repeated 32-byte block overlaps across 4 streams and 262,144 tested blocks. |

### Throughput

Stream throughput is usable for external batteries; hash throughput is still the main engineering weakness. Values below are from local May 2026 runs on an Apple M4 Pro Mac mini unless noted.

| Implementation / mode | Throughput |
|---|---:|
| Experimental C `fast8x` stream variant | ~132.7 MiB/s |
| Released C baseline stream in the same ablation harness | ~69.8 MiB/s |
| `tricube_tc256_xof_fast` stream candidate | ~80.2 MiB/s |
| `tricube_geo256_chain_fast` stream candidate | ~62.3 MiB/s |
| `tricube_tetra_block256_chain_fast` stream candidate | ~57.3 MiB/s |
| Current standalone C TriCube stream | ~51.5 MiB/s in refresh run; ~53.1 MiB/s in local package smoke run |
| `sha256_counter_chain` Python harness control | ~51.3 MiB/s |
| Current standalone C TriCube hash, 1024-byte messages, 16 rounds | ~14.7 MiB/s |

These numbers are not a claim of competitiveness with optimized SHA-2, SHA-3, BLAKE2, or BLAKE3 libraries. They identify where the current prototype is usable and where it needs engineering work.

### Interpretation

TriCube has moved past a sketch: it has a concrete geometric state model, a C implementation, a Python interface, fixed vectors, battery results, structural probes, and reproducible commands. The strongest positive evidence is the TestU01 Crush pass, the Dieharder result with no failures, the absence of obvious structural failures in the current probes, and the fact that the C stream path is fast enough for longer batteries.

The strongest negative evidence is also clear: PractRand flagged low-bit behavior, cryptanalysis is incomplete, and hash throughput is not yet competitive. The responsible conclusion is that TriCube deserves further review and hardening, not security use.

The full public evidence summary is [results/consolidated-results-2026-05-19.md](results/consolidated-results-2026-05-19.md).

## Reproducing Results

Quick local checks:

```bash
make -C c test
python -m pip install -e ".[test]"
pytest -q
python benchmarks/bench_stream.py --bytes 1048576
```

External batteries are run from the C stream path:

```bash
make -C c all
tools/run_practrand.sh 1073741824
tools/run_dieharder.sh 1073741824
tools/run_testu01.sh smallcrush 1073741824
python benchmarks/bench_stream.py --bytes 268435456 --variants baseline,fast8x --skip-python
```

See [tools/run_stat_batteries.md](tools/run_stat_batteries.md), [docs/testing.md](docs/testing.md), and [docs/reproducibility.md](docs/reproducibility.md) before interpreting results.

## Third-Party Tools

TriCube does not bundle SmokeRand, PractRand, Dieharder, TestU01, NIST STS, or
third-party hash implementations. The scripts in `tools/` assume those
programs are installed separately and used under their own upstream licenses.
See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for the public notice table.

## Security Limitations

TriCube is not secure for production use. The limitations are direct:

- no security proof;
- no independent cryptanalysis;
- no collision-resistance or preimage-resistance claim;
- incomplete reduced-round, differential, rotational, algebraic, and state-recovery analysis;
- unresolved low-bit PractRand warnings;
- no side-channel or constant-time review;
- performance is not competitive with mature optimized hashes;
- statistical batteries do not prove cryptographic security.

See [docs/security-status.md](docs/security-status.md) and [docs/limitations.md](docs/limitations.md) for the full security boundary.

## Paper and Citation

The manuscript draft is in [paper/](paper/). It explains where TriCube came from, the current construction, the available evidence, and the analysis still required before stronger claims would be responsible.

If you use this repository in research, cite [CITATION.cff](CITATION.cff).

## Funding, Conflicts, and Assistance

This work received no external funding. The author reports no external financial conflict of interest related to this repository.

AI assistance was used to help organize code, documentation, tests, and manuscript material. The design, claims, limitations, and interpretation remain the responsibility of the author.

## License

TriCube is released under the MIT License. See [LICENSE](LICENSE).
