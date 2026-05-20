/*
 * TriCube fast8x stream entry points.
 *
 * fast8x is an experimental stream/XOF-oriented variant selected from the
 * ablation lab because it improved throughput without the low-bit failures
 * seen in faster private variants. The core permutation, state schedule, and
 * xmix extraction path remain centralized in tricube.c so the implementation
 * does not fork into a second primitive.
 *
 * This variant is not a security claim and does not replace the baseline
 * TriCube stream path. Use it explicitly through these functions or through
 * the CLI option: --variant fast8x.
 */

#include "tricube.h"

int tricube_fast8x_stream_seed(uint64_t seed, uint8_t *out, size_t n_bytes) {
    return tricube_stream_seed_variant(seed, out, n_bytes, TRICUBE_STREAM_FAST8X);
}

int tricube_fast8x_stream_write(FILE *out, uint64_t seed, uint64_t n_bytes) {
    return tricube_stream_write_variant(out, seed, n_bytes, TRICUBE_STREAM_FAST8X);
}

int tricube_fast8x_stream_write_unbounded(FILE *out, uint64_t seed) {
    return tricube_stream_write_unbounded(out, seed, TRICUBE_STREAM_FAST8X);
}
