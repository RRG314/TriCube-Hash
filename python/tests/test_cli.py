from __future__ import annotations

import subprocess
import sys


def test_python_cli_hash_hex() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "tricube.cli", "hash", "--hex", "616263"],
        check=True,
        text=True,
        capture_output=True,
    )
    assert proc.stdout.strip() == "779403a9c748fc3213493953fc17309367b37161c00dc19059c14db63774e11e"

