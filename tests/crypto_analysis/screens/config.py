"""Shared screen configuration."""

from __future__ import annotations


PROFILE_DEFAULTS = {
    "quick": {
        "samples": 64,
        "algebraic_vars": 8,
        "algebraic_bits": 32,
        "collision_samples": 512,
        "near_pairs": 256,
        "stream_bytes": 1 << 20,
        "bm_bits": 4096,
    },
    "standard": {
        "samples": 256,
        "algebraic_vars": 10,
        "algebraic_bits": 64,
        "collision_samples": 4096,
        "near_pairs": 2048,
        "stream_bytes": 16 << 20,
        "bm_bits": 16384,
    },
}

DELTA_CLASSES = {
    "single_bit": [1 << b for b in (0, 1, 7, 8, 31, 32, 63)],
    "single_byte": [0xFF << (8 * b) for b in (0, 1, 3, 7)],
    "single_64_word": [0xFFFFFFFFFFFFFFFF],
    "all_low_bit_mask": [0x0101010101010101],
    "checkerboard_mask": [0xAA55AA55AA55AA55, 0x55AA55AA55AA55AA],
    "high_bit_mask": [0x8080808080808080],
    "adjacent_bit_mask": [(1 << b) | (1 << (b + 1)) for b in (0, 1, 7, 15, 31, 47, 62)],
}

ROTATIONS = [1, 2, 3, 4, 5, 7, 8, 13, 16, 17, 31, 32, 33, 47, 63]
PREFIX_BITS = [16, 24, 32, 40, 48, 64]

