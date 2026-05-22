CC ?= cc
CFLAGS ?= -std=c11 -O3 -Wall -Wextra -pedantic
LDFLAGS ?= -lm

BUILD_DIR := build
INCLUDE := -Iinclude
LIB_OBJ := $(BUILD_DIR)/tricube.o
FAST8X_OBJ := $(BUILD_DIR)/tricube_fast8x.o
CLI_OBJ := $(BUILD_DIR)/tricube_cli.o
TEST_VECTOR_OBJ := $(BUILD_DIR)/test_vectors.o
TEST_STREAM_OBJ := $(BUILD_DIR)/test_stream.o
TEST_STREAM_VARIANTS_OBJ := $(BUILD_DIR)/test_stream_variants.o
TEST_HASH_VARIANTS_OBJ := $(BUILD_DIR)/test_hash_variants.o
BENCH_HASH_VARIANTS_OBJ := $(BUILD_DIR)/bench_hash_variants.o

.PHONY: all clean test

all: $(BUILD_DIR)/tricube

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

$(LIB_OBJ): src/tricube.c include/tricube.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) $(INCLUDE) -c src/tricube.c -o $@

$(FAST8X_OBJ): src/tricube_fast8x.c include/tricube.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) $(INCLUDE) -c src/tricube_fast8x.c -o $@

$(CLI_OBJ): src/tricube_cli.c include/tricube.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) $(INCLUDE) -c src/tricube_cli.c -o $@

$(BUILD_DIR)/tricube: $(LIB_OBJ) $(FAST8X_OBJ) $(CLI_OBJ)
	$(CC) $(CFLAGS) $^ $(LDFLAGS) -o $@

$(TEST_VECTOR_OBJ): tests/test_vectors.c include/tricube.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) $(INCLUDE) -c tests/test_vectors.c -o $@

$(TEST_STREAM_OBJ): tests/test_stream.c include/tricube.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) $(INCLUDE) -c tests/test_stream.c -o $@

$(TEST_STREAM_VARIANTS_OBJ): tests/test_stream_variants.c include/tricube.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) $(INCLUDE) -c tests/test_stream_variants.c -o $@

$(TEST_HASH_VARIANTS_OBJ): tests/test_hash_variants.c include/tricube.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) $(INCLUDE) -c tests/test_hash_variants.c -o $@

$(BENCH_HASH_VARIANTS_OBJ): benchmarks/bench_hash_variants.c include/tricube.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) $(INCLUDE) -c benchmarks/bench_hash_variants.c -o $@

$(BUILD_DIR)/test_vectors: $(LIB_OBJ) $(FAST8X_OBJ) $(TEST_VECTOR_OBJ)
	$(CC) $(CFLAGS) $^ $(LDFLAGS) -o $@

$(BUILD_DIR)/test_stream: $(LIB_OBJ) $(FAST8X_OBJ) $(TEST_STREAM_OBJ)
	$(CC) $(CFLAGS) $^ $(LDFLAGS) -o $@

$(BUILD_DIR)/test_stream_variants: $(LIB_OBJ) $(FAST8X_OBJ) $(TEST_STREAM_VARIANTS_OBJ)
	$(CC) $(CFLAGS) $^ $(LDFLAGS) -o $@

$(BUILD_DIR)/test_hash_variants: $(LIB_OBJ) $(FAST8X_OBJ) $(TEST_HASH_VARIANTS_OBJ)
	$(CC) $(CFLAGS) $^ $(LDFLAGS) -o $@

$(BUILD_DIR)/bench_hash_variants: $(LIB_OBJ) $(FAST8X_OBJ) $(BENCH_HASH_VARIANTS_OBJ)
	$(CC) $(CFLAGS) $^ $(LDFLAGS) -o $@

test: $(BUILD_DIR)/tricube $(BUILD_DIR)/test_vectors $(BUILD_DIR)/test_stream $(BUILD_DIR)/test_stream_variants $(BUILD_DIR)/test_hash_variants
	$(BUILD_DIR)/tricube self-test
	$(BUILD_DIR)/test_vectors
	$(BUILD_DIR)/test_stream
	$(BUILD_DIR)/test_stream_variants
	$(BUILD_DIR)/test_hash_variants

clean:
	rm -rf $(BUILD_DIR)
