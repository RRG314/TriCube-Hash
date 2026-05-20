# Security Status

TriCube is experimental and should not be used for security-critical work.

The current implementation has deterministic tests, fixed vectors, C/Python agreement checks, project statistical checks, and several external-battery evaluations. Those results are useful for engineering triage. They are not a proof of security.

## Known Evidence

The current public repository includes:

- C self-test and vector tests;
- Python API tests;
- C/Python vector agreement;
- a cleaned May 2026 result summary with quantitative battery, structural, and throughput results;
- SmokeRand express PASS, 7/7;
- NIST STS standard check PASS, with 188 parsed rows and no starred or failed-proportion rows;
- TestU01 SmallCrush PASS, 15/15;
- TestU01 Crush PASS, 144/144;
- Dieharder battery result of 109 PASS, 2 WEAK, and 0 FAIL;
- PractRand 1 GiB WARN because of unresolved low-bit warnings;
- scripts for PractRand, Dieharder, TestU01, and NIST STS workflows.

The PractRand 1 GiB evaluation reached the final level with no anomalies in 2050 final-level results, but earlier levels flagged suspicious or unusual low-bit behavior. That result is classified as WARN.

The structural probes in the result summary are black-box development screens.
They are useful for finding obvious diffusion, rotation, overlap, and prediction
failures. They are not formal differential cryptanalysis, formal rotational
cryptanalysis, algebraic cryptanalysis, or state-recovery proofs.

## Unknowns

The following work has not been completed:

- independent cryptanalysis;
- reduced-round attack study;
- formal differential trail analysis;
- formal rotational-distinguisher analysis;
- algebraic degree and invariant analysis at useful scale;
- state-recovery attack attempts;
- collision and near-collision search at meaningful scales;
- domain-separation review;
- multi-seed long-run PractRand, TestU01 Crush reruns, and TestU01 BigCrush campaigns;
- side-channel or constant-time review.

## Safe Wording

It is reasonable to say:

> TriCube is an experimental geometric hash/XOF candidate with a standalone C implementation, reproducible vectors, and early statistical testing evidence.

It is not reasonable to say:

> TriCube is secure, cryptographic-grade, collision resistant, preimage resistant, or a replacement for SHA-2, SHA-3, BLAKE2, or BLAKE3.
