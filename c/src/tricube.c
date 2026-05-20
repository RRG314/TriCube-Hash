/*
 * TriCube experimental hash/XOF candidate.
 *
 * This file contains the standalone C implementation of the TriCube core.
 * The construction is experimental and is not validated for security-critical
 * use. Some internal domain tags are retained from the May 2026 research
 * prototype so published test vectors and result artifacts remain reproducible.
 */

#include <errno.h>
#include <inttypes.h>
#include <math.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include "tricube.h"

#define TC_STATE_WORDS 32
#define TC_STATE_BITS (TC_STATE_WORDS * 64)
#define TC_BLOCK_BYTES 64
#define TC_RATE_BYTES 192
#define TC_RC_WORDS (32 * 24)
#define TC_TETRA_COUNT (8 * 6)
#define TC_EDGE_COUNT 54

static uint64_t ROUND_CONSTANTS[TC_RC_WORDS];
static uint64_t IV[TC_STATE_WORDS];
static uint8_t TETRAHEDRA[TC_TETRA_COUNT][4];
static uint8_t EDGES[TC_EDGE_COUNT][2];
static bool TABLES_READY = false;
static uint64_t DEFAULT_HASH32_STATE[TC_STATE_WORDS];
static bool DEFAULT_HASH32_STATE_READY = false;

static const uint8_t SHELL_LANES[5] = {27, 28, 29, 30, 31};
static const uint8_t ROTATION_SETS[4][4] = {
    {17, 29, 41, 53},
    {23, 31, 47, 59},
    {19, 37, 43, 61},
    {13, 27, 39, 55},
};

static inline uint64_t rotl64(uint64_t x, unsigned int r) {
    r &= 63U;
    if (r == 0) {
        return x;
    }
    return (x << r) | (x >> (64U - r));
}

static uint64_t splitmix64_next(uint64_t *x) {
    uint64_t z;
    *x += UINT64_C(0x9E3779B97F4A7C15);
    z = *x;
    z = (z ^ (z >> 30)) * UINT64_C(0xBF58476D1CE4E5B9);
    z = (z ^ (z >> 27)) * UINT64_C(0x94D049BB133111EB);
    return z ^ (z >> 31);
}

static void fill_constant_stream(uint64_t seed, uint64_t *out, size_t n) {
    uint64_t x = seed;
    for (size_t i = 0; i < n; i++) {
        out[i] = splitmix64_next(&x);
    }
}

static inline uint8_t vindex3(uint8_t x, uint8_t y, uint8_t z) {
    return (uint8_t)(x + 3U * (y + 3U * z));
}

static void cube_vertices(uint8_t cx, uint8_t cy, uint8_t cz, uint8_t out[8]) {
    out[0] = vindex3(cx, cy, cz);
    out[1] = vindex3((uint8_t)(cx + 1), cy, cz);
    out[2] = vindex3(cx, (uint8_t)(cy + 1), cz);
    out[3] = vindex3((uint8_t)(cx + 1), (uint8_t)(cy + 1), cz);
    out[4] = vindex3(cx, cy, (uint8_t)(cz + 1));
    out[5] = vindex3((uint8_t)(cx + 1), cy, (uint8_t)(cz + 1));
    out[6] = vindex3(cx, (uint8_t)(cy + 1), (uint8_t)(cz + 1));
    out[7] = vindex3((uint8_t)(cx + 1), (uint8_t)(cy + 1), (uint8_t)(cz + 1));
}

