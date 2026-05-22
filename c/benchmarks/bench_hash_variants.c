#include "tricube.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static double now_seconds(void) {
    struct timespec ts;
    timespec_get(&ts, TIME_UTC);
    return (double)ts.tv_sec + (double)ts.tv_nsec / 1000000000.0;
}

static void fill_data(uint8_t *data, size_t n) {
    uint64_t x = UINT64_C(0x123456789abcdef0);
    for (size_t i = 0; i < n; i++) {
        x += UINT64_C(0x9E3779B97F4A7C15);
        uint64_t z = x;
        z = (z ^ (z >> 30)) * UINT64_C(0xBF58476D1CE4E5B9);
        z = (z ^ (z >> 27)) * UINT64_C(0x94D049BB133111EB);
        data[i] = (uint8_t)((z ^ (z >> 31)) >> ((i & 7U) * 8U));
    }
}

static int run_one(const char *name, tricube_hash_variant variant, const uint8_t *data, size_t size, int repeat) {
    uint8_t digest[TRICUBE_DIGEST_BYTES];
    volatile uint8_t sink = 0;
    double start = now_seconds();
    for (int i = 0; i < repeat; i++) {
        if (tricube_hash_with_variant(data, size, digest, variant) != TRICUBE_OK) {
            return 1;
        }
        sink ^= digest[(unsigned int)i & (TRICUBE_DIGEST_BYTES - 1U)];
    }
    double elapsed = now_seconds() - start;
    double mib = ((double)size * (double)repeat) / (1024.0 * 1024.0);
    double mib_per_s = elapsed > 0.0 ? mib / elapsed : 0.0;
    double hashes_per_s = elapsed > 0.0 ? (double)repeat / elapsed : 0.0;
    printf("%s,%zu,%d,%.6f,%.3f,%.3f,%u\n", name, size, repeat, elapsed, mib_per_s, hashes_per_s, (unsigned int)sink);
    return 0;
}

int main(int argc, char **argv) {
    int quick = 0;
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--quick") == 0) {
            quick = 1;
        } else {
            fprintf(stderr, "usage: %s [--quick]\n", argv[0]);
            return 2;
        }
    }
    const size_t sizes[] = {32, 64, 256, 1024, 4096, 65536, 1048576, 16777216};
    const size_t n_sizes = quick ? 6U : sizeof(sizes) / sizeof(sizes[0]);
    const struct {
        const char *name;
        tricube_hash_variant variant;
    } variants[] = {
        {"baseline", TRICUBE_HASH_BASELINE},
        {"hashfast1024", TRICUBE_HASHFAST1024},
        {"hashfast1024r6", TRICUBE_HASHFAST1024R6},
    };
    printf("variant,message_bytes,repeat,elapsed_s,mib_per_s,hashes_per_s,sink\n");
    for (size_t i = 0; i < n_sizes; i++) {
        size_t size = sizes[i];
        int repeat;
        if (quick) {
            repeat = size < 4096 ? 1000 : 100;
        } else if (size <= 1024) {
            repeat = 20000;
        } else if (size <= 65536) {
            repeat = 2000;
        } else if (size <= 1048576) {
            repeat = 128;
        } else {
            repeat = 8;
        }
        uint8_t *data = (uint8_t *)malloc(size ? size : 1U);
        if (data == NULL) {
            return 1;
        }
        fill_data(data, size);
        for (size_t v = 0; v < sizeof(variants) / sizeof(variants[0]); v++) {
            if (run_one(variants[v].name, variants[v].variant, data, size, repeat) != 0) {
                free(data);
                return 1;
            }
        }
        free(data);
    }
    return 0;
}
