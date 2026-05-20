# Reproducibility

This repository is organized so a reviewer can rebuild the C implementation, install the Python package, run tests, regenerate vectors, and rerun the public benchmark scripts without relying on private machine paths.

## Environment

Recommended baseline:

- C compiler with C11 support;
- Python 3.11 or 3.12;
- `make`;
- `pytest` for Python tests.

Optional external tools:

- PractRand;
- Dieharder;
- TestU01 wrappers;
- NIST STS;
- SmokeRand.

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
python benchmarks/bench_throughput.py --quick
python benchmarks/bench_stream.py --bytes 1048576
```

## External Batteries

External batteries are not bundled. The scripts in `tools/` assume a locally built `c/build/tricube` and available external tools on `PATH`.

```bash
tools/run_practrand.sh 1073741824
tools/run_dieharder.sh 1073741824
tools/run_testu01.sh smallcrush 1073741824
```

Each run should save command output, seed, byte count, tool version where available, and final interpretation.