static void init_tables(void) {
    if (TABLES_READY) {
        return;
    }
    fill_constant_stream(UINT64_C(0x5452494355424556), ROUND_CONSTANTS, TC_RC_WORDS);
    fill_constant_stream(UINT64_C(0x5445545241435542), IV, TC_STATE_WORDS);

    static const uint8_t local_tets[6][4] = {
        {0, 1, 3, 7},
        {0, 3, 2, 7},
        {0, 2, 6, 7},
        {0, 6, 4, 7},
        {0, 4, 5, 7},
        {0, 5, 1, 7},
    };
    size_t t = 0;
    for (uint8_t cz = 0; cz < 2; cz++) {
        for (uint8_t cy = 0; cy < 2; cy++) {
            for (uint8_t cx = 0; cx < 2; cx++) {
                uint8_t verts[8];
                cube_vertices(cx, cy, cz, verts);
                for (size_t j = 0; j < 6; j++) {
                    for (size_t k = 0; k < 4; k++) {
                        TETRAHEDRA[t][k] = verts[local_tets[j][k]];
                    }
                    t++;
                }
            }
        }
    }

    size_t e = 0;
    for (uint8_t z = 0; z < 3; z++) {
        for (uint8_t y = 0; y < 3; y++) {
            for (uint8_t x = 0; x < 3; x++) {
                uint8_t i = vindex3(x, y, z);
                if (x + 1 < 3) {
                    EDGES[e][0] = i;
                    EDGES[e][1] = vindex3((uint8_t)(x + 1), y, z);
                    e++;
                }
                if (y + 1 < 3) {
                    EDGES[e][0] = i;
                    EDGES[e][1] = vindex3(x, (uint8_t)(y + 1), z);
                    e++;
                }
                if (z + 1 < 3) {
                    EDGES[e][0] = i;
                    EDGES[e][1] = vindex3(x, y, (uint8_t)(z + 1));
                    e++;
                }
            }
        }
    }
    TABLES_READY = true;
}

static uint64_t read_le64_padded(const uint8_t *data, size_t len, size_t offset) {
    uint64_t out = 0;
    for (size_t i = 0; i < 8; i++) {
        size_t pos = offset + i;
        if (pos < len) {
            out |= ((uint64_t)data[pos]) << (8U * i);
        }
    }
    return out;
}

static void write_le64(uint8_t *out, uint64_t value) {
    for (size_t i = 0; i < 8; i++) {
        out[i] = (uint8_t)((value >> (8U * i)) & 0xffU);
    }
}

static void write_le_u64_to_buf(uint8_t *out, uint64_t value) {
    write_le64(out, value);
}

static void write_le_u128_to_buf(uint8_t *out, uint64_t low, uint64_t high) {
    write_le64(out, low);
    write_le64(out + 8, high);
}

static void absorb_words(uint64_t state[TC_STATE_WORDS], const uint64_t *words, size_t n_words, uint64_t block_index) {
    for (size_t j = 0; j < n_words; j++) {
        uint64_t word = words[j];
        size_t lane = (j * 7U + (size_t)block_index * 5U) & 31U;
        size_t mate = (lane + 11U + j) & 31U;
        size_t shell = SHELL_LANES[(j + (size_t)block_index) % 5U];
        state[lane] ^= word + UINT64_C(0xD6E8FEB86659FD93) + block_index + j;
        state[mate] += rotl64(word ^ state[lane], (unsigned int)((j * 11U + (size_t)block_index) % 63U + 1U));
        state[shell] ^= rotl64(state[lane] + state[mate] + word, (unsigned int)((j * 13U + 7U) % 63U + 1U));
    }
}

static void absorb_bytes(uint64_t state[TC_STATE_WORDS], const uint8_t *data, size_t len, uint64_t block_index) {
    uint64_t words[8];
    for (size_t i = 0; i < 8; i++) {
        words[i] = read_le64_padded(data, len, i * 8U);
    }
    absorb_words(state, words, 8, block_index);
}

