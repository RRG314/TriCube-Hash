# Results

This directory contains concise public-facing result summaries, not large uncurated logs.

- `consolidated-results-2026-05-19.md` is the main cleaned evidence snapshot.
- `local-validation-2026-05-19.md` records the local build, test, package, CLI, and smoke benchmark run for this public repo.
- `raw/practrand-1gb-summary-2026-05-19.md` summarizes the most important external-battery warning.
- `raw/practrand-1gb-stdout-2026-05-19.txt` preserves the corresponding PractRand output log.

The fast8x stream optimization is documented under
`experiments/ablation-lab/` rather than as a large result-log bundle. That record
explains why `fast8x` was added as an explicit experimental stream variant and
why faster low-bit-warning variants were not promoted.

Large external-battery logs should normally be attached to releases or stored outside the main repository unless they are small enough and important enough to inspect directly.
