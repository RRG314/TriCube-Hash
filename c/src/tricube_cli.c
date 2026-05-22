#include "tricube.h"

#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void usage(const char *argv0) {
    fprintf(stderr,
            "Usage:\n"
            "  %s self-test\n"
            "  %s vectors\n"
            "  %s hash <file> [--variant baseline|hashfast1024|hashfast1024r6]\n"
            "  %s hash --hex HEX [--variant baseline|hashfast1024|hashfast1024r6]\n"
            "  %s xof --hex HEX --bytes N [--variant baseline|hashfast1024|hashfast1024r6]\n"
            "  %s digest-stream --seed N --messages N --message-bytes N --out FILE [--variant baseline|hashfast1024|hashfast1024r6]\n"
            "  %s stream --seed N --bytes N --out FILE [--variant baseline|fast8x|fast8x384mix|fast8x512mix|fast8x768mix|fast8x1024mix]\n"
            "  %s stream --seed N --unbounded --out - [--variant baseline|fast8x|fast8x384mix|fast8x512mix|fast8x768mix|fast8x1024mix]\n",
            argv0, argv0, argv0, argv0, argv0, argv0, argv0, argv0);
}

static uint64_t parse_u64(const char *value, const char *name) {
    char *end = NULL;
    errno = 0;
    unsigned long long out = strtoull(value, &end, 10);
    if (errno || end == value || *end != '\0') {
        fprintf(stderr, "invalid %s: %s\n", name, value);
        exit(2);
    }
    return (uint64_t)out;
}

static int hex_value(int c) {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return -1;
}

static int parse_hex(const char *hex, uint8_t **out, size_t *out_len) {
    size_t len = strlen(hex);
    if (len % 2U != 0) {
        return 1;
    }
    *out_len = len / 2U;
    *out = (uint8_t *)malloc(*out_len ? *out_len : 1U);
    if (*out == NULL) {
        return 2;
    }
    for (size_t i = 0; i < *out_len; i++) {
        int hi = hex_value((unsigned char)hex[2U * i]);
        int lo = hex_value((unsigned char)hex[2U * i + 1U]);
        if (hi < 0 || lo < 0) {
            free(*out);
            *out = NULL;
            *out_len = 0;
            return 3;
        }
        (*out)[i] = (uint8_t)((hi << 4) | lo);
    }
    return 0;
}

static void print_hex(const uint8_t *data, size_t len) {
    static const char hexdigits[] = "0123456789abcdef";
    for (size_t i = 0; i < len; i++) {
        fputc(hexdigits[data[i] >> 4], stdout);
        fputc(hexdigits[data[i] & 15U], stdout);
    }
    fputc('\n', stdout);
}

static uint64_t splitmix64_value(uint64_t value) {
    uint64_t z = value + UINT64_C(0x9E3779B97F4A7C15);
    z = (z ^ (z >> 30)) * UINT64_C(0xBF58476D1CE4E5B9);
    z = (z ^ (z >> 27)) * UINT64_C(0x94D049BB133111EB);
    return z ^ (z >> 31);
}

static void fill_message_from_seed(uint8_t *out, size_t out_len, uint64_t seed) {
    uint64_t state = seed;
    size_t pos = 0;
    while (pos < out_len) {
        state += UINT64_C(0x9E3779B97F4A7C15);
        uint64_t word = splitmix64_value(state);
        for (size_t j = 0; j < 8U && pos < out_len; j++) {
            out[pos++] = (uint8_t)((word >> (8U * j)) & 0xffU);
        }
    }
}

static int read_file(const char *path, uint8_t **out, size_t *out_len) {
    FILE *fp = fopen(path, "rb");
    if (fp == NULL) {
        perror(path);
        return 1;
    }
    if (fseek(fp, 0, SEEK_END) != 0) {
        fclose(fp);
        return 1;
    }
    long size = ftell(fp);
    if (size < 0) {
        fclose(fp);
        return 1;
    }
    rewind(fp);
    *out_len = (size_t)size;
    *out = (uint8_t *)malloc(*out_len ? *out_len : 1U);
    if (*out == NULL) {
        fclose(fp);
        return 1;
    }
    if (fread(*out, 1, *out_len, fp) != *out_len) {
        free(*out);
        fclose(fp);
        return 1;
    }
    fclose(fp);
    return 0;
}

