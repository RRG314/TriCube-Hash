#include "tricube.h"

#include <stdio.h>
#include <string.h>

static int expect_distinct(const char *name, const uint8_t *a, const uint8_t *b, size_t n) {
    if (memcmp(a, b, n) == 0) {
        fprintf(stderr, "%s unexpectedly matched\n", name);
        return 1;
    }
    return 0;
}

static int expect_deterministic(tricube_stream_variant variant, const char *name) {
    uint8_t a[512];
    uint8_t b[512];
    uint8_t c[512];
    if (tricube_stream_seed_variant(123, a, sizeof(a), variant) != TRICUBE_OK) {
        fprintf(stderr, "%s stream failed\n", name);
        return 1;
    }
    if (tricube_stream_seed_variant(123, b, sizeof(b), variant) != TRICUBE_OK) {
        fprintf(stderr, "%s repeat stream failed\n", name);
        return 1;
    }
    if (tricube_stream_seed_variant(124, c, sizeof(c), variant) != TRICUBE_OK) {
        fprintf(stderr, "%s changed-seed stream failed\n", name);
        return 1;
    }
    if (memcmp(a, b, sizeof(a)) != 0) {
        fprintf(stderr, "%s same-seed streams differ\n", name);
        return 1;
    }
    if (memcmp(a, c, sizeof(a)) == 0) {
        fprintf(stderr, "%s different-seed streams match\n", name);
        return 1;
    }
    for (size_t i = 0; i < sizeof(a); i++) {
        if (a[i] != 0) {
            return 0;
        }
    }
    fprintf(stderr, "%s stream was all zero\n", name);
    return 1;
}

int main(void) {
    int failures = 0;
    tricube_stream_variant parsed;
    uint8_t baseline[256];
    uint8_t fast8x[256];

    failures += expect_deterministic(TRICUBE_STREAM_BASELINE, "baseline");
    failures += expect_deterministic(TRICUBE_STREAM_FAST8X, "fast8x");

    if (tricube_stream_variant_from_name("baseline", &parsed) != TRICUBE_OK || parsed != TRICUBE_STREAM_BASELINE) {
        fprintf(stderr, "baseline variant parsing failed\n");
        failures++;
    }
    if (tricube_stream_variant_from_name("fast8x", &parsed) != TRICUBE_OK || parsed != TRICUBE_STREAM_FAST8X) {
        fprintf(stderr, "fast8x variant parsing failed\n");
        failures++;
    }
    if (tricube_stream_variant_from_name("r8x", &parsed) != TRICUBE_OK || parsed != TRICUBE_STREAM_FAST8X) {
        fprintf(stderr, "r8x variant alias parsing failed\n");
        failures++;
    }
    if (tricube_stream_variant_from_name("does-not-exist", &parsed) == TRICUBE_OK) {
        fprintf(stderr, "invalid variant was accepted\n");
        failures++;
    }

    tricube_stream_seed_variant(123, baseline, sizeof(baseline), TRICUBE_STREAM_BASELINE);
    tricube_stream_seed_variant(123, fast8x, sizeof(fast8x), TRICUBE_STREAM_FAST8X);
    failures += expect_distinct("fast8x vs baseline", fast8x, baseline, sizeof(fast8x));

    return failures ? 1 : 0;
}
