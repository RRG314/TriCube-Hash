# TriCube Consolidated Results - 2026-05-19

TriCube remains experimental. These results support continued testing and external review; they do not establish cryptographic security.

## 2026-05-20 Fast8x Stream Update

The public C API now includes an explicit experimental stream variant,
`fast8x`, for continued statistical testing. It does not replace the released
baseline stream and must be requested by name.

In the ablation-lab run, `fast8x` measured `132.655 MiB/s` on a 256 MiB stream
benchmark, compared with `69.796 MiB/s` for the baseline in the same harness.
The ablation record lists `fast8x` as clean through PractRand 1 GiB, SmokeRand
express 7/7, and TestU01 SmallCrush 15/15. Faster candidates were not promoted
because they introduced low-bit PractRand warnings or failures.

See `experiments/ablation-lab/` for the compact public ablation record. This
update is performance and statistical-screening evidence only; it does not
establish cryptographic security.

## Environment

| Item | Value |
|---|---|
| Date | 2026-05-19 |
| Machine | Apple Mac mini, Apple M4 Pro, 12 cores, 48 GiB memory |
| Operating system | macOS 15.5 |
| C compiler | Apple clang 17.0.0 |
| Python used in original research runs | CPython 3.13.2 |
| Primary seed | 123 |

## Statistical Batteries

| Evaluation | Result | Data / runtime | Notes |
|---|---:|---:|---|
| SmokeRand express | PASS, 7/7 | 83,971,072 bytes; ~1 s | All express tests reported `Ok`; quality 4.00. |
| NIST STS standard check | PASS | 10 x 1,000,000-bit sequences; 33.3 s STS runtime | 188 parsed rows, 0 starred rows, 0 failed-proportion rows. |
| TestU01 SmallCrush | PASS, 15/15 | total CPU 8.75 s | TestU01 1.2.3 reported all tests passed. |
| TestU01 Crush | PASS, 144/144 | total CPU 26:22.53 | Full Crush completed and reported all tests passed. |
| Dieharder battery | 109 PASS / 2 WEAK / 0 FAIL | manual full transcript | Two weak rows appeared in STS serial tests. No failures were reported. |
| PractRand core to 512 MiB | WARN / no escalation | 512 MiB terminal level; 167 results | One early 16 KiB unusual result; no anomalies from 32 KiB through 512 MiB. |
| PractRand expanded to 1 GiB | WARN | 1 GiB terminal level; 2050 final-level results | Final level reported no anomalies; earlier low-bit NS3 warnings remain unresolved. |

## PractRand 1 GiB Detail

The 1 GiB expanded PractRand run reached `1 gigabyte (2^30 bytes)` and the final level reported:

```text
no anomalies in 2050 test result(s)
```

Earlier levels flagged low-bit behavior:

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

This is a WARN result. It should drive follow-up testing, not be treated as a clean pass.

## Structural Probes

| Probe | Result | Main metric |
|---|---:|---|
| Truncated birthday checks | PASS | 16-bit: 19,278 observed pairs vs 19,073 expected; 24-bit: 295 vs 298 expected; 32-bit: 2 vs 1.16 expected; 48/64-bit: 0 observed. |
| Full digest collision smoke | PASS | 0 full digest collisions and 0 prefix64 collisions over 20,000 sampled messages. |
| Diffusion, 12 rounds | PASS | Mean changed bits 128.027 of 256; stdev 7.981; min 99; max 156. |
| Diffusion, 16 rounds | PASS | Mean changed bits 127.819 of 256; stdev 7.950; min 95; max 152. |
| Differential probes | PASS | Tested deltas across 1, 2, 4, 8, 12, and 16 rounds; no repeated output differences observed. |
| Rotational probes | PASS | Tested rotations 1, 7, 8, 13, 16, and 32 across 1, 2, 4, 8, 12, and 16 rounds; mean rotational distances stayed near 128 bits. |
| Algebraic probe | PASS | Small black-box ANF probe reached max degree 10 for sampled 10-variable cases across tested rounds. |
| Domain/tweak separation | PASS | 5 unique digests; minimum hamming distance from default case was 121 bits. |
| Bit influence spread | PASS | Mean output flip rate 0.5009918; min 0.425781; max 0.570312. |
| State-recovery screen | PASS | Next-byte prediction accuracy 0.00396061; bit accuracy 0.500095; linear-complexity ratio 0.5. |
| Related-seed overlap/fork test | PASS | 0 repeated 32-byte block overlaps across 4 streams and 262,144 tested blocks. |

These probes are development gates. They can find obvious problems, but they do not replace cryptanalysis.

## Performance

### Stream Throughput

| Implementation / mode | Throughput | Notes |
|---|---:|---|
| Experimental C `fast8x` stream variant | 132.655 MiB/s | 256 MiB ablation-lab run; explicit opt-in variant. |
| Released C baseline stream in same ablation harness | 69.796 MiB/s | Same 256 MiB benchmark run as `fast8x`. |
| `tricube_tc256_xof_fast` | 80.158 MiB/s | Python harness candidate, 1 MiB stream sanity run. |
| `tricube_geo256_chain_fast` | 62.255 MiB/s | Python harness candidate, 1 MiB stream sanity run. |
| `tricube_tetra_block256_chain_fast` | 57.276 MiB/s | Python harness candidate, 1 MiB stream sanity run. |
| Current standalone C TriCube stream | 51.513 MiB/s | 1 MiB refresh run; package smoke measured 53.147 MiB/s. |
| `sha256_counter_chain` harness control | 51.307 MiB/s | Python harness control, not an optimized C SHA comparison. |

### Hash Throughput

| Message bytes | Rounds | MiB/s | Hashes/s |
|---:|---:|---:|---:|
| 32 | 12 | 3.652 | 119,678.8 |
| 64 | 12 | 7.202 | 118,004.7 |
| 256 | 12 | 14.700 | 60,209.5 |
| 1024 | 12 | 19.267 | 19,729.9 |
| 32 | 16 | 2.772 | 90,833.8 |
| 64 | 16 | 5.543 | 90,817.3 |
| 256 | 16 | 11.060 | 45,303.5 |
| 1024 | 16 | 14.678 | 15,029.9 |

Hash throughput is the main engineering weakness. The current C implementation is usable for research but not competitive with mature optimized hashes.

## Current Interpretation

The strongest positive evidence is the TestU01 Crush pass, the Dieharder battery with no failures, the NIST STS pass, the absence of obvious failures in the structural probes, and enough C stream throughput to run longer external batteries.

The strongest negative evidence is the PractRand low-bit warning. That issue needs multi-seed, low-bit-focused, and longer-run follow-up. TriCube also still lacks independent cryptanalysis, reduced-round attacks, differential trail work, rotational analysis, algebraic analysis at larger scale, side-channel review, and competitive optimized implementations.

The correct public claim is narrow:

> TriCube is an experimental geometric hash/XOF candidate with a concrete C implementation, reproducible vectors, meaningful early statistical-battery evidence, and unresolved cryptanalytic questions.

The wrong public claim is:

> TriCube is cryptographically secure.

## Required Next Tests

- multi-seed PractRand at 10 GiB and higher;
- TestU01 Crush reruns and BigCrush completion;
- full NIST STS campaign with more sequences;
- SmokeRand full battery;
- low-bit-focused diagnosis of the stream path;
- reduced-round attack search;
- differential and rotational cryptanalysis;
- algebraic and invariant analysis;
- birthday and near-collision sweeps at larger practical scales;
- optimized C throughput comparison against SHA-256, SHA3/SHAKE, BLAKE2, and BLAKE3 libraries.