static void mix_tetra64(uint64_t state[TC_STATE_WORDS], const uint8_t tet[4], int rnd, size_t tet_index) {
    uint8_t a = tet[0];
    uint8_t b = tet[1];
    uint8_t c = tet[2];
    uint8_t d = tet[3];
    if ((rnd + (int)tet_index) & 1) {
        uint8_t tmp = b;
        b = d;
        d = tmp;
    }
    if ((rnd + (int)tet_index) & 2) {
        uint8_t tmp = a;
        a = c;
        c = tmp;
    }
    uint64_t x0 = state[a];
    uint64_t x1 = state[b];
    uint64_t x2 = state[c];
    uint64_t x3 = state[d];
    size_t base = ((size_t)rnd * 32U + tet_index) % TC_RC_WORDS;
    uint64_t rc0 = ROUND_CONSTANTS[base];
    uint64_t rc1 = ROUND_CONSTANTS[(base + 7U) % TC_RC_WORDS];
    uint64_t rc2 = ROUND_CONSTANTS[(base + 13U) % TC_RC_WORDS];
    uint64_t rc3 = ROUND_CONSTANTS[(base + 21U) % TC_RC_WORDS];
    const uint8_t *rots = ROTATION_SETS[(rnd + (int)tet_index) & 3];

    x0 += x1 + rc0;
    x3 = rotl64(x3 ^ x0, rots[0]);
    x2 += x3 + rc1;
    x1 = rotl64(x1 ^ x2, rots[1]);
    x0 += x1 + (rc2 ^ (uint64_t)tet_index);
    x3 = rotl64(x3 ^ x0, rots[2]);
    x2 += x3 + (rc3 + (uint64_t)rnd);
    x1 = rotl64(x1 ^ x2, rots[3]);

    state[a] = x0;
    state[b] = x1;
    state[c] = x2;
    state[d] = x3;
}

static void edge_couple64(uint64_t state[TC_STATE_WORDS], int rnd) {
    for (size_t edge_index = 0; edge_index < TC_EDGE_COUNT; edge_index++) {
        size_t a = EDGES[edge_index][0];
        size_t b = EDGES[edge_index][1];
        uint64_t rc = ROUND_CONSTANTS[((size_t)rnd * 37U + edge_index * 5U) % TC_RC_WORDS];
        uint64_t left = state[a];
        uint64_t right = state[b];
        state[a] = left + rotl64(right ^ rc, (unsigned int)((edge_index + (size_t)rnd * 3U) % 61U + 1U));
        state[b] = right ^ rotl64(state[a] + rc + edge_index, (unsigned int)((edge_index * 7U + (size_t)rnd) % 61U + 1U));
    }
}

static void shell_couple64(uint64_t state[TC_STATE_WORDS], int rnd) {
    for (size_t j = 0; j < 5; j++) {
        size_t lane = SHELL_LANES[j];
        size_t vertex = ((size_t)rnd * 5U + j * 7U) % 27U;
        size_t opposite = (vertex * 11U + 3U) % 27U;
        uint64_t rc = ROUND_CONSTANTS[((size_t)rnd * 11U + j * 17U) % TC_RC_WORDS];
        state[lane] += state[vertex] + rc;
        state[opposite] ^= rotl64(state[lane] ^ state[vertex], (unsigned int)(((size_t)rnd + j * 9U) % 61U + 1U));
    }
}

static void permute64(uint64_t state[TC_STATE_WORDS], int rounds) {
    uint64_t tmp[TC_STATE_WORDS];
    for (int rnd = 0; rnd < rounds; rnd++) {
        for (size_t tet_index = 0; tet_index < TC_TETRA_COUNT; tet_index++) {
            mix_tetra64(state, TETRAHEDRA[tet_index], rnd, tet_index);
        }
        edge_couple64(state, rnd);
        shell_couple64(state, rnd);
        for (size_t i = 0; i < TC_STATE_WORDS; i++) {
            tmp[i] = state[(i * 9U + 5U) & 31U];
        }
        memcpy(state, tmp, sizeof(tmp));
        size_t rc_offset = (size_t)rnd * 32U;
        for (size_t i = 0; i < TC_STATE_WORDS; i++) {
            state[i] ^= rotl64(ROUND_CONSTANTS[(rc_offset + i) % TC_RC_WORDS] + i + (uint64_t)rnd,
                               (unsigned int)((i * 5U + (size_t)rnd) % 61U + 1U));
        }
    }
}

static int half_rounds(int rounds) {
    int half = rounds / 2;
    return half > 6 ? half : 6;
}

