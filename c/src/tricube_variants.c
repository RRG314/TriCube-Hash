/*
 * TriCube variant profiles.
 *
 * The tables in this file define opt-in modes over the shared TriCube core.
 * They intentionally do not duplicate the round function or implement separate
 * primitives. This keeps reviewer-visible variant parameters in one place while
 * leaving the state update, absorb, squeeze, and stream machinery in tricube.c.
 */

#include <string.h>

#include "tricube_internal.h"

static const uint8_t HASH_DOMAIN_BASELINE[] = "TC-TETRA256-" "V" "2";
static const uint8_t HASH_DOMAIN_FAST1024[] = "TC-TETRA256-" "V" "2/HASH/G1024-R8-F16";
static const uint8_t HASH_DOMAIN_FAST1024R6[] = "TC-TETRA256-" "V" "2/HASH/G1024-R6-F16";

static const tricube_hash_profile HASH_PROFILES[] = {
    {
        TRICUBE_HASH_BASELINE,
        "baseline",
        HASH_DOMAIN_BASELINE,
        sizeof(HASH_DOMAIN_BASELINE) - 1U,
        64,
        8,
        TRICUBE_DEFAULT_ROUNDS,
        8,
    },
    {
        TRICUBE_HASHFAST1024,
        "hashfast1024",
        HASH_DOMAIN_FAST1024,
        sizeof(HASH_DOMAIN_FAST1024) - 1U,
        1024,
        8,
        16,
        8,
    },
    {
        TRICUBE_HASHFAST1024R6,
        "hashfast1024r6",
        HASH_DOMAIN_FAST1024R6,
        sizeof(HASH_DOMAIN_FAST1024R6) - 1U,
        1024,
        6,
        16,
        8,
    },
};

const tricube_hash_profile *tricube_hash_profile_for_variant(tricube_hash_variant variant) {
    for (size_t i = 0; i < sizeof(HASH_PROFILES) / sizeof(HASH_PROFILES[0]); i++) {
        if (HASH_PROFILES[i].variant == variant) {
            return &HASH_PROFILES[i];
        }
    }
    return NULL;
}

const char *tricube_hash_variant_name(tricube_hash_variant variant) {
    const tricube_hash_profile *profile = tricube_hash_profile_for_variant(variant);
    return profile == NULL ? NULL : profile->name;
}

int tricube_hash_variant_from_name(const char *name, tricube_hash_variant *variant) {
    if (name == NULL || variant == NULL) {
        return TRICUBE_ERR_INVALID_ARGUMENT;
    }
    if (strcmp(name, "baseline") == 0 || strcmp(name, "default") == 0 || strcmp(name, "released") == 0) {
        *variant = TRICUBE_HASH_BASELINE;
        return TRICUBE_OK;
    }
    if (strcmp(name, "hashfast1024") == 0 || strcmp(name, "g1024_r8_f16") == 0) {
        *variant = TRICUBE_HASHFAST1024;
        return TRICUBE_OK;
    }
    if (strcmp(name, "hashfast1024r6") == 0 || strcmp(name, "hashfast1024-r6") == 0 ||
        strcmp(name, "g1024_r6_f16") == 0) {
        *variant = TRICUBE_HASHFAST1024R6;
        return TRICUBE_OK;
    }
    return TRICUBE_ERR_INVALID_ARGUMENT;
}

static const uint8_t STREAM_DOMAIN_BASELINE[] = "TC-TETRA256-" "V" "2/STREAM";
static const uint8_t STREAM_DOMAIN_FAST8X[] = "TC-TETRA256-" "V" "2/STREAM/FAST8X";
static const uint8_t STREAM_DOMAIN_FAST8X384MIX[] = "TC-TETRA256-" "V" "2/STREAM/FAST8X384MIX";
static const uint8_t STREAM_DOMAIN_FAST8X512MIX[] = "TC-TETRA256-" "V" "2/STREAM/FAST8X512MIX";
static const uint8_t STREAM_DOMAIN_FAST8X768MIX[] = "TC-TETRA256-" "V" "2/STREAM/FAST8X768MIX";
static const uint8_t STREAM_DOMAIN_FAST8X1024MIX[] = "TC-TETRA256-" "V" "2/STREAM/FAST8X1024MIX";

static const tricube_stream_profile STREAM_PROFILES[] = {
    {
        TRICUBE_STREAM_BASELINE,
        "baseline",
        STREAM_DOMAIN_BASELINE,
        sizeof(STREAM_DOMAIN_BASELINE) - 1U,
        12,
        6,
        192,
        0,
    },
    {
        TRICUBE_STREAM_FAST8X,
        "fast8x",
        STREAM_DOMAIN_FAST8X,
        sizeof(STREAM_DOMAIN_FAST8X) - 1U,
        8,
        4,
        256,
        1,
    },
    {
        TRICUBE_STREAM_FAST8X384MIX,
        "fast8x384mix",
        STREAM_DOMAIN_FAST8X384MIX,
        sizeof(STREAM_DOMAIN_FAST8X384MIX) - 1U,
        8,
        4,
        384,
        2,
    },
    {
        TRICUBE_STREAM_FAST8X512MIX,
        "fast8x512mix",
        STREAM_DOMAIN_FAST8X512MIX,
        sizeof(STREAM_DOMAIN_FAST8X512MIX) - 1U,
        8,
        4,
        512,
        2,
    },
    {
        TRICUBE_STREAM_FAST8X768MIX,
        "fast8x768mix",
        STREAM_DOMAIN_FAST8X768MIX,
        sizeof(STREAM_DOMAIN_FAST8X768MIX) - 1U,
        8,
        4,
        768,
        2,
    },
    {
        TRICUBE_STREAM_FAST8X1024MIX,
        "fast8x1024mix",
        STREAM_DOMAIN_FAST8X1024MIX,
        sizeof(STREAM_DOMAIN_FAST8X1024MIX) - 1U,
        8,
        4,
        1024,
        2,
    },
};

const tricube_stream_profile *tricube_stream_profile_for_variant(tricube_stream_variant variant) {
    for (size_t i = 0; i < sizeof(STREAM_PROFILES) / sizeof(STREAM_PROFILES[0]); i++) {
        if (STREAM_PROFILES[i].variant == variant) {
            return &STREAM_PROFILES[i];
        }
    }
    return NULL;
}

const char *tricube_stream_variant_name(tricube_stream_variant variant) {
    const tricube_stream_profile *profile = tricube_stream_profile_for_variant(variant);
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
    if (strcmp(name, "fast8x384mix") == 0 || strcmp(name, "fast8x384") == 0 || strcmp(name, "r8x384") == 0) {
        *variant = TRICUBE_STREAM_FAST8X384MIX;
        return TRICUBE_OK;
    }
    if (strcmp(name, "fast8x512mix") == 0 || strcmp(name, "fast8x512") == 0 || strcmp(name, "r8x512") == 0) {
        *variant = TRICUBE_STREAM_FAST8X512MIX;
        return TRICUBE_OK;
    }
    if (strcmp(name, "fast8x768mix") == 0 || strcmp(name, "fast8x768") == 0 || strcmp(name, "r8x768") == 0) {
        *variant = TRICUBE_STREAM_FAST8X768MIX;
        return TRICUBE_OK;
    }
    if (strcmp(name, "fast8x1024mix") == 0 || strcmp(name, "fast8x1024") == 0 || strcmp(name, "r8x1024") == 0) {
        *variant = TRICUBE_STREAM_FAST8X1024MIX;
        return TRICUBE_OK;
    }
    return TRICUBE_ERR_INVALID_ARGUMENT;
}
