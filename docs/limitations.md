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

- The C implementation is portable C11 but not heavily optimized for hash mode.
- The experimental stream variants improve same-harness stream throughput over
  the released baseline, with `fast8x1024mix` reaching 375.694 MiB/s in the
  latest 256 MiB local run. This is stream/XOF-oriented evidence only. The
  main hash path remains much slower, and the missing performance comparison
  is against optimized SHA-2, SHA-3/SHAKE, BLAKE2, and BLAKE3 libraries on the
  same hardware.
- Wider stream extraction is a risk area. `fast8x768mix` crossed 300 MiB/s but
  showed PractRand Low4/64 unusual rows, so speed alone is not enough to
  justify promotion.
- The context API currently buffers input before finalization, so very large file hashing should prefer CLI/file-oriented paths until streaming internals are hardened.
- Windows CI and wheel packaging need regular verification before public package release.

## Research Limitations

- Reduced-round attacks are incomplete.
- Formal differential trail analysis is incomplete.
- Formal rotational-distinguisher analysis is incomplete.
- Algebraic structure analysis is incomplete.
- The current white-box work is limited to word-level schedule dependency and
  does not yet provide SAT, MILP, SMT, Gröbner, or trail-search results.
- The specification is now written as the normative description, but it still
  needs an independent clean-room implementation to prove that a reviewer can
  implement it without reading `c/src/tricube.c`.
- Birthday collision experiments are small relative to cryptographic claims.
- Long multi-seed PractRand, TestU01 Crush reruns, TestU01 BigCrush, larger NIST STS, and SmokeRand full campaigns remain open.

## Terminology Correction

Earlier project notes used shorter phrases such as differential probes,
rotational probes, and algebraic screens. The public documentation now uses
more precise names: black-box differential diffusion probe, black-box
rotational relation probe, small black-box algebraic degree screen,
collision/birthday sanity check, overlap/fork stream uniqueness screen,
black-box state-recovery/predictability screen, and low-bit diagnostic screen.
These are development gates intended to find obvious failures before deeper
analysis. Formal differential, rotational, algebraic, collision, and
state-recovery cryptanalysis remains future work.

These limitations are intentional in the public documentation. They prevent the project from implying a stronger security status than the evidence supports.
