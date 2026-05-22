# TriCube Stream Ablation Lab

This ablation lab tests whether the released TriCube stream path can be made
faster without accepting obvious statistical regressions. The default stream
path remains the preserved baseline, and every faster path is opt-in.

- `baseline`: the released TriCube stream path, kept as the default.
- `fast8x`: an experimental stream variant using 8 initialization rounds, 4
  per-block rounds, a 256-byte stream rate, and an additional TriCube-family
  output mixer.
- `fast8x384mix`, `fast8x512mix`, `fast8x768mix`, and `fast8x1024mix`:
  newer feedback-mixed stream candidates that keep the `fast8x` round budget
  but widen the output rate and chain the extraction through state-derived
  carry terms.

The ablation lab is about speed and variant selection. The reproducible
black-box development probes for differential diffusion, rotational relations,
algebraic degree, collision/birthday behavior, overlap/fork uniqueness,
predictability, and low-bit diagnostics live separately in
[tests/crypto_analysis/](../crypto_analysis/). Keeping those two folders
separate makes the evidence easier to read: this folder explains variant
selection and speed results, while `crypto_analysis` explains how the current
screens are run and what they do not prove.

Older high-speed paths that produced low-bit failures remain excluded. The
newer feedback-mixed candidates are included for review because they are
domain-separated, deterministic, covered by fixed vectors, and easier to test
side by side with the baseline.

## Why fast8x was added

`fast8x` was the best speed/safety tradeoff in the first ablation pass. On the
same Apple M4 Pro machine used for the May 2026 result refresh, that pass
measured about `132.65 MiB/s` for a 256 MiB stream run, compared with about
`69.80 MiB/s` for the released baseline in the same harness.

After adding `fast8x` to the repository, a smaller 64 MiB smoke benchmark
measured `130.94 MiB/s` for `fast8x` and `73.07 MiB/s` for the baseline. That
run is recorded in
[tables/fast8x_stream_smoke_bench.csv](tables/fast8x_stream_smoke_bench.csv).
The latest portable `-O3` 256 MiB run measured `150.01 MiB/s` for `fast8x`
and `79.97 MiB/s` for the baseline. The older numbers are retained because
they are the original acceptance record for adding `fast8x`; the latest numbers
are used in the current variant ranking table.

The same ablation record lists `fast8x` as clean through:

- PractRand 1 GiB screen;
- SmokeRand express, 7/7 tests;
- TestU01 SmallCrush, 15/15 tests;
- 16 MiB sanity probes with no repeated 32-byte blocks.

These checks are not security claims. They justify keeping `fast8x` available
for continued testing, not using TriCube in security-critical systems.

## New feedback-mixed candidates

The feedback-mixed candidates were added to push stream/XOF throughput without
using an external hash or cipher as a whitening layer. They keep the `fast8x`
stream round budget: 8 initialization rounds and 4 rounds per stream step. The
change is in the output path.

Each `fast8x*mix` variant uses a separate domain tag and a wider output rate:

| Variant | Output rate | Latest 256 MiB throughput | Current interpretation |
|---|---:|---:|---|
| `fast8x384mix` | 384 bytes | 185.30 MiB/s | Faster than `fast8x`, below the main speed target. |
| `fast8x512mix` | 512 bytes | 238.32 MiB/s | Useful middle candidate if wider extraction later regresses. |
| `fast8x768mix` | 768 bytes | 316.22 MiB/s | Crosses 300 MiB/s but has a PractRand low-bit watch item. |
| `fast8x1024mix` | 1024 bytes | 375.69 MiB/s | Current best local candidate; needs long batteries before promotion. |

The output layer first computes the xmix word and then folds it with two carry
words derived from the current state, round constants, and stream counter. The
carry words are updated after each 64-bit emitted word. This is meant to make
the wider output a chained TriCube-family extraction path rather than a raw
state read.

The strongest current local result is `fast8x1024mix`: it passed the 64 MiB
low-bit diagnostic, SmokeRand express, PractRand to 1 GiB, and TestU01
SmallCrush in the latest local run. That is enough to justify deeper testing,
not enough to claim cryptographic security.

`fast8x768mix` is a cautionary result. It crossed the 300 MiB/s target, but
PractRand reported Low4/64 DC6 unusual rows at 16 MiB and 256 MiB. It should
not be promoted unless that pattern disappears under a corrected design and
longer multi-seed testing.

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

The feedback-mixed candidates use the same CLI shape:

```bash
c/build/tricube stream --seed 123 --bytes 1048576 --out stream.bin --variant fast8x1024mix
```

For source navigation, the named C entry points are in
`c/src/tricube_fast8x.c`. The shared permutation, state schedule, and all
stream profiles remain in `c/src/tricube.c`.

## Rejected high-speed variants

Several older faster variants were tested but not promoted:

- `fast8x_batch` reached about `311.98 MiB/s`, but failed PractRand low-bit FPF
  checks at 8 KiB.
- `fast8x_wide` reached about `285.71 MiB/s`, but showed very suspicious
  low-bit rows by 16 KiB.
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
- [tables/latest_low_bit_diagnostics.csv](tables/latest_low_bit_diagnostics.csv)

Large generated streams, full terminal transcripts, and rejected C implementations are
not included in the repository.
