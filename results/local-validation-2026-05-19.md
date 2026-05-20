# Local Validation - 2026-05-19

This file records the local validation run used while preparing the first public TriCube repository.

## Commands

```bash
make -C c clean test
python -m venv .venv-test
. .venv-test/bin/activate
python -m pip install -e ".[test]"
pytest -q
c/build/tricube hash --hex 616263
c/build/tricube xof --hex 616263 --bytes 64
c/build/tricube stream --seed 123 --bytes 64 --out /tmp/tricube_stream.bin
python -m tricube.cli hash --hex 616263
python -m tricube.cli xof --hex 616263 --bytes 64
python examples/xof_stream.py
python benchmarks/bench_hash_sizes.py --quick
python benchmarks/bench_throughput.py --quick
python benchmarks/bench_stream.py --bytes 1048576
python -m build
python -m twine check dist/*
```

## Results

| Check | Result |
|---|---:|
| C build | PASS |
| C self-test | PASS |
| C vector test | PASS |
| C stream smoke test | PASS |
| Python package install | PASS |
| Python tests | PASS, 6 passed |
| C CLI hash smoke | PASS |
| C CLI XOF smoke | PASS |
| Python CLI hash smoke | PASS |
| Python CLI XOF smoke | PASS |
| Examples | PASS |
| Build source distribution | PASS |
| Build wheel | PASS |
| Twine metadata check | PASS |

## Smoke Benchmark Output

Hash-size benchmark, quick mode:

```text
algorithm,size_bytes,elapsed_s,mib_per_s
tricube,0,0.012727,0.000
sha256,0,0.000039,0.000
sha3_256,0,0.000009,0.000
tricube,3,0.012276,0.001
sha256,3,0.000013,0.652
sha3_256,3,0.000005,1.689
tricube,64,0.012344,0.015
sha256,64,0.000013,14.503
sha3_256,64,0.000005,38.892
tricube,1024,0.066157,0.044
sha256,1024,0.000013,217.675
sha3_256,1024,0.000008,372.025
tricube,65536,3.372399,0.056
sha256,65536,0.000099,1894.744
sha3_256,65536,0.000228,822.819
```

Stream benchmark:

```text
tricube_c_stream,1048576,0.018816,53.147 MiB/s
tricube_python_stream,1048576,4.628282,0.216 MiB/s
```

These are smoke measurements, not final performance claims. The Python reference is intentionally slow. The C stream path is the relevant implementation for external statistical batteries.

## Notes

The XOF API was corrected during validation so longer XOF requests are prefix-consistent. The fixed 32-byte hash vectors remained unchanged.

DOCX rendering through the document QA tool could not be completed because LibreOffice `soffice` is not installed in this environment. Text extraction from the DOCX succeeded, and a PDF manuscript was generated separately.