static int cmd_hash(int argc, char **argv) {
    uint8_t *data = NULL;
    size_t data_len = 0;
    uint8_t digest[TRICUBE_DIGEST_BYTES];
    tricube_hash_variant variant = TRICUBE_HASH_BASELINE;
    const char *hex = NULL;
    const char *file_path = NULL;
    int rc;
    for (int i = 2; i < argc; i++) {
        if (strcmp(argv[i], "--hex") == 0 && i + 1 < argc) {
            hex = argv[++i];
        } else if (strcmp(argv[i], "--variant") == 0 && i + 1 < argc) {
            if (tricube_hash_variant_from_name(argv[++i], &variant) != TRICUBE_OK) {
                fprintf(stderr, "invalid hash variant; expected baseline, hashfast1024, or hashfast1024r6\n");
                return 2;
            }
        } else if (argv[i][0] != '-' && file_path == NULL) {
            file_path = argv[i];
        } else {
            return 2;
        }
    }
    if ((hex == NULL && file_path == NULL) || (hex != NULL && file_path != NULL)) {
        return 2;
    }
    if (file_path != NULL) {
        if (read_file(file_path, &data, &data_len) != 0) {
            return 2;
        }
    } else if (parse_hex(hex, &data, &data_len) != 0) {
        fprintf(stderr, "invalid hex input\n");
        return 2;
    }
    rc = tricube_hash_with_variant(data, data_len, digest, variant);
    free(data);
    if (rc != TRICUBE_OK) {
        return rc;
    }
    print_hex(digest, sizeof(digest));
    return 0;
}

static int cmd_xof(int argc, char **argv) {
    const char *hex = NULL;
    size_t out_len = 0;
    tricube_hash_variant variant = TRICUBE_HASH_BASELINE;
    for (int i = 2; i < argc; i++) {
        if (strcmp(argv[i], "--hex") == 0 && i + 1 < argc) {
            hex = argv[++i];
        } else if (strcmp(argv[i], "--bytes") == 0 && i + 1 < argc) {
            out_len = (size_t)parse_u64(argv[++i], "bytes");
        } else if (strcmp(argv[i], "--variant") == 0 && i + 1 < argc) {
            if (tricube_hash_variant_from_name(argv[++i], &variant) != TRICUBE_OK) {
                fprintf(stderr, "invalid hash variant; expected baseline, hashfast1024, or hashfast1024r6\n");
                return 2;
            }
        } else {
            return 2;
        }
    }
    if (hex == NULL || out_len == 0) {
        return 2;
    }
    uint8_t *data = NULL;
    size_t data_len = 0;
    if (parse_hex(hex, &data, &data_len) != 0) {
        fprintf(stderr, "invalid hex input\n");
        return 2;
    }
    uint8_t *out = (uint8_t *)malloc(out_len);
    if (out == NULL) {
        free(data);
        return 2;
    }
    int rc = tricube_xof_with_variant(data, data_len, out, out_len, variant);
    free(data);
    if (rc != TRICUBE_OK) {
        free(out);
        return rc;
    }
    print_hex(out, out_len);
    free(out);
    return 0;
}

static int cmd_digest_stream(int argc, char **argv) {
    uint64_t seed = 123;
    uint64_t messages = 0;
    size_t message_bytes = 64;
    const char *out_path = NULL;
    tricube_hash_variant variant = TRICUBE_HASH_BASELINE;
    for (int i = 2; i < argc; i++) {
        if (strcmp(argv[i], "--seed") == 0 && i + 1 < argc) {
            seed = parse_u64(argv[++i], "seed");
        } else if (strcmp(argv[i], "--messages") == 0 && i + 1 < argc) {
            messages = parse_u64(argv[++i], "messages");
        } else if (strcmp(argv[i], "--message-bytes") == 0 && i + 1 < argc) {
            message_bytes = (size_t)parse_u64(argv[++i], "message-bytes");
        } else if (strcmp(argv[i], "--out") == 0 && i + 1 < argc) {
            out_path = argv[++i];
        } else if (strcmp(argv[i], "--variant") == 0 && i + 1 < argc) {
            if (tricube_hash_variant_from_name(argv[++i], &variant) != TRICUBE_OK) {
                fprintf(stderr, "invalid hash variant; expected baseline, hashfast1024, or hashfast1024r6\n");
                return 2;
            }
        } else {
            return 2;
        }
    }
    if (messages == 0 || message_bytes == 0 || out_path == NULL) {
        return 2;
    }
    FILE *out = strcmp(out_path, "-") == 0 ? stdout : fopen(out_path, "wb");
    if (out == NULL) {
        perror(out_path);
        return 2;
    }
    uint8_t *message = (uint8_t *)malloc(message_bytes);
    if (message == NULL) {
        if (out != stdout) {
            fclose(out);
        }
        return 2;
    }
    uint8_t digest[TRICUBE_DIGEST_BYTES];
    int rc = TRICUBE_OK;
    for (uint64_t i = 0; i < messages; i++) {
        fill_message_from_seed(message, message_bytes, seed + i);
        rc = tricube_hash_with_variant(message, message_bytes, digest, variant);
        if (rc != TRICUBE_OK || fwrite(digest, 1, sizeof(digest), out) != sizeof(digest)) {
            rc = rc == TRICUBE_OK ? TRICUBE_ERR_IO : rc;
            break;
        }
    }
    free(message);
    if (out != stdout) {
        fclose(out);
    }
    return rc == TRICUBE_OK ? 0 : rc;
}

