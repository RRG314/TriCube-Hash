from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

import pytest
import tricube


def test_c_cli_and_python_vectors_agree() -> None:
    root = Path(__file__).resolve().parents[2]
    cli = root / "c" / "build" / "tricube"
    if not cli.exists():
        if shutil.which("make") is None:
            pytest.skip("make is not available for building the C CLI")
        subprocess.run(["make", "-C", str(root / "c"), "all"], check=True)
    if not cli.exists():
        pytest.skip("C CLI was not built")
    proc = subprocess.run([str(cli), "hash", "--hex", "616263"], check=True, text=True, capture_output=True)
    assert proc.stdout.strip() == tricube.hexdigest(b"abc")
    proc = subprocess.run(
        [str(cli), "xof", "--hex", "616263", "--bytes", "64"],
        check=True,
        text=True,
        capture_output=True,
    )
    assert proc.stdout.strip() == tricube.xof(b"abc", 64).hex()
