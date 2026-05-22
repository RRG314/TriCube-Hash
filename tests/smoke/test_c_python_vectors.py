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


def test_c_cli_hash_variants_and_digest_stream() -> None:
    root = Path(__file__).resolve().parents[2]
    cli = root / "c" / "build" / "tricube"
    if not cli.exists():
        if shutil.which("make") is None:
            pytest.skip("make is not available for building the C CLI")
        subprocess.run(["make", "-C", str(root / "c"), "all"], check=True)
    if not cli.exists():
        pytest.skip("C CLI was not built")
    proc = subprocess.run(
        [str(cli), "hash", "--hex", "616263", "--variant", "hashfast1024"],
        check=True,
        text=True,
        capture_output=True,
    )
    assert proc.stdout.strip() == "9b3930e72f1b5f006ac845ac5cf4b0b243fc49d82e52dd23e54c208718f6c607"
    proc = subprocess.run(
        [str(cli), "hash", "--hex", "616263", "--variant", "hashfast1024r6"],
        check=True,
        text=True,
        capture_output=True,
    )
    assert proc.stdout.strip() == "30b5095808175d52fb8afdf6933660752250696803873f4267068e77332da770"
    proc = subprocess.run(
        [
            str(cli),
            "digest-stream",
            "--seed",
            "123",
            "--messages",
            "4",
            "--message-bytes",
            "64",
            "--out",
            "-",
            "--variant",
            "hashfast1024",
        ],
        check=True,
        capture_output=True,
    )
    assert len(proc.stdout) == 128