static int cmd_stream(int argc, char **argv) {
    uint64_t seed = 0;
    uint64_t n_bytes = 0;
    const char *out_path = NULL;
    int unbounded = 0;
    tricube_stream_variant variant = TRICUBE_STREAM_BASELINE;
    for (int i = 2; i < argc; i++) {
        if (strcmp(argv[i], "--seed") == 0 && i + 1 < argc) {
            seed = parse_u64(argv[++i], "seed");
        } else if (strcmp(argv[i], "--bytes") == 0 && i + 1 < argc) {
            n_bytes = parse_u64(argv[++i], "bytes");
        } else if (strcmp(argv[i], "--out") == 0 && i + 1 < argc) {
            out_path = argv[++i];
        } else if (strcmp(argv[i], "--unbounded") == 0) {
            unbounded = 1;
        } else if (strcmp(argv[i], "--variant") == 0 && i + 1 < argc) {
            if (tricube_stream_variant_from_name(argv[++i], &variant) != TRICUBE_OK) {
                fprintf(stderr, "invalid stream variant; expected baseline, fast8x, fast8x384mix, fast8x512mix, fast8x768mix, or fast8x1024mix\n");
                return 2;
            }
        } else {
            return 2;
        }
    }
    if ((!unbounded && n_bytes == 0) || out_path == NULL) {
        return 2;
    }
    if (unbounded && strcmp(out_path, "-") != 0) {
        fprintf(stderr, "--unbounded is only allowed with --out -\n");
        return 2;
    }
    FILE *out = strcmp(out_path, "-") == 0 ? stdout : fopen(out_path, "wb");
    if (out == NULL) {
        perror(out_path);
        return 2;
    }
    int rc = unbounded ? tricube_stream_write_unbounded(out, seed, variant) : tricube_stream_write_variant(out, seed, n_bytes, variant);
    if (out != stdout) {
        fclose(out);
    }
    return rc == TRICUBE_OK ? 0 : rc;
}

static int cmd_vectors(void) {
    const char *messages[] = {"", "abc", "TriCube"};
    printf("{\n  \"algorithm\": \"TriCube\",\n  \"hash_vectors\": [\n");
    for (size_t i = 0; i < 3; i++) {
        char digest[TRICUBE_HEX_BYTES];
        tricube_hexdigest((const uint8_t *)messages[i], strlen(messages[i]), digest);
        printf("    {\"message_ascii\": \"%s\", \"digest_hex\": \"%s\"}%s\n",
               messages[i], digest, i + 1 < 3 ? "," : "");
    }
    printf("  ]\n}\n");
    return 0;
}

int main(int argc, char **argv) {
    if (argc < 2) {
        usage(argv[0]);
        return 2;
    }
    if (strcmp(argv[1], "self-test") == 0) {
        int rc = tricube_self_test();
        if (rc == TRICUBE_OK) {
            fprintf(stderr, "TriCube self-test passed\n");
            return 0;
        }
        fprintf(stderr, "TriCube self-test failed\n");
        return rc;
    }
    if (strcmp(argv[1], "vectors") == 0) {
        return cmd_vectors();
    }
    if (strcmp(argv[1], "hash") == 0) {
        int rc = cmd_hash(argc, argv);
        if (rc == 2) usage(argv[0]);
        return rc;
    }
    if (strcmp(argv[1], "xof") == 0) {
        int rc = cmd_xof(argc, argv);
        if (rc == 2) usage(argv[0]);
        return rc;
    }
    if (strcmp(argv[1], "digest-stream") == 0) {
        int rc = cmd_digest_stream(argc, argv);
        if (rc == 2) usage(argv[0]);
        return rc;
    }
    if (strcmp(argv[1], "stream") == 0) {
        int rc = cmd_stream(argc, argv);
        if (rc == 2) usage(argv[0]);
        return rc;
    }
    usage(argv[0]);
    return 2;
}
