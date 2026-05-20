# Limitations

TriCube is not ready for security use. The current project should be treated as a research candidate.

## Security Limitations

- No security proof exists.
- No independent cryptanalysis has been completed.
- Collision resistance is not established.
- Preimage and second-preimage resistance are not established.
- Output pseudorandomness is not established.
- Statistical batteries do not prove cryptographic security.
- Current external testing includes a PractRand 1 GiB warning that needs diagnosis.

## Engineering Limitations

- The C implementation is portable C11 but not heavily optimized.
- Performance is below mature optimized hash implementations.
- The context API currently buffers input before finalization, so very large file hashing should prefer CLI/file-oriented paths until streaming internals are hardened.
- Windows CI and wheel packaging need regular verification before public package release.

## Research Limitations

- Reduced-round attacks are incomplete.
- Differential and rotational analysis are incomplete.
- Algebraic structure analysis is incomplete.
- Birthday collision experiments are small relative to cryptographic claims.
- Long multi-seed PractRand, TestU01 Crush reruns, TestU01 BigCrush, larger NIST STS, and SmokeRand full campaigns remain open.

These limitations are intentional in the public documentation. They prevent the project from implying a stronger security status than the evidence supports.
