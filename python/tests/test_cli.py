from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "tricube", *args],
        check=True,
        text=True,
        capture_output=True,
    )


def test_python_module_cli_hash_hex() -> None:
    proc = run_cli("hash", "--hex", "616263")
    assert proc.stdout.strip() == "779403a9c748fc3213493953fc17309367b37161c00dc19059c14db63774e11e"


def test_python_module_cli_xof() -> None:
    proc = run_cli("xof", "--hex", "616263", "--bytes", "64")
    assert len(proc.stdout.strip()) == 128


def test_python_module_cli_stream(tmp_path: Path) -> None:
    out = tmp_path / "stream.bin"
    run_cli("stream", "--seed", "123", "--bytes", "1024", "--out", str(out))
    data = out.read_bytes()
    assert len(data) == 1024
    assert any(data)


def test_python_module_cli_self_test() -> None:
    proc = run_cli("self-test")
    assert "passed" in proc.stdout


def test_python_module_cli_security_notice() -> None:
    proc = run_cli("security-notice")
    assert "must not be used" in proc.stdout


def test_console_script_hash_hex() -> None:
    proc = subprocess.run(
        ["tricube", "hash", "--hex", "616263"],
        check=True,
        text=True,
        capture_output=True,
    )
    assert proc.stdout.strip() == "779403a9c748fc3213493953fc17309367b37161c00dc19059c14db63774e11e"
