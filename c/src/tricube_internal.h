#ifndef TRICUBE_INTERNAL_H
#define TRICUBE_INTERNAL_H

#include <stddef.h>
#include <stdint.h>

#include "tricube.h"

typedef struct tricube_hash_profile {
    tricube_hash_variant variant;
    const char *name;
    const uint8_t *domain;
    size_t domain_len;
    size_t group_bytes;
    int group_rounds;
    int final_rounds;
    int squeeze_rounds;
} tricube_hash_profile;

typedef struct tricube_stream_profile {
    tricube_stream_variant variant;
    const char *name;
    const uint8_t *domain;
    size_t domain_len;
    int init_rounds;
    int step_rounds;
    size_t rate_bytes;
    int extractor;
} tricube_stream_profile;

const tricube_hash_profile *tricube_hash_profile_for_variant(tricube_hash_variant variant);
const tricube_stream_profile *tricube_stream_profile_for_variant(tricube_stream_variant variant);

#endif
