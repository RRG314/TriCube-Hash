# Reproducibility

This repository is organized so a reviewer can rebuild the C implementation, install the Python package, run tests, regenerate vectors, and rerun the public benchmark scripts without relying on machine-specific paths.

## Environment

Recommended baseline:

- C compiler with C11 support;
- Python 3.11 or 3.12;
- `make`;
- `pytest` for Python tests.

Optional external tools:

- Z3;
- SageMath;
- CryptoMiniSat;
- PractRand;
- Dieharder;
- TestU01 wrappers;
- NIST STS;
- SmokeRand.

These tools are not bundled in the TriCube repository or PyPI package. Install
them separately and follow their upstream licenses. See
[THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md) for the public notice table.

## Rebuild

```bash
make -C c clean
make -C c test
```

## Python Install and Tests

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[test]"
pytest -q
```

## Regenerate Vectors

```bash
make -C c all
python tools/generate_vectors.py > tests/vectors/tricube_vectors.json
```

The C and Python implementations should agree on the fixed vectors.

## Benchmark Smoke Runs

```bash
python benchmarks/bench_hash_sizes.py --quick
make -C c build/bench_hash_variants
c/build/bench_hash_variants --quick
python benchmarks/bench_throughput.py --quick
python benchmarks/bench_stream.py --bytes 1048576 --variants baseline,fast8x,fast8x1024mix
python benchmarks/bench_stream.py --bytes 268435456 --variants baseline,fast8x,fast8x512mix,fast8x768mix,fast8x1024mix --skip-python
```

The C `bench_hash_variants` target measures the baseline hash path and the
experimental `hashfast1024` and `hashfast1024r6` candidates through the C API,
without Python or CLI startup overhead. The current local result is about
273.188 MiB/s for `hashfast1024` and 343.013 MiB/s for `hashfast1024r6` on
16 MiB messages, compared with about 20.178 MiB/s for the baseline. These are
long-message engineering results, not security evidence.

The `fast8x` and `fast8x*mix` stream variants are experimental optimized paths.
They are not the default and do not replace the baseline stream. The ablation
record explaining why they were added is in
[tests/ablation_lab/](../tests/ablation_lab/). The latest local snapshot
reports `fast8x1024mix` at 375.694 MiB/s on a 256 MiB stream run, compared
with 79.971 MiB/s for the released baseline in the same harness. That is a
same-machine comparison against the TriCube baseline, not a claim that the
variant has been competitively benchmarked against optimized SHA-2, SHA-3,
BLAKE2, or BLAKE3 implementations.

## Development Screens

The compact development screens are reproducible without storing large raw
streams:

```bash
python tests/crypto_analysis/run_all_screens.py \
  --profile quick \
  --variants baseline,fast8x,fast8x1024mix \
  --out tests/crypto_analysis/results/quick-latest

python tests/crypto_analysis/screens/low_bit_diagnostics.py \
  --variants baseline,fast8x,fast8x1024mix \
  --bytes 16777216 \
  --out tests/crypto_analysis/results/low-bit-latest

python tests/crypto_analysis/screens/whitebox_round_model.py \
  --rounds 24 \
  --out tests/crypto_analysis/results/whitebox-latest

python tests/crypto_analysis/hash_mode/run_hash_screens.py \
  --profile quick \
  --implementations baseline_hash,hashfast1024,hashfast1024r6 \
  --out tests/crypto_analysis/results/hash-quick-latest
```

These screens write compact JSON, Markdown, and CSV summaries. They do not
replace external batteries or formal cryptanalysis.

## Optional Analysis Tooling

Check local solver and battery availability:

```bash
python tests/crypto_analysis/tooling/check_tools.py
python tests/crypto_analysis/tooling/z3_smoke.py
sage -python tests/crypto_analysis/tooling/sage_smoke.py
```

Missing optional tools are reported as `NOT_INSTALLED`. They are not repository
test failures. See [docs/tooling.md](tooling.md) for the tool plan and the
custom TriCube model work required before solver results should be interpreted.

## External Batteries

External batteries are not bundled. The scripts in `tools/` assume a locally built `c/build/tricube` and available external tools on `PATH`.

```bash
tools/run_practrand.sh 1073741824
tools/run_dieharder.sh 1073741824
tools/run_testu01.sh smallcrush 1073741824
```

Each run should save command output, seed, byte count, tool version where available, and final interpretation.
