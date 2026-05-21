"""Import-path setup for directly executed screen scripts."""

from __future__ import annotations

from pathlib import Path
import sys


CRYPTO_ANALYSIS_DIR = Path(__file__).resolve().parents[1]


def ensure_import_path() -> None:
    path = str(CRYPTO_ANALYSIS_DIR)
    if path not in sys.path:
        sys.path.insert(0, path)

