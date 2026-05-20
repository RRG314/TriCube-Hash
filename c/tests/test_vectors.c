#include "tricube.h"

#include <stdio.h>
#include <string.h>

static int expect_hex(const char *name, const char *message, const char *expected) {
    char got[TRICUBE_HEX_BYTES];
    int rc = tricube_hexdigest((const uint8_t *)message, strlen(message), got);
    if (rc != TRICUBE_OK) {
        fprintf(stderr, "%s: tricube_hexdigest returned %d\n", name, rc);
        return 1;
    }
    if (strcmp(got, expected) != 0) {
        fprintf(stderr, "%s: expected %s got %s\n", name, expected, got);
        return 1;
    }
    return 0;
}

int main(void) {
    int failures = 0;
    failures += expect_hex("empty", "", "7fcaaa35165277bcaca583e23ef1d3545705e14d39f3ed7a802b1275d920cf49");
    failures += expect_hex("abc", "abc", "779403a9c748fc3213493953fc17309367b37161c00dc19059c14db63774e11e");
    failures += expect_hex("TriCube", "TriCube", "5b4c461fe975dfba72fc9b2fbcf04e3a1a807c83fa4502c238ee4fe48b736d13");
    return failures ? 1 : 0;
}
