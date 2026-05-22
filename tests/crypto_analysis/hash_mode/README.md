# TriCube Hash-Mode Screens

This folder contains development screens for the public TriCube hash path. The
stream screens in `tests/crypto_analysis/screens/` evaluate deterministic
stream output. These scripts deliberately test something different: each sample
is a message, and the measured output is the 32-byte digest returned by the C
CLI command:

```bash
c/build/tricube hash --hex MESSAGE_HEX
```

The implementation list contains `baseline_hash`, `hashfast1024`, and
`hashfast1024r6`. The two `hashfast` entries are experimental candidates with
their own domain tags and fixed C vectors. They do not replace the default hash
or XOF path.

## Quick Run

```bash
python tests/crypto_analysis/hash_mode/run_hash_screens.py \
  --profile quick \
  --implementations baseline_hash,hashfast1024,hashfast1024r6 \
  --out tests/crypto_analysis/results/hash-quick-latest
```

The quick profile uses 64-byte deterministic messages generated from 64-bit
seeds. It runs differential diffusion, rotational relation, algebraic degree,
collision/birthday, near-collision, and low-bit digest diagnostics.

## Individual Screens

| Screen | Command |
|---|---|
| Differential diffusion | `python tests/crypto_analysis/hash_mode/differential_hash_screen.py --implementations baseline_hash,hashfast1024,hashfast1024r6 --samples 64 --out tests/crypto_analysis/results/hash-differential-latest` |
| Rotational relation | `python tests/crypto_analysis/hash_mode/rotational_hash_screen.py --implementations baseline_hash,hashfast1024,hashfast1024r6 --samples 64 --out tests/crypto_analysis/results/hash-rotational-latest` |
| Algebraic degree | `python tests/crypto_analysis/hash_mode/algebraic_hash_screen.py --implementations baseline_hash,hashfast1024,hashfast1024r6 --variables 8 --output-bits 32 --out tests/crypto_analysis/results/hash-algebraic-latest` |
| Collision and birthday | `python tests/crypto_analysis/hash_mode/collision_hash_screen.py --implementations baseline_hash,hashfast1024,hashfast1024r6 --samples 512 --near-pairs 256 --out tests/crypto_analysis/results/hash-collision-latest` |
| Low-bit digest diagnostics | `python tests/crypto_analysis/hash_mode/low_bit_hash_screen.py --implementations baseline_hash,hashfast1024,hashfast1024r6 --samples 4096 --out tests/crypto_analysis/results/hash-low-bit-latest` |

## Digest Streams for External Batteries

Some external randomness batteries can be run on concatenated hash digests. That
is not the same as testing native XOF or stream output, so the input source must
be labeled clearly in reports. The C CLI can write repeated 32-byte digests of
deterministic messages:

```bash
c/build/tricube digest-stream \
  --variant hashfast1024 \
  --seed 123 \
  --messages 524288 \
  --message-bytes 64 \
  --out -
```

The Python `digest_stream.py` helper uses the same deterministic message
schedule and remains available for small reproducibility checks, but the C CLI
path is the practical input source for larger batteries.

The output can be piped into tools such as PractRand or TestU01 stdin adapters.
Passing such a battery is still a statistical screen, not a cryptographic
security result.

## What These Screens Exercise

The differential screen flips selected bits, bytes, word masks, and random
masks in deterministic messages and measures digest Hamming distance and
per-bit flip bias. The rotational screen rotates message words and checks for
obvious preserved output rotations. The algebraic screen varies a small set of
message bits, builds output-bit truth tables, and computes sampled black-box
ANF degree. The collision screen compares observed prefix collisions with the
birthday expectation and samples pairwise digest distances. The low-bit screen
concatenates digests and measures bit-position balance, low-nibble frequencies,
and lag-1 transition behavior.

These are development gates. They can find obvious defects or warning patterns,
but they do not replace formal differential, rotational, algebraic, collision,
or preimage cryptanalysis.
