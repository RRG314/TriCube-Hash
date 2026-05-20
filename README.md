# TriCube

TriCube is an experimental hash, extendable-output function (XOF), and deterministic stream generator built around a geometric state update. The current implementation represents the internal state as a small cube-connected vertex grid, decomposes the cube cells into tetrahedra, applies local tetrahedral mixing, couples neighboring vertices, and squeezes bytes from the evolved state.

The project is meant for cryptographic engineering research. It is not a secure hash standard, not production ready, and not a replacement for SHA-2, SHA-3/SHAKE, BLAKE2, or BLAKE3. Current evidence is enough to justify continued testing and outside review, but it does not establish collision resistance, preimage resistance, pseudorandomness, or security for any real application.

## What This Repository Contains

This repository contains a standalone C11 implementation, a Python reference package, fixed test vectors, CLI tools, reproducibility notes, benchmark scripts, and a cleaned result summary from the May 2026 validation pass.

The C implementation is the primary implementation path. Python exposes a small API for scripting and tests, and keeps a pure Python reference path so the package remains inspectable without native build steps.

## Security Status

TriCube is experimental. Do not use it for passwords, signatures, message authentication, key derivation, blockchain consensus, production random streams, encrypted storage, or any security-critical system.

The current evidence consists of deterministic test vectors, C/Python agreement tests, unit tests, internal statistical sanity checks, selected Dieharder/TestU01/PractRand artifacts, throughput checks, and structural probes from the research archive. Statistical batteries can find defects, but passing them does not prove cryptographic security. No independent cryptanalysis has been completed.

## Build the C Implementation

```bash
git clone https://github.com/RRG314/tricube-hash.git
cd tricube-hash
make -C c test
```

This builds the CLI at `c/build/tricube` and runs the C self-test plus vector and stream tests.

The C CLI supports:

```bash
c/build/tricube self-test
c/build/tricube vectors
c/build/tricube hash --hex 616263
c/build/tricube hash path/to/file.bin
c/build/tricube xof --hex 616263 --bytes 64
c/build/tricube stream --seed 123 --bytes 1048576 --out stream.bin
```

The library header is `c/include/tricube.h`. It exposes fixed 256-bit digest mode, XOF mode, context-style update/finalize/squeeze functions, deterministic stream generation, and a self-test.

## Install the Python Package

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[test]"
pytest -q
```

The package import name is `tricube`:

```python
import tricube

digest = tricube.hash(b"abc")
print(tricube.hexdigest(b"abc"))

out = tricube.xof(b"abc", 64)
stream = tricube.stream(seed=123, n=1024)
```

The Python CLI is available as:

```bash
tricube-py hash --hex 616263
tricube-py xof --hex 616263 --bytes 64
tricube-py stream --seed 123 --bytes 1024 --out stream.bin
```

## Design Summary

TriCube uses a 2048-bit state arranged as 32 64-bit lanes. Twenty-seven lanes correspond to a 3 x 3 x 3 vertex grid; the remaining lanes act as shell/global lanes. The eight cube cells of the 2 x 2 x 2 block are each decomposed into six tetrahedra. A round applies orientation-dependent tetrahedral ARX mixing, edge coupling over adjacent vertices, shell coupling, and a global lane permutation.

Input bytes are absorbed into the state with domain separation and length encoding. Digest mode squeezes 32 bytes. XOF mode squeezes an arbitrary number of bytes. Stream mode initializes from a seed and emits deterministic blocks for testing external statistical batteries.

The candidate novelty is the cube/tetrahedral state evolution and propagation schedule. It is not the use of hashing, XOFs, ARX operations, or sponge-like absorb/squeeze structure, all of which are established design families.

See [docs/design.md](docs/design.md) for details.

## Current Results

The May 2026 validation pass should be read as a research snapshot, not a security certificate.

| Area | Current result | Interpretation |
|---|---|---|
| C self-test and fixed vectors | pass | Implementation is deterministic for saved vectors. |
| C/Python vector agreement | pass in local tests | Python reference and C path agree on public vectors. |
| Internal 1 MiB statistical sanity checks | pass for the current C stream path | Basic byte/bit metrics did not show obvious failure. |
| Dieharder saved artifact | pass in saved run, but artifact covered a limited report set | Useful but incomplete. |
| TestU01 SmallCrush saved artifact | pass in saved run | Useful sanity evidence, not BigCrush-level evidence. |
| PractRand 1 GiB expanded run | warn | Final level reported no anomalies, but earlier low-bit warnings must be investigated. |
| Throughput | about 44 MiB/s in the saved C stream check | Not yet competitive with mature optimized hashes. |

The cleaned result report is [results/consolidated-results-2026-05-19.md](results/consolidated-results-2026-05-19.md). The PractRand 1 GiB summary and log are in [results/raw/](results/raw/).

## Benchmarks

Quick local benchmarks:

```bash
python benchmarks/bench_throughput.py --quick
python benchmarks/bench_hash_sizes.py --quick
python benchmarks/bench_stream.py --bytes 1048576
```

The benchmark scripts compare TriCube against Python `hashlib` SHA-256 and SHA3-256 where practical. Those comparisons are performance references only. Mature hashes have extensive analysis and optimized implementations; TriCube does not.

## Reproducing External Batteries

External batteries are intentionally kept as commands rather than bundled logs:

```bash
make -C c all
tools/run_practrand.sh 1073741824
tools/run_dieharder.sh 1073741824
tools/run_testu01.sh smallcrush 1073741824
```

See [tools/run_stat_batteries.md](tools/run_stat_batteries.md) and [docs/testing.md](docs/testing.md) before interpreting results.

## Limitations

The important limitations are direct:

- no security proof;
- no independent review;
- no collision-resistance or preimage-resistance claim;
- incomplete reduced-round, differential, rotational, algebraic, and state-recovery analysis;
- low-bit PractRand warnings in the saved 1 GiB run;
- performance is not competitive with mature optimized hashes;
- statistical batteries do not prove cryptographic security.

See [docs/limitations.md](docs/limitations.md) for the full limitation list.

## Paper and Citation

The current manuscript draft is in [paper/](paper/). The draft explains where TriCube came from, its construction, current evidence, and the open security work required before stronger claims would be responsible.

If you use this repository in research, cite [CITATION.cff](CITATION.cff).

## Funding and Conflicts

This work received no external funding. The author reports no external financial conflict of interest related to this repository.

AI assistance was used to help organize code, documentation, tests, and manuscript material. The design, claims, limitations, and interpretation remain the responsibility of the author.

## License

TriCube is released under the MIT License. See [LICENSE](LICENSE).

