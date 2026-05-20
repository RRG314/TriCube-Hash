# Testing

TriCube uses several layers of testing. Each layer answers a different question.

Unit tests verify deterministic behavior, output lengths, vector agreement, CLI behavior, and basic stream separation. They do not evaluate security.

Internal statistical checks measure byte entropy, bit balance, serial correlation, chi-square behavior, block entropy, avalanche response, throughput, and simple repetition/cycle smoke checks. These are useful for finding obvious flaws.

External batteries such as PractRand, Dieharder, TestU01, SmokeRand, and NIST STS are stronger statistical screens. They can identify suspicious output structure, but they still do not prove cryptographic security.

Cryptanalytic analysis is a separate requirement. TriCube still needs reduced-round, differential, rotational, algebraic, collision-search, fork/overlap, and state-recovery studies.

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
```

## Interpreting Failures

A unit-test failure is an implementation failure. A statistical battery failure may indicate a structural weakness, a stream-format problem, a test-harness problem, or a reduced-quality region that needs diagnosis. A timeout is not a randomness failure; it is a performance or harness blocker.

Passing statistical batteries should be recorded as evidence of no detected failure under those conditions, not as a security claim.