static void init_state(uint64_t state[TC_STATE_WORDS], const uint8_t *domain, size_t domain_len,
                       const uint8_t *tweak, size_t tweak_len, uint32_t outlen) {
    static const uint8_t prefix[] = "TriCube-Tetra256-" "v" "2-native";
    uint8_t header[512];
    size_t pos = 0;
    init_tables();
    memcpy(state, IV, sizeof(IV));
    memcpy(header + pos, prefix, sizeof(prefix) - 1);
    pos += sizeof(prefix) - 1;
    header[pos++] = (uint8_t)(domain_len & 0xffU);
    header[pos++] = (uint8_t)((domain_len >> 8U) & 0xffU);
    header[pos++] = (uint8_t)(tweak_len & 0xffU);
    header[pos++] = (uint8_t)((tweak_len >> 8U) & 0xffU);
    header[pos++] = (uint8_t)(outlen & 0xffU);
    header[pos++] = (uint8_t)((outlen >> 8U) & 0xffU);
    header[pos++] = (uint8_t)((outlen >> 16U) & 0xffU);
    header[pos++] = (uint8_t)((outlen >> 24U) & 0xffU);
    if (domain_len > 0) {
        memcpy(header + pos, domain, domain_len);
        pos += domain_len;
    }
    if (tweak_len > 0) {
        memcpy(header + pos, tweak, tweak_len);
        pos += tweak_len;
    }
    size_t blocks = (pos + TC_BLOCK_BYTES - 1U) / TC_BLOCK_BYTES;
    if (blocks == 0) {
        blocks = 1;
    }
    for (size_t block_index = 0; block_index < blocks; block_index++) {
        size_t off = block_index * TC_BLOCK_BYTES;
        size_t take = pos > off ? pos - off : 0;
        if (take > TC_BLOCK_BYTES) {
            take = TC_BLOCK_BYTES;
        }
        absorb_bytes(state, header + off, take, block_index);
        permute64(state, 4);
    }
}

static bool use_default_hash32_state(uint64_t state[TC_STATE_WORDS], const uint8_t *domain, size_t domain_len,
                                     const uint8_t *tweak, size_t tweak_len, size_t encoded_outlen) {
    static const uint8_t default_domain[] = "TC-TETRA256-" "V" "2";
    if (encoded_outlen != 32U || tweak != NULL || tweak_len != 0U) {
        return false;
    }
    if (domain_len != sizeof(default_domain) - 1U || memcmp(domain, default_domain, sizeof(default_domain) - 1U) != 0) {
        return false;
    }
    if (!DEFAULT_HASH32_STATE_READY) {
        init_state(DEFAULT_HASH32_STATE, default_domain, sizeof(default_domain) - 1U, NULL, 0, 32U);
        DEFAULT_HASH32_STATE_READY = true;
    }
    memcpy(state, DEFAULT_HASH32_STATE, sizeof(DEFAULT_HASH32_STATE));
    return true;
}

static void squeeze_rate64(uint64_t state[TC_STATE_WORDS], uint64_t counter, uint8_t *out, size_t n_bytes) {
    size_t groups = (n_bytes + 7U) / 8U;
    uint8_t word_bytes[8];
    size_t pos = 0;
    for (size_t j = 0; j < groups; j++) {
        uint64_t a = state[(j * 5U + (size_t)counter) & 31U];
        uint64_t b = state[(j * 11U + 7U) & 31U];
        uint64_t c = state[(j * 17U + 13U) & 31U];
        uint64_t d = state[(j * 23U + 19U) & 31U];
        uint64_t word = a + rotl64(b ^ ROUND_CONSTANTS[(counter + j) % TC_RC_WORDS],
                                    (unsigned int)((j * 7U + 9U) % 61U + 1U));
        word ^= rotl64(c + d + j + counter, (unsigned int)((j * 13U + 3U) % 61U + 1U));
        write_le64(word_bytes, word);
        for (size_t k = 0; k < 8 && pos < n_bytes; k++) {
            out[pos++] = word_bytes[k];
        }
    }
}

