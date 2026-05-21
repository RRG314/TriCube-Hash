# Experiments

This directory contains small, public-facing experiment records that explain why
selected implementation changes entered the repository. It is not a log archive.
Large terminal transcripts, generated streams, development-only scripts, and
rejected implementation branches are intentionally left out.

The current experiment records are:

- `ablation-lab/`, which documents why the `fast8x` stream variant was added
  as an experimental C stream/XOF path while faster but weaker variants were
  not promoted;
- `crypto-analysis/`, which contains compact reproducible development screens
  and a first white-box word-dependency model.

Optional solver and battery setup checks live under `crypto-analysis/tooling/`.
They are intentionally thin wrappers and smoke tests. External projects such
as Z3, SageMath, PractRand, TestU01, Dieharder, SmokeRand, and NIST STS are not
vendored into this repository.

These experiment records are engineering evidence only. They do not establish
cryptographic security.
