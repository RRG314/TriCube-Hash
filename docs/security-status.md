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
- a first white-box word-dependency model showing full 32-lane dependency by
  round 2 at 64-bit lane granularity;
- scripts for PractRand, Dieharder, TestU01, and NIST STS workflows.

The PractRand 1 GiB evaluation reached the final level with no anomalies in 2050 final-level results, but earlier levels flagged suspicious or unusual low-bit behavior. That result is classified as WARN.

The structural probes in the result summary are black-box development screens:
the black-box differential diffusion probe, black-box rotational relation
probe, small black-box algebraic degree screen, collision/birthday sanity
check, overlap/fork stream uniqueness screen, black-box
state-recovery/predictability screen, and low-bit diagnostic screen. They are
useful for finding obvious diffusion, rotation, overlap, prediction, collision,
and low-bit warning patterns. They are not formal differential cryptanalysis,
formal rotational cryptanalysis, algebraic cryptanalysis, collision-resistance
evidence, or state-recovery proofs.

The white-box round model is stronger than a black-box output probe in one
narrow way: it inspects the specified tetrahedron, edge, shell, and permutation
schedule directly. Its current result is only a word-level reachability result.
It does not model bit-level differential probabilities, rotational trails,
algebraic equations, or attack cost.

The reproducible versions of these screens now live in
`experiments/crypto-analysis/`. They record compact JSON, Markdown, and CSV
summaries with branch, commit, command, seed, sample count, byte count, and
PASS/WARN/FAIL/BLOCKED/NOT_RUN status labels.

The open-source tooling plan is in [tooling.md](tooling.md). The intended path
for deeper work is to build a verified reduced-round TriCube model and then use
standard solvers and algebra systems such as Z3, SageMath, SAT solvers, and
cryptanalysis frameworks where they fit. The repo does not treat private
black-box screens as substitutes for those tools.

## Unknowns

The following work has not been completed:

- independent cryptanalysis;
- reduced-round attack study;
- formal differential trail analysis;
- formal rotational-distinguisher analysis;
- algebraic degree and invariant analysis at useful scale;
- SAT/SMT/MILP or Gröbner-style reduced-round modeling;
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
