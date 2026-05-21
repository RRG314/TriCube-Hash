# TriCube Stream Ablation Lab

This ablation lab tested whether the released TriCube stream path could be made
faster without accepting obvious statistical regressions. The public repository
keeps only the result that passed the current screening threshold:

- `baseline`: the released TriCube stream path, kept as the default.
- `fast8x`: an experimental stream variant using 8 initialization rounds, 4
  per-block rounds, a 256-byte stream rate, and an additional TriCube-family
  output mixer.

The ablation lab is about speed and variant selection. The reproducible
black-box development probes for differential diffusion, rotational relations,
algebraic degree, collision/birthday behavior, overlap/fork uniqueness,
predictability, and low-bit diagnostics live separately in
[tests/crypto_analysis/](../crypto_analysis/). Keeping those two folders
separate makes the evidence easier to read: this folder explains why `fast8x`
was the only optimized variant carried forward, while `crypto_analysis`
explains how the current screens are run and what they do not prove.

The rejected high-speed paths are documented here but are not included in the
public C API. They produced higher throughput by widening the extraction rate
or batching output, but the strongest versions also produced low-bit PractRand
warnings or failures. Those variants remain excluded until the failure mode is
understood.

## Why fast8x was added

`fast8x` was the best speed/safety tradeoff in the ablation pass. On the
same Apple M4 Pro machine used for the May 2026 result refresh, it
measured about `132.65 MiB/s` for a 256 MiB stream run, compared with about
`69.80 MiB/s` for the released baseline in the same harness.

After adding `fast8x` to the repository, a smaller 64 MiB smoke benchmark
measured `130.94 MiB/s` for `fast8x` and `73.07 MiB/s` for the baseline. That
run is recorded in
[tables/fast8x_stream_smoke_bench.csv](tables/fast8x_stream_smoke_bench.csv).

The same ablation record lists `fast8x` as clean through:

- PractRand 1 GiB screen;
- SmokeRand express, 7/7 tests;
- TestU01 SmallCrush, 15/15 tests;
- 16 MiB sanity probes with no repeated 32-byte blocks.

These checks are not security claims. They justify keeping `fast8x` available
for continued testing, not using TriCube in security-critical systems.

## What changed in fast8x

Compared with the baseline stream path:

- the stream domain is separated as `.../STREAM/FAST8X`;
- initialization uses 8 rounds instead of 12;
- each stream block update uses 4 rounds instead of 6;
- the output rate is widened from 192 bytes to 256 bytes per state update;
- output words pass through an additional xmix layer derived from the TriCube
  state and round constants.

The hash API, digest vectors, XOF API, and default stream behavior remain
unchanged. Users must explicitly request the variant:

```bash
c/build/tricube stream --seed 123 --bytes 1048576 --out stream.bin --variant fast8x
```

For source navigation, the named C entry points are in
`c/src/tricube_fast8x.c`. The shared permutation, state schedule, and `fast8x`
stream profile remain in `c/src/tricube.c`.

## Rejected high-speed variants

Several faster variants were tested but not promoted:

- `fast8x_batch` reached about `311.98 MiB/s`, but failed PractRand low-bit FPF
  checks at 8 KiB.
- `fast8x_wide` reached about `285.71 MiB/s`, but showed very suspicious
  low-bit rows by 16 KiB.
- `fast8x512` reached about `230.74 MiB/s`, but had recurring mild low-bit
  warnings.
- `fast4x512` reached about `371.32 MiB/s`, but had too much warning density.

The public rule is conservative: speed gains that introduce repeatable low-bit
warnings do not get promoted.

## Tables

The compact public tables are:

- [tables/stream_speed_variants.csv](tables/stream_speed_variants.csv)
- [tables/quality_gate_summary.csv](tables/quality_gate_summary.csv)
- [tables/external_screen_summary.csv](tables/external_screen_summary.csv)
- [tables/candidate_recommendations.csv](tables/candidate_recommendations.csv)
- [tables/fast8x_stream_smoke_bench.csv](tables/fast8x_stream_smoke_bench.csv)

Large generated streams, full terminal transcripts, and rejected C implementations are
not included in the repository.
