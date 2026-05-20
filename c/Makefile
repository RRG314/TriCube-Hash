CC ?= cc
CFLAGS ?= -std=c11 -O3 -Wall -Wextra -pedantic
LDFLAGS ?= -lm

BUILD_DIR := build
INCLUDE := -Iinclude
LIB_OBJ := $(BUILD_DIR)/tricube.o
CLI_OBJ := $(BUILD_DIR)/tricube_cli.o
TEST_VECTOR_OBJ := $(BUILD_DIR)/test_vectors.o
TEST_STREAM_OBJ := $(BUILD_DIR)/test_stream.o

.PHONY: all clean test

all: $(BUILD_DIR)/tricube

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

$(LIB_OBJ): src/tricube.c include/tricube.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) $(INCLUDE) -c src/tricube.c -o $@

$(CLI_OBJ): src/tricube_cli.c include/tricube.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) $(INCLUDE) -c src/tricube_cli.c -o $@

$(BUILD_DIR)/tricube: $(LIB_OBJ) $(CLI_OBJ)
	$(CC) $(CFLAGS) $^ $(LDFLAGS) -o $@

$(TEST_VECTOR_OBJ): tests/test_vectors.c include/tricube.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) $(INCLUDE) -c tests/test_vectors.c -o $@

$(TEST_STREAM_OBJ): tests/test_stream.c include/tricube.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) $(INCLUDE) -c tests/test_stream.c -o $@

$(BUILD_DIR)/test_vectors: $(LIB_OBJ) $(TEST_VECTOR_OBJ)
	$(CC) $(CFLAGS) $^ $(LDFLAGS) -o $@

$(BUILD_DIR)/test_stream: $(LIB_OBJ) $(TEST_STREAM_OBJ)
	$(CC) $(CFLAGS) $^ $(LDFLAGS) -o $@

test: $(BUILD_DIR)/tricube $(BUILD_DIR)/test_vectors $(BUILD_DIR)/test_stream
	$(BUILD_DIR)/tricube self-test
	$(BUILD_DIR)/test_vectors
	$(BUILD_DIR)/test_stream

clean:
	rm -rf $(BUILD_DIR)
