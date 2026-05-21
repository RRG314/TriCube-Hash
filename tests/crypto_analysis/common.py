"""Shared helpers for TriCube black-box development screens.

These helpers intentionally treat TriCube as a black box. They are useful for
finding obvious warning patterns in stream output. They are not formal
cryptanalysis and do not model the internal round function.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
import csv
import json
import math
import os
from pathlib import Path
import platform
import random
import shutil
import subprocess
import sys
from functools import lru_cache
from typing import Any


STATUS_PASS = "PASS"
STATUS_WARN = "WARN"
STATUS_FAIL = "FAIL"
STATUS_BLOCKED = "BLOCKED"
STATUS_NOT_RUN = "NOT_RUN"

REPO_ROOT = Path(__file__).resolve().parents[2]
C_CLI = REPO_ROOT / "c" / "build" / "tricube"


@dataclass(frozen=True)
class Variant:
    name: str
    cli_name: str


VARIANTS = {
    "baseline": Variant("baseline", "baseline"),
    "fast8x": Variant("fast8x", "fast8x"),
}


def run_text(args: list[str], *, cwd: Path = REPO_ROOT, timeout: int = 30) -> str:
    try:
        return subprocess.check_output(args, cwd=cwd, text=True, stderr=subprocess.DEVNULL, timeout=timeout).strip()
    except Exception:
        return ""


def git_branch() -> str:
    return run_text(["git", "rev-parse", "--abbrev-ref", "HEAD"]) or "UNKNOWN"


def git_commit() -> str:
    return run_text(["git", "rev-parse", "HEAD"]) or "UNKNOWN"


def environment(command: list[str] | None = None) -> dict[str, Any]:
    return {
        "date_utc": datetime.now(timezone.utc).isoformat(),
        "git_branch": git_branch(),
        "git_commit": git_commit(),
        "machine": platform.node(),
        "platform": platform.platform(),
        "processor": platform.processor(),
        "python_version": sys.version.replace("\n", " "),
        "command": command or sys.argv,
    }


def ensure_cli() -> None:
    if C_CLI.exists():
        return
    subprocess.check_call(["make", "-C", "c", "all"], cwd=REPO_ROOT)


@lru_cache(maxsize=8192)
def stream_bytes(variant: str, seed: int, n_bytes: int) -> bytes:
    ensure_cli()
    if variant not in VARIANTS:
        raise ValueError(f"unknown variant: {variant}")
    cmd = [
        str(C_CLI),
        "stream",
        "--seed",
        str(seed & 0xFFFFFFFFFFFFFFFF),
        "--bytes",
        str(n_bytes),
        "--out",
        "-",
    ]
    if variant != "baseline":
        cmd.extend(["--variant", VARIANTS[variant].cli_name])
    return subprocess.check_output(cmd, cwd=REPO_ROOT)


def digest32(variant: str, seed: int) -> bytes:
    """Return the first 32 bytes of deterministic stream output.

    This is a stream-output screen, not a hash-mode screen. It exists so the
    baseline and fast8x stream variants can be compared under the same black-box
    input/output interface.
    """

    return stream_bytes(variant, seed, 32)


def hamming_bytes(a: bytes, b: bytes) -> int:
    return sum((x ^ y).bit_count() for x, y in zip(a, b))


def xor_bytes(a: bytes, b: bytes) -> bytes:
    return bytes(x ^ y for x, y in zip(a, b))


def rotl64(x: int, r: int) -> int:
    r &= 63
    return ((x << r) | (x >> (64 - r))) & 0xFFFFFFFFFFFFFFFF


def rotate_words64(data: bytes, r: int) -> bytes:
    out = bytearray()
    for off in range(0, len(data), 8):
        word = int.from_bytes(data[off : off + 8].ljust(8, b"\0"), "little")
        out.extend(rotl64(word, r).to_bytes(8, "little"))
    return bytes(out[: len(data)])


def bytes_to_bits(data: bytes) -> list[int]:
    return [(byte >> bit) & 1 for byte in data for bit in range(8)]


def berlekamp_massey_binary(bits: list[int]) -> int:
    """Return binary linear complexity using the Berlekamp-Massey algorithm."""

    n = len(bits)
    c = [0] * n
    b = [0] * n
    c[0] = 1
    b[0] = 1
    length = 0
    m = -1
    for idx in range(n):
        discrepancy = bits[idx]
        for j in range(1, length + 1):
            discrepancy ^= c[j] & bits[idx - j]
        if discrepancy:
            t = c[:]
            shift = idx - m
            for j in range(0, n - shift):
                c[j + shift] ^= b[j]
            if 2 * length <= idx:
                length = idx + 1 - length
                m = idx
                b = t
    return length


def anf_degree(truth: list[int]) -> int:
    """Compute ANF degree from a truth table whose length is a power of two."""

    coeff = truth[:]
    n = len(coeff).bit_length() - 1
    for i in range(n):
        bit = 1 << i
        for mask in range(len(coeff)):
            if mask & bit:
                coeff[mask] ^= coeff[mask ^ bit]
    degree = 0
    for mask, value in enumerate(coeff):
        if value:
            degree = max(degree, mask.bit_count())
    return degree


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def stdev(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mu = mean(values)
    return math.sqrt(sum((x - mu) ** 2 for x in values) / (len(values) - 1))


def choose2(n: int) -> int:
    return n * (n - 1) // 2


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields: list[str] = []
    seen = set()
    for row in rows:
        for key in row:
            if key not in seen:
                fields.append(key)
                seen.add(key)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def markdown_table(rows: list[dict[str, Any]], fields: list[str] | None = None) -> str:
    if not rows:
        return "_No rows._\n"
    fields = fields or list(rows[0].keys())
    lines = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(f, "")) for f in fields) + " |")
    return "\n".join(lines) + "\n"


def write_summary_md(path: Path, title: str, intro: str, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = f"# {title}\n\n{intro.strip()}\n\n{markdown_table(rows, fields)}"
    path.write_text(text, encoding="utf-8")


def parse_variants(value: str) -> list[str]:
    variants = [v.strip() for v in value.split(",") if v.strip()]
    for variant in variants:
        if variant not in VARIANTS:
            raise ValueError(f"unknown variant {variant!r}; expected one of {sorted(VARIANTS)}")
    return variants


def rng_for(seed: int) -> random.Random:
    return random.Random(seed & 0xFFFFFFFFFFFFFFFF)


def command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def count_repeated_blocks(data: bytes, block_size: int) -> int:
    counts = Counter(data[i : i + block_size] for i in range(0, len(data) - block_size + 1, block_size))
    return sum(count - 1 for count in counts.values() if count > 1)


def bit_position_counts64(data: bytes) -> list[int]:
    counts = [0] * 64
    words = len(data) // 8
    for i in range(words):
        word = int.from_bytes(data[i * 8 : i * 8 + 8], "little")
        for bit in range(64):
            counts[bit] += (word >> bit) & 1
    return counts


def zscore_ones(ones: int, n: int) -> float:
    if n <= 0:
        return 0.0
    return (ones - n / 2.0) / math.sqrt(n / 4.0)


def group_by_status(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for row in rows:
        counts[str(row.get("status", "UNKNOWN"))] += 1
    return dict(sorted(counts.items()))