static void tricube_hash_core(const uint8_t *data, size_t data_len, uint8_t *out, size_t outlen,
                      const uint8_t *domain, size_t domain_len, const uint8_t *tweak, size_t tweak_len,
                      size_t encoded_outlen, int rounds) {
    uint64_t state[TC_STATE_WORDS];
    uint64_t block_index = 0;
    if (!use_default_hash32_state(state, domain, domain_len, tweak, tweak_len, encoded_outlen)) {
        init_state(state, domain, domain_len, tweak, tweak_len, (uint32_t)encoded_outlen);
    }
    if (data_len == 0) {
        uint8_t empty_block[9] = {0x80, 0, 0, 0, 0, 0, 0, 0, 0};
        absorb_bytes(state, empty_block, sizeof(empty_block), block_index);
        permute64(state, half_rounds(rounds));
    } else {
        for (size_t off = 0; off < data_len; off += TC_BLOCK_BYTES) {
            size_t take = data_len - off;
            if (take > TC_BLOCK_BYTES) {
                take = TC_BLOCK_BYTES;
            }
            absorb_bytes(state, data + off, take, block_index);
            permute64(state, half_rounds(rounds));
            block_index++;
        }
    }

    uint8_t trailer[33];
    memset(trailer, 0, sizeof(trailer));
    write_le_u128_to_buf(trailer, (uint64_t)data_len, 0);
    write_le_u64_to_buf(trailer + 16, (uint64_t)encoded_outlen);
    write_le_u64_to_buf(trailer + 24, block_index);
    trailer[32] = 0x80;
    absorb_bytes(state, trailer, sizeof(trailer), block_index + 1U);
    permute64(state, rounds);

    size_t pos = 0;
    uint64_t counter = 0;
    while (pos < outlen) {
        uint8_t rate[TC_RATE_BYTES];
        size_t take = outlen - pos;
        if (take > TC_RATE_BYTES) {
            take = TC_RATE_BYTES;
        }
        squeeze_rate64(state, counter, rate, take);
        memcpy(out + pos, rate, take);
        pos += take;
        counter++;
        if (pos < outlen) {
            uint64_t words[4] = {
                counter,
                (uint64_t)encoded_outlen,
                (uint64_t)data_len,
                counter ^ UINT64_C(0xA5A5A5A5A5A5A5A5),
            };
            absorb_words(state, words, 4, block_index + counter + 2U);
            permute64(state, half_rounds(rounds));
        }
    }
}

static void seed_to_tweak(uint64_t seed, uint8_t out[16]) {
    memset(out, 0, 16);
    write_le64(out, seed);
}

static int write_stream(FILE *out, uint64_t seed, uint64_t n_bytes, size_t block_size, int rounds) {
    static const uint8_t domain[] = "TC-TETRA256-" "V" "2/STREAM";
    uint8_t seed_bytes[16];
    uint64_t state[TC_STATE_WORDS];
    uint8_t *block = NULL;
    uint64_t counter = 0;
    uint64_t written = 0;

    seed_to_tweak(seed, seed_bytes);
    init_state(state, domain, sizeof(domain) - 1, seed_bytes, sizeof(seed_bytes), 64);
    absorb_bytes(state, seed_bytes, sizeof(seed_bytes), 0);
    permute64(state, rounds);

    block = (uint8_t *)malloc(block_size);
    if (block == NULL) {
        fprintf(stderr, "allocation failed for %zu byte block\n", block_size);
        return 2;
    }

    while (written < n_bytes) {
        size_t pos = 0;
        while (pos < block_size) {
            uint64_t words[4] = {
                counter,
                counter ^ UINT64_C(0x9E3779B97F4A7C15),
                seed + counter,
                seed * UINT64_C(0xD6E8FEB86659FD93) + counter,
            };
            size_t take = block_size - pos;
            if (take > TC_RATE_BYTES) {
                take = TC_RATE_BYTES;
            }
            absorb_words(state, words, 4, counter + 1U);
            permute64(state, half_rounds(rounds));
            squeeze_rate64(state, counter, block + pos, take);
            pos += take;
            counter++;
        }
        size_t emit = block_size;
        if ((uint64_t)emit > n_bytes - written) {
            emit = (size_t)(n_bytes - written);
        }
        if (fwrite(block, 1, emit, out) != emit) {
            free(block);
            return 3;
        }
        written += (uint64_t)emit;
    }
    free(block);
    return 0;
}



