# TriCube

TriCube is an experimental geometric hash and extendable-output function (XOF)
research package. It exposes a small Python API for hashing, hex digests, XOF
output, and deterministic test streams.

TriCube is not a production cryptography library. It has not received
independent cryptanalysis and must not be used for passwords, signatures,
message authentication, key derivation, encryption, blockchain consensus,
production random streams, or any security-critical application.

The full project repository is:

https://github.com/RRG314/tricube-hash

The current manuscript draft is kept with the repository:

https://github.com/RRG314/tricube-hash/tree/main/paper

## Install

```bash
python -m pip install tricube
```

For local development from the repository:

```bash
python -m pip install -e ".[test]"
python -m pytest -q
```

## Python API

```python
import tricube

digest = tricube.hash(b"abc")
hex_digest = tricube.hexdigest(b"abc")
out = tricube.xof(b"abc", 64)
stream = tricube.stream(seed=123, n=1024)

print(hex_digest)
print(tricube.security_notice())
```

The main public functions are:

- `tricube.hash(data, domain=None) -> bytes`
- `tricube.hexdigest(data, domain=None) -> str`
- `tricube.xof(data, n, domain=None) -> bytes`
- `tricube.stream(seed, n, domain=None) -> bytes`
- `tricube.self_test() -> bool`
- `tricube.version() -> str`
- `tricube.security_notice() -> str`

## Command Line

```bash
python -m tricube hash --hex 616263
python -m tricube xof --hex 616263 --bytes 64
python -m tricube stream --seed 123 --bytes 1024 --out stream.bin
python -m tricube self-test
python -m tricube vectors
python -m tricube security-notice
```

After installation, the same interface is available through the `tricube`
console command:

```bash
tricube self-test
tricube hash --hex 616263
```

## Current Status

This package contains the clean Python reference implementation and fixed test
vectors. The public GitHub repository also contains the standalone C
implementation, benchmarks, external-battery scripts, documentation, and the
manuscript draft.

The current evidence supports continued research and external review. It does
not establish collision resistance, preimage resistance, pseudorandomness, or
security for real applications.

## License

TriCube is released under the MIT License.
