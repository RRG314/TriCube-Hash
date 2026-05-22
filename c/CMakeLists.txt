cmake_minimum_required(VERSION 3.16)
project(tricube C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

add_library(tricube_core src/tricube.c src/tricube_variants.c src/tricube_fast8x.c)
target_include_directories(tricube_core PUBLIC include)
target_link_libraries(tricube_core PUBLIC m)

add_executable(tricube src/tricube_cli.c)
target_link_libraries(tricube PRIVATE tricube_core)

add_executable(test_vectors tests/test_vectors.c)
target_link_libraries(test_vectors PRIVATE tricube_core)

add_executable(test_stream tests/test_stream.c)
target_link_libraries(test_stream PRIVATE tricube_core)

add_executable(test_stream_variants tests/test_stream_variants.c)
target_link_libraries(test_stream_variants PRIVATE tricube_core)

add_executable(test_hash_variants tests/test_hash_variants.c)
target_link_libraries(test_hash_variants PRIVATE tricube_core)

add_executable(bench_hash_variants benchmarks/bench_hash_variants.c)
target_link_libraries(bench_hash_variants PRIVATE tricube_core)

enable_testing()
add_test(NAME tricube_self_test COMMAND tricube self-test)
add_test(NAME tricube_vectors COMMAND test_vectors)
add_test(NAME tricube_stream COMMAND test_stream)
add_test(NAME tricube_stream_variants COMMAND test_stream_variants)
add_test(NAME tricube_hash_variants COMMAND test_hash_variants)