static const uint8_t TRICUBE_DEFAULT_DOMAIN_BYTES[] = "TC-TETRA256-" "V" "2";

int tricube_xof(const uint8_t *data, size_t data_len, uint8_t *out, size_t out_len) {
    if ((data_len != 0 && data == NULL) || (out_len != 0 && out == NULL)) {
        return TRICUBE_ERR_INVALID_ARGUMENT;
    }
    tricube_hash_core(data, data_len, out, out_len,
                      TRICUBE_DEFAULT_DOMAIN_BYTES, sizeof(TRICUBE_DEFAULT_DOMAIN_BYTES) - 1U,
                      NULL, 0, 0, TRICUBE_DEFAULT_ROUNDS);
    return TRICUBE_OK;
}

int tricube_hash(const uint8_t *data, size_t data_len, uint8_t out[TRICUBE_DIGEST_BYTES]) {
    if ((data_len != 0 && data == NULL) || out == NULL) {
        return TRICUBE_ERR_INVALID_ARGUMENT;
    }
    tricube_hash_core(data, data_len, out, TRICUBE_DIGEST_BYTES,
                      TRICUBE_DEFAULT_DOMAIN_BYTES, sizeof(TRICUBE_DEFAULT_DOMAIN_BYTES) - 1U,
                      NULL, 0, TRICUBE_DIGEST_BYTES, TRICUBE_DEFAULT_ROUNDS);
    return TRICUBE_OK;
}

int tricube_stream_seed(uint64_t seed, uint8_t *out, size_t n_bytes) {
    if (n_bytes != 0 && out == NULL) {
        return TRICUBE_ERR_INVALID_ARGUMENT;
    }
    FILE *fp = tmpfile();
    if (fp == NULL) {
        return TRICUBE_ERR_IO;
    }
    int rc = write_stream(fp, seed, (uint64_t)n_bytes, 1U << 16, 12);
    if (rc == 0) {
        rewind(fp);
        if (fread(out, 1, n_bytes, fp) != n_bytes) {
            rc = TRICUBE_ERR_IO;
        }
    }
    fclose(fp);
    return rc == 0 ? TRICUBE_OK : TRICUBE_ERR_IO;
}

int tricube_stream_write(FILE *out, uint64_t seed, uint64_t n_bytes) {
    if (out == NULL) {
        return TRICUBE_ERR_INVALID_ARGUMENT;
    }
    int rc = write_stream(out, seed, n_bytes, 1U << 16, 12);
    return rc == 0 ? TRICUBE_OK : TRICUBE_ERR_IO;
}

int tricube_init(tricube_ctx *ctx) {
    if (ctx == NULL) {
        return TRICUBE_ERR_INVALID_ARGUMENT;
    }
    memset(ctx, 0, sizeof(*ctx));
    return TRICUBE_OK;
}

void tricube_free(tricube_ctx *ctx) {
    if (ctx == NULL) {
        return;
    }
    free(ctx->data);
    free(ctx->xof_cache);
    memset(ctx, 0, sizeof(*ctx));
}

int tricube_update(tricube_ctx *ctx, const uint8_t *data, size_t data_len) {
    if (ctx == NULL || (data_len != 0 && data == NULL) || ctx->finalized) {
        return TRICUBE_ERR_INVALID_ARGUMENT;
    }
    if (data_len == 0) {
        return TRICUBE_OK;
    }
    if (ctx->data_len > SIZE_MAX - data_len) {
        return TRICUBE_ERR_ALLOCATION;
    }
    size_t needed = ctx->data_len + data_len;
    if (needed > ctx->data_cap) {
        size_t cap = ctx->data_cap ? ctx->data_cap : 256U;
        while (cap < needed) {
            if (cap > SIZE_MAX / 2U) {
                return TRICUBE_ERR_ALLOCATION;
            }
            cap *= 2U;
        }
        uint8_t *next = (uint8_t *)realloc(ctx->data, cap);
        if (next == NULL) {
            return TRICUBE_ERR_ALLOCATION;
        }
        ctx->data = next;
        ctx->data_cap = cap;
    }
    memcpy(ctx->data + ctx->data_len, data, data_len);
    ctx->data_len += data_len;
    return TRICUBE_OK;
}

