"""Optional helpers for locating the standalone C TriCube CLI.

The Python package ships with a reference implementation so it does not require
the C binary at import time. Tests and examples may use this module to call a
locally built CLI when one is present.
"""

from __future__ import annotations

from pathlib import Path
import shutil


def find_cli() -> Path | None:
    """Return a usable TriCube CLI path if one is available."""

    exe = shutil.which("tricube")
    if exe:
        return Path(exe)
    root = Path(__file__).resolve().parents[4]
    candidate = root / "c" / "build" / "tricube"
    if candidate.exists():
        return candidate
    return None

