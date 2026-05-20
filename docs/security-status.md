# Security Status

TriCube is experimental and should not be used for security-critical work.

The current implementation has deterministic tests, fixed vectors, C/Python agreement checks, internal statistical checks, and selected external battery artifacts. Those results are useful for engineering triage. They are not a proof of security.

## Known Evidence

The current public repository includes:

- C self-test and vector tests;
- Python API tests;
- C/Python vector agreement;
- a cleaned May 2026 result summary;
- PractRand 1 GiB artifact with low-bit warnings;
- scripts for PractRand, Dieharder, TestU01, and NIST STS workflows.

The saved PractRand run reached 1 GiB and ended with no final-level anomalies, but earlier levels flagged suspicious or unusual low-bit behavior. That result is classified as WARN.

## Unknowns

The following work has not been completed:

- independent cryptanalysis;
- reduced-round attack study;
- differential trail analysis;
- rotational symmetry analysis;
- algebraic degree and invariant analysis;
- state-recovery attempts;
- collision and near-collision search at meaningful scales;
- domain-separation review;
- multi-seed long-run PractRand and TestU01 BigCrush campaigns;
- side-channel or constant-time review.

## Safe Wording

It is reasonable to say:

> TriCube is an experimental geometric hash/XOF candidate with a standalone C implementation, reproducible vectors, and early statistical testing evidence.

It is not reasonable to say:

> TriCube is secure, cryptographic-grade, collision resistant, preimage resistant, or a replacement for SHA-2, SHA-3, BLAKE2, or BLAKE3.

