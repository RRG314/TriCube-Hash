# Tests and Analysis

This directory is the public testing home for TriCube. It keeps implementation
tests, fixed vectors, stream-variant ablation evidence, and cryptanalysis
screens in one place without mixing their purposes.

## Layout

- `smoke/` contains small pytest checks that exercise the packaged code and C
  vector agreement.
- `vectors/` contains fixed public test vectors.
- `ablation_lab/` contains the compact evidence for adding the experimental
  `fast8x` stream variant while leaving rejected high-speed variants out.
- `crypto_analysis/` contains reproducible development screens, low-bit
  diagnostics, the word-level schedule model, and optional external-tool setup
  checks.

The folders are separate because they answer different questions. The ablation
lab explains why one variant was kept. The crypto-analysis screens explain how
the current probes are run and what they do not prove. Neither folder
establishes cryptographic security.

Inside `crypto_analysis/`, the `screens/` subfolder contains the individual
screen entry points. `run_all_screens.py` remains as the combined runner and
imports those same screen modules.
