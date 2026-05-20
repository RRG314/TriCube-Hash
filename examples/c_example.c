#include "tricube.h"

#include <stdio.h>
#include <string.h>

int main(void) {
    const unsigned char message[] = "abc";
    char hex[TRICUBE_HEX_BYTES];
    if (tricube_hexdigest(message, strlen((const char *)message), hex) != TRICUBE_OK) {
        return 1;
    }
    puts(hex);
    return 0;
}

