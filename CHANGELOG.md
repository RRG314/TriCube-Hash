# Changelog

## Unreleased

Updates preparing the experimental `fast8x` stream path for review.

- Added feedback-mixed stream candidates `fast8x384mix`, `fast8x512mix`,
  `fast8x768mix`, and `fast8x1024mix` as opt-in C stream variants.
- Added fixed seed-123 first-64-byte C test coverage for the new feedback-mixed
  stream candidates.
- Updated the specification, ablation record, result summary, and
  reproducibility docs with the new variant parameters, domain tags,
  throughput numbers, and current battery status.
- Recorded `fast8x1024mix` as the current best local stream candidate:
  375.694 MiB/s on a 256 MiB stream run, SmokeRand express 7/7, PractRand
  1 GiB with no anomalies, and TestU01 SmallCrush 15/15 in the latest local
  pass.
- Recorded `fast8x768mix` as a warning case: it crossed 300 MiB/s but showed
  PractRand Low4/64 unusual rows and should not be promoted without a fix.
- Added the opt-in `fast8x` C stream variant and documented its separate
  domain, round profile, output rate, and benchmark status.
- Added a fixed `fast8x` seed-123 stream vector and C test coverage for that
  vector.
- Added the reproducible crypto-analysis screen suite under `tests/`, with
  separate screen modules and an all-in-one quick runner.
- Added a separate hash-mode screen suite so digest-path tests are not inferred
  from stream-output screens.
- Added CI coverage for C tests, Python tests, and the quick crypto-analysis
  screen profiles on non-Windows runners.
- Clarified that `fast8x` has been compared against the released TriCube
  stream baseline in the same C ablation harness, while optimized SHA-2,
  SHA-3/SHAKE, BLAKE2, and BLAKE3 library comparisons remain future work.
- Kept `paper/manuscript.md` as the source manuscript and added a short
  manuscript DOCX under `paper/`.

## 0.1.0 - 2026-05-19

Initial public repository preparation for TriCube.

- Added standalone C11 implementation, public header, CLI, Makefile, and CMake build.
- Added Python package with hash, XOF, and deterministic stream APIs.
- Added fixed test vectors shared by the C and Python paths.
- Added documentation for design, testing, limitations, comparison, and reproducibility.
- Added cleaned result summary from the May 2026 validation pass.
