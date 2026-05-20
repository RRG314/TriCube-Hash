#include "tricube.h"

#include <stdio.h>
#include <string.h>

int main(void) {
    uint8_t a[128];
    uint8_t b[128];
    uint8_t c[128];
    if (tricube_stream_seed(123, a, sizeof(a)) != TRICUBE_OK) {
        fprintf(stderr, "stream_seed failed\n");
        return 1;
    }
    if (tricube_stream_seed(123, b, sizeof(b)) != TRICUBE_OK) {
        fprintf(stderr, "stream_seed repeat failed\n");
        return 1;
    }
    if (tricube_stream_seed(124, c, sizeof(c)) != TRICUBE_OK) {
        fprintf(stderr, "stream_seed different seed failed\n");
        return 1;
    }
    if (memcmp(a, b, sizeof(a)) != 0) {
        fprintf(stderr, "same-seed streams differ\n");
        return 1;
    }
    if (memcmp(a, c, sizeof(a)) == 0) {
        fprintf(stderr, "different-seed streams match\n");
        return 1;
    }
    for (size_t i = 0; i < sizeof(a); i++) {
        if (a[i] != 0) {
            return 0;
        }
    }
    fprintf(stderr, "stream output was all zero\n");
    return 1;
}
