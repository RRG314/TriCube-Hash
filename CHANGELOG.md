# Changelog

## Unreleased

Branch updates preparing the experimental `fast8x` stream path for review.

- Added the opt-in `fast8x` C stream variant and documented its separate
  domain, round profile, output rate, and benchmark status.
- Added a fixed `fast8x` seed-123 stream vector and C test coverage for that
  vector.
- Added the reproducible crypto-analysis screen suite under `tests/`, with
  separate screen modules and an all-in-one quick runner.
- Added CI coverage for C tests, Python tests, and the quick crypto-analysis
  screen profile on non-Windows runners.
- Clarified that `fast8x` has been compared against the released TriCube
  stream baseline in the same C ablation harness, while optimized SHA-2,
  SHA-3/SHAKE, BLAKE2, and BLAKE3 library comparisons remain future work.
- Treat `paper/manuscript.md` as the tracked paper source and keep generated
  PDF/DOCX exports as release artifacts rather than source files.

## 0.1.0 - 2026-05-19

Initial public repository preparation for TriCube.

- Added standalone C11 implementation, public header, CLI, Makefile, and CMake build.
- Added Python package with hash, XOF, and deterministic stream APIs.
- Added fixed test vectors shared by the C and Python paths.
- Added documentation for design, testing, limitations, comparison, and reproducibility.
- Added cleaned result summary from the May 2026 internal validation pass.
