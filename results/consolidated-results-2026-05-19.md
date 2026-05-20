# TriCube Consolidated Results - 2026-05-19

This is the cleaned public summary of the May 2026 TriCube validation pass. The original run artifacts were produced during local research development; this file removes private paths and keeps only the interpretable evidence.

TriCube remains experimental. These results support continued testing and review, not security-critical use.

## Environment Snapshot

| Item | Value |
|---|---|
| Date | 2026-05-19 |
| Machine | Apple Mac mini, Apple M4 Pro, 12 cores, 48 GiB memory |
| Operating system | macOS 15.5 |
| C compiler | Apple clang 17.0.0 |
| Python | CPython 3.13.2 in the original local run |
| Primary C path | standalone TriCube C stream/hash implementation |
| Primary seed for stream batteries | 123 |

## Implementation Checks

| Check | Result | Notes |
|---|---:|---|
| C self-test | PASS | Fixed 256-bit digest vectors matched expected values. |
| C stream smoke test | PASS | Same seed reproduced output; different seed changed output. |
| Python reference vectors | PASS | Python reference matched saved digest vectors. |
| C/Python agreement | PASS | C CLI and Python reference agreed on public vectors. |

## Internal Statistical Sanity Checks

The internal benchmark used 1 MiB streams for quick triage. It measured byte entropy, bit balance, serial correlation, byte chi-square behavior, avalanche response, repetition smoke checks, and throughput.

| Generator | Status | Bytes | Throughput MiB/s | Byte entropy | Bit ones fraction | Lag-1 correlation | Avalanche mean | Repeated 32-byte blocks |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Python reference stream | PASS | 1,048,576 | 0.227 | 7.999798 | 0.499887 | -0.001290 | 0.501221 | 0 |
| C stream | PASS | 1,048,576 | 44.300 | 7.999798 | 0.499887 | -0.001290 | 0.501221 | 0 |

Interpretation: the C stream path was much faster than the Python reference and did not show an obvious failure in the internal 1 MiB checks. These checks are sanity gates only.

## External Battery Artifacts

| Tool | Result | Bytes | Runtime | Interpretation |
|---|---:|---:|---:|---|
| Dieharder saved artifact | PASS | 4,294,967,296 | 75.092 s | Useful saved evidence, but the artifact contains only 13 reported assessment lines and should not be treated as a complete Dieharder campaign. |
| TestU01 SmallCrush saved artifact | PASS | 4,294,967,296 | 15.620 s | Useful sanity evidence; Crush and BigCrush remain required before stronger claims. |
| PractRand expanded saved artifact | WARN | 134,217,728 | 3.096 s | Low-bit anomalies appeared in shorter runs. |
| PractRand 1 GiB expanded run | WARN | 1,073,741,824 | 152 s | Final 1 GiB level reported no anomalies, but earlier low-bit suspicious/unusual results remain unresolved. |

## PractRand 1 GiB Detail

The 1 GiB PractRand run used the C stream path with expanded tests and extra folding. It reached `1 gigabyte (2^30 bytes)` and the final level reported:

```text
no anomalies in 2050 test result(s)
```

Earlier levels flagged low-bit issues:

```text
length= 1 megabyte (2^20 bytes)
  [Low1/64]NS3[2:hw:both]           suspicious
  [Low1/64]NS3[2:hw:all-]           unusual
  [Low4/32]NS3[4:hw:both]           mildly suspicious
  [Low4/32]NS3[4:hw:all-]           unusual

length= 2 megabytes (2^21 bytes)
  [Low1/64]NS3[2:hw:both]           unusual

length= 512 megabytes (2^29 bytes)
  [Low1/32]NS3[1:pd:both]           unusual
```

This is classified as WARN. It must not be described as a clean pass or as evidence of cryptographic security.

## Current Interpretation

The strongest engineering result is that the C implementation is deterministic, reasonably fast for an early research implementation, and reproducible against fixed vectors. The most important open issue is the low-bit PractRand behavior. That issue should be investigated before presenting TriCube as more than an experimental candidate.

## Required Next Tests

- multi-seed PractRand runs at 10 GiB and higher;
- full Dieharder with explicit per-test output;
- TestU01 Crush and BigCrush;
- NIST STS with documented bitstream formatting;
- SmokeRand full battery;
- reduced-round and differential analysis;
- rotational and algebraic probes;
- birthday collision sweeps at larger scales;
- C throughput comparison against optimized SHA-256, SHA3/SHAKE, BLAKE2, and BLAKE3 implementations.