int tricube_finalize(tricube_ctx *ctx, uint8_t out[TRICUBE_DIGEST_BYTES]) {
    if (ctx == NULL || out == NULL) {
        return TRICUBE_ERR_INVALID_ARGUMENT;
    }
    int rc = tricube_hash(ctx->data, ctx->data_len, out);
    if (rc == TRICUBE_OK) {
        memcpy(ctx->digest, out, TRICUBE_DIGEST_BYTES);
        ctx->finalized = 1;
    }
    return rc;
}

int tricube_squeeze(tricube_ctx *ctx, uint8_t *out, size_t out_len) {
    if (ctx == NULL || (out_len != 0 && out == NULL)) {
        return TRICUBE_ERR_INVALID_ARGUMENT;
    }
    if (!ctx->finalized) {
        uint8_t digest[TRICUBE_DIGEST_BYTES];
        int rc = tricube_finalize(ctx, digest);
        if (rc != TRICUBE_OK) {
            return rc;
        }
    }
    size_t needed = ctx->squeeze_pos + out_len;
    if (needed > ctx->xof_cache_len) {
        uint8_t *next = (uint8_t *)realloc(ctx->xof_cache, needed ? needed : 1U);
        if (next == NULL) {
            return TRICUBE_ERR_ALLOCATION;
        }
        ctx->xof_cache = next;
        int rc = tricube_xof(ctx->data, ctx->data_len, ctx->xof_cache, needed);
        if (rc != TRICUBE_OK) {
            return rc;
        }
        ctx->xof_cache_len = needed;
    }
    memcpy(out, ctx->xof_cache + ctx->squeeze_pos, out_len);
    ctx->squeeze_pos += out_len;
    return TRICUBE_OK;
}

static void hex_encode(const uint8_t *data, size_t len, char *out) {
    static const char hexdigits[] = "0123456789abcdef";
    for (size_t i = 0; i < len; i++) {
        out[2U * i] = hexdigits[data[i] >> 4];
        out[2U * i + 1U] = hexdigits[data[i] & 15U];
    }
    out[2U * len] = '\0';
}

int tricube_hexdigest(const uint8_t *data, size_t data_len, char out_hex[TRICUBE_HEX_BYTES]) {
    uint8_t digest[TRICUBE_DIGEST_BYTES];
    if (out_hex == NULL) {
        return TRICUBE_ERR_INVALID_ARGUMENT;
    }
    int rc = tricube_hash(data, data_len, digest);
    if (rc != TRICUBE_OK) {
        return rc;
    }
    hex_encode(digest, sizeof(digest), out_hex);
    return TRICUBE_OK;
}

int tricube_self_test(void) {
    struct vector {
        const char *name;
        const uint8_t *data;
        size_t len;
        const char *expected;
    };
    static const uint8_t empty[] = "";
    static const uint8_t abc[] = "abc";
    static const uint8_t tricube[] = "TriCube";
    const struct vector vectors[] = {
        {"empty", empty, 0, "7fcaaa35165277bcaca583e23ef1d3545705e14d39f3ed7a802b1275d920cf49"},
        {"abc", abc, 3, "779403a9c748fc3213493953fc17309367b37161c00dc19059c14db63774e11e"},
        {"TriCube", tricube, 7, "5b4c461fe975dfba72fc9b2fbcf04e3a1a807c83fa4502c238ee4fe48b736d13"},
    };
    for (size_t i = 0; i < sizeof(vectors) / sizeof(vectors[0]); i++) {
        char got[TRICUBE_HEX_BYTES];
        int rc = tricube_hexdigest(vectors[i].data, vectors[i].len, got);
        if (rc != TRICUBE_OK || strcmp(got, vectors[i].expected) != 0) {
            return TRICUBE_ERR_SELF_TEST;
        }
    }
    return TRICUBE_OK;
}
