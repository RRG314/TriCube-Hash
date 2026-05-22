#include "tricube.h"

#include <stdio.h>
#include <string.h>

static int expect_variant_hex(const char *name, tricube_hash_variant variant,
                              const char *message, const char *expected) {
    uint8_t digest[TRICUBE_DIGEST_BYTES];
    char got[TRICUBE_HEX_BYTES];
    static const char hexdigits[] = "0123456789abcdef";
    int rc = tricube_hash_with_variant((const uint8_t *)message, strlen(message), digest, variant);
    if (rc != TRICUBE_OK) {
        fprintf(stderr, "%s: tricube_hash_with_variant returned %d\n", name, rc);
        return 1;
    }
    for (size_t i = 0; i < TRICUBE_DIGEST_BYTES; i++) {
        got[2U * i] = hexdigits[digest[i] >> 4];
        got[2U * i + 1U] = hexdigits[digest[i] & 15U];
    }
    got[TRICUBE_HEX_BYTES - 1U] = '\0';
    if (strcmp(got, expected) != 0) {
        fprintf(stderr, "%s: expected %s got %s\n", name, expected, got);
        return 1;
    }
    return 0;
}

static int expect_xof_prefix_differs(void) {
    uint8_t baseline[64];
    uint8_t fast1024[64];
    uint8_t fast1024r6[64];
    int rc = tricube_xof_with_variant((const uint8_t *)"abc", 3, baseline, sizeof(baseline), TRICUBE_HASH_BASELINE);
    rc |= tricube_xof_with_variant((const uint8_t *)"abc", 3, fast1024, sizeof(fast1024), TRICUBE_HASHFAST1024);
    rc |= tricube_xof_with_variant((const uint8_t *)"abc", 3, fast1024r6, sizeof(fast1024r6), TRICUBE_HASHFAST1024R6);
    if (rc != TRICUBE_OK) {
        fprintf(stderr, "xof variant call failed\n");
        return 1;
    }
    if (memcmp(baseline, fast1024, sizeof(baseline)) == 0 ||
        memcmp(baseline, fast1024r6, sizeof(baseline)) == 0 ||
        memcmp(fast1024, fast1024r6, sizeof(fast1024)) == 0) {
        fprintf(stderr, "xof variants are not domain separated\n");
        return 1;
    }
    return 0;
}

static int expect_variant_parse(const char *name, tricube_hash_variant expected) {
    tricube_hash_variant parsed;
    if (tricube_hash_variant_from_name(name, &parsed) != TRICUBE_OK || parsed != expected) {
        fprintf(stderr, "hash variant parse failed for %s\n", name);
        return 1;
    }
    return 0;
}

int main(void) {
    int failures = 0;
    failures += expect_variant_parse("baseline", TRICUBE_HASH_BASELINE);
    failures += expect_variant_parse("hashfast1024", TRICUBE_HASHFAST1024);
    failures += expect_variant_parse("hashfast1024r6", TRICUBE_HASHFAST1024R6);
    failures += expect_variant_hex(
        "hashfast1024-empty",
        TRICUBE_HASHFAST1024,
        "",
        "ed5cff65fbeee6a702bdf1eefddb5e73b7bb4a31500d21b6bddff7336081869e");
    failures += expect_variant_hex(
        "hashfast1024-abc",
        TRICUBE_HASHFAST1024,
        "abc",
        "9b3930e72f1b5f006ac845ac5cf4b0b243fc49d82e52dd23e54c208718f6c607");
    failures += expect_variant_hex(
        "hashfast1024r6-empty",
        TRICUBE_HASHFAST1024R6,
        "",
        "9c68491790e4728e200772cd91948529b4b31dc57c8a92aa943aee41d6faaa88");
    failures += expect_variant_hex(
        "hashfast1024r6-abc",
        TRICUBE_HASHFAST1024R6,
        "abc",
        "30b5095808175d52fb8afdf6933660752250696803873f4267068e77332da770");
    failures += expect_xof_prefix_differs();
    return failures ? 1 : 0;
}
