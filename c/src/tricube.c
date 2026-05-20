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
#define TC_SCHEDULE_ROUNDS 24

typedef struct tetra_op {
    uint8_t a;
    uint8_t b;
    uint8_t c;
    uint8_t d;
    uint8_t r0;
    uint8_t r1;
    uint8_t r2;
    uint8_t r3;
    uint64_t rc0;
    uint64_t rc1;
    uint64_t rc2;
    uint64_t rc3;
} tetra_op;

typedef struct edge_op {
    uint8_t a;
    uint8_t b;
    uint8_t r0;
    uint8_t r1;
    uint64_t rc;
} edge_op;

typedef struct shell_op {
    uint8_t lane;
    uint8_t vertex;
    uint8_t opposite;
    uint8_t rot;
    uint64_t rc;
} shell_op;

typedef struct perm_op {
    uint8_t src;
    uint8_t rot;
    uint64_t rc;
} perm_op;

static uint64_t ROUND_CONSTANTS[TC_RC_WORDS];
static uint64_t IV[TC_STATE_WORDS];
static uint8_t TETRAHEDRA[TC_TETRA_COUNT][4];
static uint8_t EDGES[TC_EDGE_COUNT][2];
static tetra_op TETRA_OPS[TC_SCHEDULE_ROUNDS][TC_TETRA_COUNT];
static edge_op EDGE_OPS[TC_SCHEDULE_ROUNDS][TC_EDGE_COUNT];
static shell_op SHELL_OPS[TC_SCHEDULE_ROUNDS][5];
static perm_op PERM_OPS[TC_SCHEDULE_ROUNDS][TC_STATE_WORDS];
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

    for (int rnd = 0; rnd < TC_SCHEDULE_ROUNDS; rnd++) {
        for (size_t tet_index = 0; tet_index < TC_TETRA_COUNT; tet_index++) {
            uint8_t a = TETRAHEDRA[tet_index][0];
            uint8_t b = TETRAHEDRA[tet_index][1];
            uint8_t c = TETRAHEDRA[tet_index][2];
            uint8_t d = TETRAHEDRA[tet_index][3];
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
            size_t base = ((size_t)rnd * 32U + tet_index) % TC_RC_WORDS;
            const uint8_t *rots = ROTATION_SETS[(rnd + (int)tet_index) & 3];
            TETRA_OPS[rnd][tet_index].a = a;
            TETRA_OPS[rnd][tet_index].b = b;
            TETRA_OPS[rnd][tet_index].c = c;
            TETRA_OPS[rnd][tet_index].d = d;
            TETRA_OPS[rnd][tet_index].r0 = rots[0];
            TETRA_OPS[rnd][tet_index].r1 = rots[1];
            TETRA_OPS[rnd][tet_index].r2 = rots[2];
            TETRA_OPS[rnd][tet_index].r3 = rots[3];
            TETRA_OPS[rnd][tet_index].rc0 = ROUND_CONSTANTS[base];
            TETRA_OPS[rnd][tet_index].rc1 = ROUND_CONSTANTS[(base + 7U) % TC_RC_WORDS];
            TETRA_OPS[rnd][tet_index].rc2 = ROUND_CONSTANTS[(base + 13U) % TC_RC_WORDS];
            TETRA_OPS[rnd][tet_index].rc3 = ROUND_CONSTANTS[(base + 21U) % TC_RC_WORDS];
        }
        for (size_t edge_index = 0; edge_index < TC_EDGE_COUNT; edge_index++) {
            EDGE_OPS[rnd][edge_index].a = EDGES[edge_index][0];
            EDGE_OPS[rnd][edge_index].b = EDGES[edge_index][1];
            EDGE_OPS[rnd][edge_index].rc = ROUND_CONSTANTS[((size_t)rnd * 37U + edge_index * 5U) % TC_RC_WORDS];
            EDGE_OPS[rnd][edge_index].r0 = (uint8_t)((edge_index + (size_t)rnd * 3U) % 61U + 1U);
            EDGE_OPS[rnd][edge_index].r1 = (uint8_t)((edge_index * 7U + (size_t)rnd) % 61U + 1U);
        }
        for (size_t j = 0; j < 5; j++) {
            uint8_t vertex = (uint8_t)(((size_t)rnd * 5U + j * 7U) % 27U);
            SHELL_OPS[rnd][j].lane = SHELL_LANES[j];
            SHELL_OPS[rnd][j].vertex = vertex;
            SHELL_OPS[rnd][j].opposite = (uint8_t)((vertex * 11U + 3U) % 27U);
            SHELL_OPS[rnd][j].rc = ROUND_CONSTANTS[((size_t)rnd * 11U + j * 17U) % TC_RC_WORDS];
            SHELL_OPS[rnd][j].rot = (uint8_t)(((size_t)rnd + j * 9U) % 61U + 1U);
        }
        for (size_t i = 0; i < TC_STATE_WORDS; i++) {
            PERM_OPS[rnd][i].src = (uint8_t)((i * 9U + 5U) & 31U);
            PERM_OPS[rnd][i].rc = ROUND_CONSTANTS[((size_t)rnd * 32U + i) % TC_RC_WORDS] + i + (uint64_t)rnd;
            PERM_OPS[rnd][i].rot = (uint8_t)((i * 5U + (size_t)rnd) % 61U + 1U);
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

static inline void emit_le64(uint8_t *out, size_t *pos, size_t n_bytes, uint64_t value) {
    size_t p = *pos;
    if (p + 8U <= n_bytes) {
        write_le64(out + p, value);
        *pos = p + 8U;
        return;
    }
    for (size_t k = 0; k < 8U && p < n_bytes; k++) {
        out[p++] = (uint8_t)((value >> (8U * k)) & 0xffU);
    }
    *pos = p;
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

static void permute64(uint64_t state[TC_STATE_WORDS], int rounds) {
    uint64_t tmp[TC_STATE_WORDS];
    for (int rnd = 0; rnd < rounds; rnd++) {
        int srnd = rnd % TC_SCHEDULE_ROUNDS;
        for (size_t tet_index = 0; tet_index < TC_TETRA_COUNT; tet_index++) {
            const tetra_op *op = &TETRA_OPS[srnd][tet_index];
            uint64_t x0 = state[op->a];
            uint64_t x1 = state[op->b];
            uint64_t x2 = state[op->c];
            uint64_t x3 = state[op->d];

            x0 += x1 + op->rc0;
            x3 = rotl64(x3 ^ x0, op->r0);
            x2 += x3 + op->rc1;
            x1 = rotl64(x1 ^ x2, op->r1);
            x0 += x1 + (op->rc2 ^ (uint64_t)tet_index);
            x3 = rotl64(x3 ^ x0, op->r2);
            x2 += x3 + (op->rc3 + (uint64_t)rnd);
            x1 = rotl64(x1 ^ x2, op->r3);

            state[op->a] = x0;
            state[op->b] = x1;
            state[op->c] = x2;
            state[op->d] = x3;
        }
        for (size_t edge_index = 0; edge_index < TC_EDGE_COUNT; edge_index++) {
            const edge_op *op = &EDGE_OPS[srnd][edge_index];
            uint64_t left = state[op->a];
            uint64_t right = state[op->b];
            state[op->a] = left + rotl64(right ^ op->rc, op->r0);
            state[op->b] = right ^ rotl64(state[op->a] + op->rc + edge_index, op->r1);
        }
        for (size_t j = 0; j < 5; j++) {
            const shell_op *op = &SHELL_OPS[srnd][j];
            state[op->lane] += state[op->vertex] + op->rc;
            state[op->opposite] ^= rotl64(state[op->lane] ^ state[op->vertex], op->rot);
        }
        for (size_t i = 0; i < TC_STATE_WORDS; i++) {
            tmp[i] = state[PERM_OPS[srnd][i].src];
        }
        memcpy(state, tmp, sizeof(tmp));
        for (size_t i = 0; i < TC_STATE_WORDS; i++) {
            state[i] ^= rotl64(PERM_OPS[srnd][i].rc, PERM_OPS[srnd][i].rot);
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
    size_t pos = 0;
    for (size_t j = 0; j < groups; j++) {
        uint64_t a = state[(j * 5U + (size_t)counter) & 31U];
        uint64_t b = state[(j * 11U + 7U) & 31U];
        uint64_t c = state[(j * 17U + 13U) & 31U];
        uint64_t d = state[(j * 23U + 19U) & 31U];
        uint64_t word = a + rotl64(b ^ ROUND_CONSTANTS[(counter + j) % TC_RC_WORDS],
                                    (unsigned int)((j * 7U + 9U) % 61U + 1U));
        word ^= rotl64(c + d + j + counter, (unsigned int)((j * 13U + 3U) % 61U + 1U));
        emit_le64(out, &pos, n_bytes, word);
    }
}

static void squeeze_rate64_xmix(uint64_t state[TC_STATE_WORDS], uint64_t counter, uint8_t *out, size_t n_bytes) {
    size_t groups = (n_bytes + 7U) / 8U;
    size_t pos = 0;
    for (size_t j = 0; j < groups; j++) {
        uint64_t a = state[(j * 5U + (size_t)counter) & 31U];
        uint64_t b = state[(j * 11U + 7U) & 31U];
        uint64_t c = state[(j * 17U + 13U) & 31U];
        uint64_t d = state[(j * 23U + 19U) & 31U];
        uint64_t e = state[(j * 29U + (size_t)counter * 3U + 3U) & 31U];
        uint64_t rc0 = ROUND_CONSTANTS[(counter * 13U + j * 17U) % TC_RC_WORDS];
        uint64_t rc1 = ROUND_CONSTANTS[(counter * 29U + j * 31U + 11U) % TC_RC_WORDS];
        uint64_t word = a + rotl64(b ^ rc0, (unsigned int)((j * 7U + 9U) % 61U + 1U));
        word ^= rotl64(c + d + j + counter, (unsigned int)((j * 13U + 3U) % 61U + 1U));
        word += rotl64(e ^ rc1 ^ (counter + j * UINT64_C(0x9E3779B97F4A7C15)),
                       (unsigned int)((j * 19U + 17U) % 61U + 1U));
        word ^= rotl64(word, 23) ^ rotl64(word, 41);
        word += rotl64(word ^ a ^ d, 17);
        word ^= (word >> 31) ^ (word >> 47);
        word += rotl64(word ^ b ^ c ^ rc0, 29);
        word ^= word >> 33;
        emit_le64(out, &pos, n_bytes, word);
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

typedef struct stream_profile {
    tricube_stream_variant variant;
    const char *name;
    const uint8_t *domain;
    size_t domain_len;
    int init_rounds;
    int step_rounds;
    size_t rate_bytes;
    int use_xmix;
} stream_profile;

static const uint8_t STREAM_DOMAIN_BASELINE[] = "TC-TETRA256-" "V" "2/STREAM";
static const uint8_t STREAM_DOMAIN_FAST8X[] = "TC-TETRA256-" "V" "2/STREAM/FAST8X";

static const stream_profile STREAM_PROFILES[] = {
    {TRICUBE_STREAM_BASELINE, "baseline", STREAM_DOMAIN_BASELINE, sizeof(STREAM_DOMAIN_BASELINE) - 1U, 12, 6, TC_RATE_BYTES, 0},
    {TRICUBE_STREAM_FAST8X, "fast8x", STREAM_DOMAIN_FAST8X, sizeof(STREAM_DOMAIN_FAST8X) - 1U, 8, 4, 256, 1},
};

static const stream_profile *stream_profile_for_variant(tricube_stream_variant variant) {
    for (size_t i = 0; i < sizeof(STREAM_PROFILES) / sizeof(STREAM_PROFILES[0]); i++) {
        if (STREAM_PROFILES[i].variant == variant) {
            return &STREAM_PROFILES[i];
        }
    }
    return NULL;
}

const char *tricube_stream_variant_name(tricube_stream_variant variant) {
    const stream_profile *profile = stream_profile_for_variant(variant);
    return profile == NULL ? NULL : profile->name;
}

int tricube_stream_variant_from_name(const char *name, tricube_stream_variant *variant) {
    if (name == NULL || variant == NULL) {
        return TRICUBE_ERR_INVALID_ARGUMENT;
    }
    if (strcmp(name, "baseline") == 0 || strcmp(name, "default") == 0 || strcmp(name, "released") == 0) {
        *variant = TRICUBE_STREAM_BASELINE;
        return TRICUBE_OK;
    }
    if (strcmp(name, "fast8x") == 0 || strcmp(name, "rounds8x") == 0 || strcmp(name, "r8x") == 0) {
        *variant = TRICUBE_STREAM_FAST8X;
        return TRICUBE_OK;
    }
    return TRICUBE_ERR_INVALID_ARGUMENT;
}

static void stream_init_state(uint64_t state[TC_STATE_WORDS], uint64_t seed, const stream_profile *profile) {
    uint8_t seed_bytes[16];
    seed_to_tweak(seed, seed_bytes);
    init_state(state, profile->domain, profile->domain_len, seed_bytes, sizeof(seed_bytes), 64);
    absorb_bytes(state, seed_bytes, sizeof(seed_bytes), 0);
    permute64(state, profile->init_rounds);
}

static void stream_fill_bytes(uint64_t state[TC_STATE_WORDS], uint64_t seed, const stream_profile *profile,
                              uint64_t *counter, uint8_t *out, size_t n_bytes) {
    size_t pos = 0;
    while (pos < n_bytes) {
        uint64_t words[4] = {
            *counter,
            *counter ^ UINT64_C(0x9E3779B97F4A7C15),
            seed + *counter,
            seed * UINT64_C(0xD6E8FEB86659FD93) + *counter,
        };
        size_t take = n_bytes - pos;
        if (take > profile->rate_bytes) {
            take = profile->rate_bytes;
        }
        absorb_words(state, words, 4, *counter + 1U);
        permute64(state, profile->step_rounds);
        if (profile->use_xmix) {
            squeeze_rate64_xmix(state, *counter, out + pos, take);
        } else {
            squeeze_rate64(state, *counter, out + pos, take);
        }
        pos += take;
        (*counter)++;
    }
}

static int write_stream_profile(FILE *out, uint64_t seed, uint64_t n_bytes, size_t block_size, const stream_profile *profile) {
    uint64_t state[TC_STATE_WORDS];
    uint8_t *block = NULL;
    uint64_t counter = 0;
    uint64_t written = 0;

    stream_init_state(state, seed, profile);

    block = (uint8_t *)malloc(block_size);
    if (block == NULL) {
        fprintf(stderr, "allocation failed for %zu byte block\n", block_size);
        return 2;
    }

    while (written < n_bytes) {
        size_t emit = block_size;
        if ((uint64_t)emit > n_bytes - written) {
            emit = (size_t)(n_bytes - written);
        }
        stream_fill_bytes(state, seed, profile, &counter, block, emit);
        if (fwrite(block, 1, emit, out) != emit) {
            free(block);
            return 3;
        }
        written += (uint64_t)emit;
    }
    free(block);
    return 0;
}

static int write_stream_profile_unbounded(FILE *out, uint64_t seed, size_t block_size, const stream_profile *profile) {
    uint64_t state[TC_STATE_WORDS];
    uint8_t *block = NULL;
    uint64_t counter = 0;

    stream_init_state(state, seed, profile);

    block = (uint8_t *)malloc(block_size);
    if (block == NULL) {
        fprintf(stderr, "allocation failed for %zu byte block\n", block_size);
        return 2;
    }

    while (1) {
        stream_fill_bytes(state, seed, profile, &counter, block, block_size);
        if (fwrite(block, 1, block_size, out) != block_size) {
            free(block);
            return ferror(out) ? 3 : 0;
        }
    }
}

static int stream_seed_profile(uint64_t seed, uint8_t *out, size_t n_bytes, const stream_profile *profile) {
    if (n_bytes != 0 && out == NULL) {
        return TRICUBE_ERR_INVALID_ARGUMENT;
    }
    uint64_t state[TC_STATE_WORDS];
    uint64_t counter = 0;
    stream_init_state(state, seed, profile);
    stream_fill_bytes(state, seed, profile, &counter, out, n_bytes);
    return TRICUBE_OK;
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
    return tricube_stream_seed_variant(seed, out, n_bytes, TRICUBE_STREAM_BASELINE);
}

int tricube_stream_seed_variant(uint64_t seed, uint8_t *out, size_t n_bytes, tricube_stream_variant variant) {
    const stream_profile *profile = stream_profile_for_variant(variant);
    if (profile == NULL) {
        return TRICUBE_ERR_INVALID_ARGUMENT;
    }
    return stream_seed_profile(seed, out, n_bytes, profile);
}

int tricube_stream_write(FILE *out, uint64_t seed, uint64_t n_bytes) {
    return tricube_stream_write_variant(out, seed, n_bytes, TRICUBE_STREAM_BASELINE);
}

int tricube_stream_write_variant(FILE *out, uint64_t seed, uint64_t n_bytes, tricube_stream_variant variant) {
    if (out == NULL) {
        return TRICUBE_ERR_INVALID_ARGUMENT;
    }
    const stream_profile *profile = stream_profile_for_variant(variant);
    if (profile == NULL) {
        return TRICUBE_ERR_INVALID_ARGUMENT;
    }
    int rc = write_stream_profile(out, seed, n_bytes, 1U << 20, profile);
    return rc == 0 ? TRICUBE_OK : TRICUBE_ERR_IO;
}

int tricube_stream_write_unbounded(FILE *out, uint64_t seed, tricube_stream_variant variant) {
    if (out == NULL) {
        return TRICUBE_ERR_INVALID_ARGUMENT;
    }
    const stream_profile *profile = stream_profile_for_variant(variant);
    if (profile == NULL) {
        return TRICUBE_ERR_INVALID_ARGUMENT;
    }
    int rc = write_stream_profile_unbounded(out, seed, 1U << 20, profile);
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
