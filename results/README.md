# Results

This directory contains concise public-facing result summaries, not large uncurated logs.

- `consolidated-results-2026-05-19.md` is the main cleaned evidence snapshot.
- `local-validation-2026-05-19.md` records the local build, test, package, CLI, and smoke benchmark run for this public repo.
- `raw/practrand-1gb-summary-2026-05-19.md` summarizes the most important external-battery warning.
- `raw/practrand-1gb-stdout-2026-05-19.txt` preserves the corresponding PractRand output log.

The stream optimization work is documented under `tests/ablation_lab/` rather
than as a large result-log bundle. That record explains why `fast8x` was added,
how the feedback-mixed `fast8x*mix` candidates differ, and why variants with
repeatable low-bit warnings are held back.

The latest local stream result is 375.694 MiB/s for `fast8x1024mix` on a
256 MiB stream run, versus 79.971 MiB/s for the released TriCube baseline in
the same C harness. That is a baseline comparison inside the TriCube
implementation family. Optimized SHA-2, SHA-3/SHAKE, BLAKE2, and BLAKE3
library comparisons remain future work.

Large external-battery logs should normally be attached to releases or stored outside the main repository unless they are small enough and important enough to inspect directly.
