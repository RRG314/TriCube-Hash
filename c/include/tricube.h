#ifndef TRICUBE_H
#define TRICUBE_H

#include <stdint.h>
#include <stddef.h>
#include <stdio.h>

#ifdef __cplusplus
extern "C" {
#endif

#define TRICUBE_VERSION "0.1.0"
#define TRICUBE_DIGEST_BYTES 32
#define TRICUBE_HEX_BYTES 65
#define TRICUBE_DEFAULT_ROUNDS 16

typedef enum tricube_stream_variant {
    TRICUBE_STREAM_BASELINE = 0,
    TRICUBE_STREAM_FAST8X = 1,
    /* Experimental feedback-mixed stream candidates. These are opt-in
       research variants and do not replace the baseline stream path. */
    TRICUBE_STREAM_FAST8X384MIX = 2,
    TRICUBE_STREAM_FAST8X512MIX = 3,
    TRICUBE_STREAM_FAST8X768MIX = 4,
    TRICUBE_STREAM_FAST8X1024MIX = 5
} tricube_stream_variant;

typedef enum tricube_hash_variant {
    TRICUBE_HASH_BASELINE = 0,
    /* Experimental wide-group hash candidates. These are opt-in research
       modes and do not replace the baseline hash/XOF path. */
    TRICUBE_HASHFAST1024 = 1,
    TRICUBE_HASHFAST1024R6 = 2
} tricube_hash_variant;

enum {
    TRICUBE_OK = 0,
    TRICUBE_ERR_INVALID_ARGUMENT = 1,
    TRICUBE_ERR_ALLOCATION = 2,
    TRICUBE_ERR_IO = 3,
    TRICUBE_ERR_SELF_TEST = 4
};

typedef struct tricube_ctx {
    uint8_t *data;
    size_t data_len;
    size_t data_cap;
    uint8_t finalized;
    uint8_t digest[TRICUBE_DIGEST_BYTES];
    uint8_t *xof_cache;
    size_t xof_cache_len;
    size_t squeeze_pos;
} tricube_ctx;

int tricube_hash(const uint8_t *data, size_t data_len, uint8_t out[TRICUBE_DIGEST_BYTES]);
int tricube_hexdigest(const uint8_t *data, size_t data_len, char out_hex[TRICUBE_HEX_BYTES]);
int tricube_xof(const uint8_t *data, size_t data_len, uint8_t *out, size_t out_len);
int tricube_hash_with_variant(const uint8_t *data, size_t data_len, uint8_t out[TRICUBE_DIGEST_BYTES],
                              tricube_hash_variant variant);
int tricube_xof_with_variant(const uint8_t *data, size_t data_len, uint8_t *out, size_t out_len,
                             tricube_hash_variant variant);
const char *tricube_hash_variant_name(tricube_hash_variant variant);
int tricube_hash_variant_from_name(const char *name, tricube_hash_variant *variant);

int tricube_init(tricube_ctx *ctx);
int tricube_update(tricube_ctx *ctx, const uint8_t *data, size_t data_len);
int tricube_finalize(tricube_ctx *ctx, uint8_t out[TRICUBE_DIGEST_BYTES]);
int tricube_squeeze(tricube_ctx *ctx, uint8_t *out, size_t out_len);
void tricube_free(tricube_ctx *ctx);

int tricube_stream_seed(uint64_t seed, uint8_t *out, size_t n_bytes);
int tricube_stream_write(FILE *out, uint64_t seed, uint64_t n_bytes);
int tricube_stream_seed_variant(uint64_t seed, uint8_t *out, size_t n_bytes, tricube_stream_variant variant);
int tricube_stream_write_variant(FILE *out, uint64_t seed, uint64_t n_bytes, tricube_stream_variant variant);
int tricube_stream_write_unbounded(FILE *out, uint64_t seed, tricube_stream_variant variant);
const char *tricube_stream_variant_name(tricube_stream_variant variant);
int tricube_stream_variant_from_name(const char *name, tricube_stream_variant *variant);

int tricube_fast8x_stream_seed(uint64_t seed, uint8_t *out, size_t n_bytes);
int tricube_fast8x_stream_write(FILE *out, uint64_t seed, uint64_t n_bytes);
int tricube_fast8x_stream_write_unbounded(FILE *out, uint64_t seed);

int tricube_self_test(void);

#ifdef __cplusplus
}
#endif

#endif
