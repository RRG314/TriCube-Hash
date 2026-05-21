#!/usr/bin/env python3
"""Run TriCube black-box development screens.

The screens in this file are reproducible engineering gates. They do not model
TriCube internals and do not replace formal cryptanalysis.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import math
from pathlib import Path
import sys
from typing import Any

from common import (
    STATUS_BLOCKED,
    STATUS_FAIL,
    STATUS_NOT_RUN,
    STATUS_PASS,
    STATUS_WARN,
    anf_degree,
    berlekamp_massey_binary,
    bit_position_counts64,
    bytes_to_bits,
    choose2,
    command_exists,
    count_repeated_blocks,
    digest32,
    environment,
    group_by_status,
    hamming_bytes,
    markdown_table,
    mean,
    parse_variants,
    rng_for,
    rotate_words64,
    rotl64,
    stdev,
    stream_bytes,
    write_csv,
    write_json,
    write_summary_md,
    xor_bytes,
    zscore_ones,
)


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


def status_for_diff(mean_bits: float, max_bias: float, repeated_top: int) -> str:
    if mean_bits < 96 or mean_bits > 160 or repeated_top > 4:
        return STATUS_FAIL
    if mean_bits < 112 or mean_bits > 144 or max_bias > 0.25 or repeated_top > 1:
        return STATUS_WARN
    return STATUS_PASS


def differential_screen(variants: list[str], samples: int, seed: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    rng = rng_for(seed)
    random_deltas = {
        "random_low_weight": [sum(1 << rng.randrange(64) for _ in range(3)) for _ in range(4)],
        "random_medium_weight": [rng.getrandbits(64) & rng.getrandbits(64) for _ in range(4)],
        "random_full_weight": [rng.getrandbits(64) or 1 for _ in range(4)],
    }
    all_classes = {**DELTA_CLASSES, **random_deltas}
    for variant in variants:
        for name, deltas in all_classes.items():
            distances: list[int] = []
            repeated = Counter()
            bit_flips = [0] * 256
            for idx in range(samples):
                base_seed = rng.getrandbits(64)
                delta = deltas[idx % len(deltas)] & 0xFFFFFFFFFFFFFFFF
                a = digest32(variant, base_seed)
                b = digest32(variant, base_seed ^ delta)
                diff = xor_bytes(a, b)
                distances.append(hamming_bytes(a, b))
                repeated[diff] += 1
                for bit_idx, bit in enumerate(bytes_to_bits(diff)):
                    bit_flips[bit_idx] += bit
            max_bias = max(abs(count / samples - 0.5) for count in bit_flips)
            chi2 = sum(((count - samples / 2) ** 2) / (samples / 2) for count in bit_flips)
            top = repeated.most_common(1)[0][1] if repeated else 0
            m = mean([float(x) for x in distances])
            rows.append(
                {
                    "screen": "black-box differential diffusion probe",
                    "variant": variant,
                    "delta_class": name,
                    "samples": samples,
                    "mean_hamming": round(m, 4),
                    "min_hamming": min(distances),
                    "max_hamming": max(distances),
                    "max_bit_bias": round(max_bias, 6),
                    "chi_square_bit_flips": round(chi2, 3),
                    "repeated_output_differences": sum(v - 1 for v in repeated.values() if v > 1),
                    "top_repeated_difference_count": top,
                    "status": status_for_diff(m, max_bias, top),
                }
            )
    return rows


def rotational_screen(variants: list[str], samples: int, seed: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    rng = rng_for(seed ^ 0xA55A)
    for variant in variants:
        for rotation in ROTATIONS:
            distances: list[int] = []
            exact = 0
            bit_flips = [0] * 256
            for _ in range(samples):
                base_seed = rng.getrandbits(64)
                a = digest32(variant, base_seed)
                b = digest32(variant, rotl64(base_seed, rotation))
                expected = rotate_words64(a, rotation)
                diff = xor_bytes(expected, b)
                if diff == b"\0" * len(diff):
                    exact += 1
                distances.append(hamming_bytes(expected, b))
                for bit_idx, bit in enumerate(bytes_to_bits(diff)):
                    bit_flips[bit_idx] += bit
            m = mean([float(x) for x in distances])
            max_bias = max(abs(count / samples - 0.5) for count in bit_flips)
            status = STATUS_FAIL if exact else (STATUS_WARN if m < 112 or m > 144 or max_bias > 0.25 else STATUS_PASS)
            rows.append(
                {
                    "screen": "black-box rotational relation probe",
                    "variant": variant,
                    "rotation": rotation,
                    "samples": samples,
                    "mean_rotational_distance": round(m, 4),
                    "min_distance": min(distances),
                    "max_distance": max(distances),
                    "max_bit_bias": round(max_bias, 6),
                    "exact_rotational_relations": exact,
                    "z_score_mean_distance": round((m - 128.0) / math.sqrt(256 * 0.25 / samples), 4),
                    "status": status,
                }
            )
    return rows


def algebraic_screen(variants: list[str], variable_count: int, output_bits: int, seed: int) -> list[dict[str, Any]]:
    if variable_count > 12:
        raise ValueError("variable_count above 12 is intentionally blocked for this black-box screen")
    rows: list[dict[str, Any]] = []
    positions = [((i * 13) % 64) for i in range(variable_count)]
    assignments = 1 << variable_count
    for variant in variants:
        outputs = []
        for mask in range(assignments):
            s = seed
            for i, pos in enumerate(positions):
                if (mask >> i) & 1:
                    s ^= 1 << pos
            outputs.append(digest32(variant, s))
        degrees: list[int] = []
        for bit_idx in range(output_bits):
            table = []
            byte_idx = bit_idx // 8
            bit_in_byte = bit_idx % 8
            for out in outputs:
                table.append((out[byte_idx] >> bit_in_byte) & 1)
            degrees.append(anf_degree(table))
        low = sum(1 for d in degrees if d <= max(0, variable_count - 2))
        max_degree = max(degrees) if degrees else 0
        status = STATUS_WARN if low > 0 or max_degree < variable_count - 1 else STATUS_PASS
        rows.append(
            {
                "screen": "small black-box algebraic degree screen",
                "variant": variant,
                "variables": variable_count,
                "assignments": assignments,
                "output_bits": output_bits,
                "variable_positions": ",".join(str(p) for p in positions),
                "min_degree": min(degrees) if degrees else 0,
                "mean_degree": round(mean([float(x) for x in degrees]), 4),
                "max_degree": max_degree,
                "low_degree_outputs": low,
                "status": status,
            }
        )
    return rows


def collision_screen(variants: list[str], samples: int, near_pairs: int, seed: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    rng = rng_for(seed ^ 0xC0111510)
    for variant in variants:
        outputs = [digest32(variant, rng.getrandbits(64)) for _ in range(samples)]
        full_counts = Counter(outputs)
        full_collisions = sum(choose2(c) for c in full_counts.values() if c > 1)
        rows.append(
            {
                "screen": "collision/birthday sanity check",
                "variant": variant,
                "kind": "full_digest",
                "samples": samples,
                "prefix_bits": 256,
                "observed_collision_pairs": full_collisions,
                "expected_collision_pairs": "near 0",
                "observed_expected_ratio": "",
                "status": STATUS_FAIL if full_collisions else STATUS_PASS,
            }
        )
        for bits in PREFIX_BITS:
            prefix_bytes = (bits + 7) // 8
            shift = prefix_bytes * 8 - bits
            prefixes = []
            for out in outputs:
                value = int.from_bytes(out[:prefix_bytes], "big")
                prefixes.append(value >> shift if shift else value)
            counts = Counter(prefixes)
            observed = sum(choose2(c) for c in counts.values() if c > 1)
            expected = samples * (samples - 1) / (2 * (2**bits))
            ratio = observed / expected if expected else 0.0
            # Prefix birthday counts are noisy at small expected counts.  In
            # the quick profile, a 16-bit prefix has lambda ~= 2 collision
            # pairs, so observing zero is ordinary Poisson variation rather
            # than a useful warning.  Flag only large deviations where the
            # expected count is high enough to make a compact screen meaningful.
            if expected >= 10:
                sigma = math.sqrt(expected)
                status = STATUS_WARN if abs(observed - expected) > max(5.0 * sigma, 10.0) else STATUS_PASS
            else:
                status = STATUS_WARN if observed > max(10, expected * 10.0) else STATUS_PASS
            rows.append(
                {
                    "screen": "collision/birthday sanity check",
                    "variant": variant,
                    "kind": "prefix",
                    "samples": samples,
                    "prefix_bits": bits,
                    "observed_collision_pairs": observed,
                    "expected_collision_pairs": round(expected, 4),
                    "observed_expected_ratio": round(ratio, 4) if expected else "",
                    "status": status,
                }
            )
        distances = []
        for _ in range(near_pairs):
            a, b = rng.sample(outputs, 2)
            distances.append(hamming_bytes(a, b))
        rows.append(
            {
                "screen": "near-collision sanity check",
                "variant": variant,
                "kind": "sampled_pair_hamming",
                "samples": near_pairs,
                "prefix_bits": "",
                "observed_collision_pairs": "",
                "expected_collision_pairs": "",
                "observed_expected_ratio": "",
                "min_hamming": min(distances),
                "mean_hamming": round(mean([float(x) for x in distances]), 4),
                "max_hamming": max(distances),
                "status": STATUS_WARN if min(distances) < 80 else STATUS_PASS,
            }
        )
    return rows


def overlap_fork_screen(variants: list[str], stream_size: int, seed: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seed_set = [seed, seed + 1, seed ^ 1, seed ^ (1 << 63)]
    for variant in variants:
        streams = {s: stream_bytes(variant, s, stream_size) for s in seed_set}
        for block_size in (16, 32, 64):
            within = sum(count_repeated_blocks(data, block_size) for data in streams.values())
            cross = 0
            same_position = 0
            seen_by_seed: dict[bytes, int] = {}
            for s, data in streams.items():
                for pos in range(0, len(data) - block_size + 1, block_size):
                    block = data[pos : pos + block_size]
                    if block in seen_by_seed and seen_by_seed[block] != s:
                        cross += 1
                    else:
                        seen_by_seed[block] = s
            first = streams[seed]
            second = streams[seed + 1]
            for pos in range(0, min(len(first), len(second)) - block_size + 1, block_size):
                if first[pos : pos + block_size] == second[pos : pos + block_size]:
                    same_position += 1
            prefix_hamming = hamming_bytes(first[:1024], second[:1024])
            status = STATUS_FAIL if within or cross or same_position else STATUS_PASS
            rows.append(
                {
                    "screen": "overlap/fork stream uniqueness screen",
                    "variant": variant,
                    "stream_bytes_per_seed": stream_size,
                    "seeds": ",".join(str(s) for s in seed_set),
                    "block_size": block_size,
                    "within_stream_repeated_blocks": within,
                    "cross_stream_overlaps": cross,
                    "same_position_equal_blocks": same_position,
                    "adjacent_seed_prefix_hamming_1024B": prefix_hamming,
                    "status": status,
                }
            )
    return rows


def state_recovery_screen(variants: list[str], stream_size: int, bm_bits: int, seed: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for variant in variants:
        data = stream_bytes(variant, seed, stream_size)
        half = len(data) // 2
        train = data[:half]
        test = data[half:]
        most_common_byte = Counter(train).most_common(1)[0][0]
        next_byte_acc = sum(1 for b in test if b == most_common_byte) / len(test)
        transitions: dict[int, Counter[int]] = defaultdict(Counter)
        for a, b in zip(train, train[1:]):
            transitions[a][b] += 1
        hits = 0
        total = 0
        for a, b in zip(test, test[1:]):
            pred = transitions.get(a)
            if pred:
                hits += pred.most_common(1)[0][0] == b
            total += 1
        ngram_acc = hits / total if total else 0.0
        bit_hits = 0
        bit_total = 0
        train_bits = bytes_to_bits(train)
        test_bits = bytes_to_bits(test)
        majority = 1 if sum(train_bits) >= len(train_bits) / 2 else 0
        for bit in test_bits:
            bit_hits += bit == majority
            bit_total += 1
        bit_acc = bit_hits / bit_total if bit_total else 0.0
        lc_ratios = []
        for bit_pos in (0, 1, 7):
            seq = [((byte >> bit_pos) & 1) for byte in data[:bm_bits]]
            lc_ratios.append(berlekamp_massey_binary(seq) / len(seq))
        status = STATUS_WARN if next_byte_acc > 0.02 or ngram_acc > 0.02 or abs(bit_acc - 0.5) > 0.02 else STATUS_PASS
        rows.append(
            {
                "screen": "black-box state-recovery/predictability screen",
                "variant": variant,
                "train_bytes": len(train),
                "test_bytes": len(test),
                "next_byte_accuracy": round(next_byte_acc, 6),
                "ngram1_accuracy": round(ngram_acc, 6),
                "random_next_byte_baseline": round(1 / 256, 6),
                "bit_accuracy": round(bit_acc, 6),
                "berlekamp_massey_lc_ratio_min": round(min(lc_ratios), 6),
                "berlekamp_massey_lc_ratio_mean": round(mean(lc_ratios), 6),
                "berlekamp_massey_lc_ratio_max": round(max(lc_ratios), 6),
                "status": status,
            }
        )
    return rows


def low_bit_screen(variants: list[str], stream_size: int, seed: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for variant in variants:
        data = stream_bytes(variant, seed, stream_size)
        n_bytes = len(data)
        byte_lsb = sum(byte & 1 for byte in data)
        word32_count = n_bytes // 4
        word64_count = n_bytes // 8
        word32_lsb = sum(int.from_bytes(data[i * 4 : i * 4 + 4], "little") & 1 for i in range(word32_count))
        word64_lsb = sum(int.from_bytes(data[i * 8 : i * 8 + 8], "little") & 1 for i in range(word64_count))
        low_nibbles = Counter(byte & 0x0F for byte in data)
        expected_nibble = n_bytes / 16
        nibble_chi2 = sum(((low_nibbles[i] - expected_nibble) ** 2) / expected_nibble for i in range(16))
        bit_counts = bit_position_counts64(data[: word64_count * 8])
        bit_z = [abs(zscore_ones(count, word64_count)) for count in bit_counts]
        low_bits = [(byte & 1) for byte in data]
        transitions = Counter((low_bits[i], low_bits[i + 1]) for i in range(len(low_bits) - 1))
        high_bits = [(byte >> 7) & 1 for byte in data]
        low_lag1 = lag_correlation(low_bits)
        high_lag1 = lag_correlation(high_bits)
        max_z = max(
            abs(zscore_ones(byte_lsb, n_bytes)),
            abs(zscore_ones(word32_lsb, word32_count)),
            abs(zscore_ones(word64_lsb, word64_count)),
            max(bit_z) if bit_z else 0.0,
        )
        status = STATUS_WARN if max_z > 6.0 or nibble_chi2 > 45.0 or abs(low_lag1) > 0.01 else STATUS_PASS
        rows.append(
            {
                "screen": "low-bit diagnostic screen",
                "variant": variant,
                "bytes": n_bytes,
                "byte_lsb_fraction": round(byte_lsb / n_bytes, 8),
                "byte_lsb_z": round(zscore_ones(byte_lsb, n_bytes), 4),
                "word32_lsb_fraction": round(word32_lsb / word32_count, 8),
                "word32_lsb_z": round(zscore_ones(word32_lsb, word32_count), 4),
                "word64_lsb_fraction": round(word64_lsb / word64_count, 8),
                "word64_lsb_z": round(zscore_ones(word64_lsb, word64_count), 4),
                "low_nibble_chi_square": round(nibble_chi2, 4),
                "max_bit_position_z64": round(max(bit_z), 4),
                "low_bit_transition_00": transitions[(0, 0)],
                "low_bit_transition_01": transitions[(0, 1)],
                "low_bit_transition_10": transitions[(1, 0)],
                "low_bit_transition_11": transitions[(1, 1)],
                "low_bit_lag1_corr": round(low_lag1, 8),
                "high_bit_lag1_corr": round(high_lag1, 8),
                "status": status,
            }
        )
    return rows


def lag_correlation(bits: list[int]) -> float:
    if len(bits) < 2:
        return 0.0
    xs = bits[:-1]
    ys = bits[1:]
    mx = mean([float(x) for x in xs])
    my = mean([float(y) for y in ys])
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    denx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    deny = math.sqrt(sum((y - my) ** 2 for y in ys))
    return num / (denx * deny) if denx and deny else 0.0


def external_status_rows(variants: list[str]) -> list[dict[str, Any]]:
    tools = [
        ("PractRand", "RNG_test", "PractRand 256 MiB quick screen"),
        ("SmokeRand", "smokerand", "SmokeRand express"),
        ("TestU01 SmallCrush", "testu01_stdin32", "SmallCrush stdin32 wrapper"),
        ("Dieharder", "dieharder", "Dieharder full battery"),
        ("NIST STS", "assess", "NIST STS assess binary"),
    ]
    rows = []
    for variant in variants:
        for name, binary, purpose in tools:
            exists = command_exists(binary)
            rows.append(
                {
                    "screen": "external statistical battery",
                    "variant": variant,
                    "tool": name,
                    "binary": binary,
                    "purpose": purpose,
                    "status": STATUS_NOT_RUN if exists else STATUS_BLOCKED,
                    "notes": "tool detected but not launched by this quick internal run" if exists else "external tool not installed or not on PATH",
                }
            )
    return rows


def write_outputs(out_dir: Path, rows_by_name: dict[str, list[dict[str, Any]]], metadata: dict[str, Any]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    all_rows = [row for rows in rows_by_name.values() for row in rows]
    write_json(out_dir / "summary.json", {"metadata": metadata, "status_counts": group_by_status(all_rows), "screens": rows_by_name})
    for name, rows in rows_by_name.items():
        write_csv(out_dir / f"{name}.csv", rows)
        write_summary_md(
            out_dir / f"{name}.md",
            title=name.replace("_", " ").title(),
            intro="Generated by TriCube black-box development screens. PASS means no issue was detected under this budget; it is not a security proof.",
            rows=rows,
        )
    write_csv(out_dir / "all_screens.csv", all_rows)
    md = [
        "# TriCube Crypto-Analysis Screen Summary",
        "",
        "These tests are development gates. They can find obvious failures or warning patterns, but they do not replace white-box cryptanalysis.",
        "",
        "## Metadata",
        "",
        markdown_table([{k: v for k, v in metadata.items() if k != "command"}]),
        "## Status Counts",
        "",
        markdown_table([group_by_status(all_rows)]),
    ]
    for name, rows in rows_by_name.items():
        md.extend([f"## {name.replace('_', ' ').title()}", "", markdown_table(rows)])
    (out_dir / "summary.md").write_text("\n".join(md), encoding="utf-8")


def run(profile: str, variants: list[str], out_dir: Path, seed: int) -> dict[str, list[dict[str, Any]]]:
    defaults = PROFILE_DEFAULTS[profile]
    rows_by_name = {
        "differential_screen": differential_screen(variants, defaults["samples"], seed),
        "rotational_screen": rotational_screen(variants, defaults["samples"], seed),
        "algebraic_degree_screen": algebraic_screen(variants, defaults["algebraic_vars"], defaults["algebraic_bits"], seed),
        "collision_screen": collision_screen(variants, defaults["collision_samples"], defaults["near_pairs"], seed),
        "overlap_fork_screen": overlap_fork_screen(variants, defaults["stream_bytes"], seed),
        "state_recovery_screen": state_recovery_screen(variants, defaults["stream_bytes"], defaults["bm_bits"], seed),
        "low_bit_diagnostics": low_bit_screen(variants, defaults["stream_bytes"], seed),
        "external_batteries": external_status_rows(variants),
    }
    metadata = environment()
    metadata.update({"profile": profile, "variants": variants, "seed": seed, **defaults})
    write_outputs(out_dir, rows_by_name, metadata)
    return rows_by_name


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run TriCube black-box development screens.")
    parser.add_argument("--profile", choices=sorted(PROFILE_DEFAULTS), default="quick")
    parser.add_argument("--variants", default="baseline,fast8x")
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    variants = parse_variants(args.variants)
    rows = run(args.profile, variants, args.out, args.seed)
    counts = group_by_status([row for screen_rows in rows.values() for row in screen_rows])
    print(f"wrote {args.out}")
    print(counts)
    return 0 if counts.get(STATUS_FAIL, 0) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
