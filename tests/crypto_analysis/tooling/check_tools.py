#!/usr/bin/env python3
"""Check optional cryptanalysis and statistical-testing tools.

The script reports availability only. Missing tools are expected on many
developer machines and are reported as NOT_INSTALLED rather than failure.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]


def command_path(*names: str) -> str | None:
    for name in names:
        found = shutil.which(name)
        if found:
            return found
    return None


def python_package(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def version_for(command: str, args: list[str] | None = None) -> str:
    args = args or ["--version"]
    try:
        proc = subprocess.run(
            [command, *args],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=5,
            check=False,
        )
    except Exception as exc:
        return f"version unavailable: {exc.__class__.__name__}"
    text = " ".join(proc.stdout.strip().split())
    return text[:180] if text else "version unavailable"


def local_testu01_adapter() -> str | None:
    candidates = [
        REPO_ROOT / "external_tools" / "bin" / "testu01_stdin32",
        REPO_ROOT.parent / "external_tools" / "bin" / "testu01_stdin32",
        REPO_ROOT / "external_tools" / "bin" / "testu01_stdin64",
        REPO_ROOT.parent / "external_tools" / "bin" / "testu01_stdin64",
    ]
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return str(candidate)
    return command_path("testu01_stdin32", "testu01_stdin64", "TestU01Drv")


def row(area: str, tool: str, status: str, detail: str, path: str = "") -> dict[str, str]:
    return {
        "area": area,
        "tool": tool,
        "status": status,
        "path": path,
        "detail": detail,
    }


def collect() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    if python_package("z3"):
        rows.append(row("SMT", "Z3 Python package", "INSTALLED", "import z3 succeeds"))
    else:
        rows.append(row("SMT", "Z3 Python package", "NOT_INSTALLED", "install optional package with: python -m pip install z3-solver"))

    sage = command_path("sage")
    if sage:
        rows.append(row("Algebraic", "SageMath", "INSTALLED", version_for(sage, ["--version"]), sage))
    else:
        rows.append(row("Algebraic", "SageMath", "NOT_INSTALLED", "install SageMath separately; it is not a Python package dependency"))

    cms = command_path("cryptominisat5", "cryptominisat", "cms")
    if cms:
        rows.append(row("SAT", "CryptoMiniSat", "INSTALLED", version_for(cms, ["--version"]), cms))
    else:
        rows.append(row("SAT", "CryptoMiniSat", "NOT_INSTALLED", "optional SAT solver for future CNF experiments"))

    dieharder = command_path("dieharder")
    if dieharder:
        rows.append(row("Statistical batteries", "Dieharder", "INSTALLED", version_for(dieharder, ["--version"]), dieharder))
    else:
        rows.append(row("Statistical batteries", "Dieharder", "NOT_INSTALLED", "install separately; do not vendor in this repo"))

    rng_test = command_path("RNG_test", "pracrand-RNG_test")
    if rng_test:
        rows.append(row("Statistical batteries", "PractRand RNG_test", "INSTALLED", version_for(rng_test, ["--version"]), rng_test))
    else:
        rows.append(row("Statistical batteries", "PractRand RNG_test", "NOT_INSTALLED", "install PractRand separately"))

    testu01 = local_testu01_adapter()
    if testu01:
        rows.append(row("Statistical batteries", "TestU01 stdin adapter", "INSTALLED", "stdin adapter found", testu01))
    else:
        rows.append(row("Statistical batteries", "TestU01 stdin adapter", "NOT_INSTALLED", "build or install a local adapter; TestU01 is not bundled"))

    smokerand = command_path("smokerand", "SmokeRand")
    if smokerand:
        rows.append(row("Statistical batteries", "SmokeRand", "INSTALLED", version_for(smokerand, ["--help"]), smokerand))
    else:
        rows.append(row("Statistical batteries", "SmokeRand", "NOT_INSTALLED", "install from upstream if needed"))

    nist = command_path("assess")
    if nist:
        rows.append(row("Statistical batteries", "NIST STS assess", "INSTALLED", "assess command found", nist))
    else:
        rows.append(row("Statistical batteries", "NIST STS assess", "NOT_INSTALLED", "install NIST STS separately; command is commonly named assess"))

    return rows


def markdown_table(rows: list[dict[str, str]]) -> str:
    fields = ["area", "tool", "status", "path", "detail"]
    lines = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for item in rows:
        lines.append("| " + " | ".join(item.get(field, "").replace("|", "\\|") for field in fields) + " |")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check optional TriCube analysis tools.")
    parser.add_argument("--json", type=Path, help="write JSON output to this path")
    args = parser.parse_args()
    rows = collect()
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps({"tools": rows}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(markdown_table(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

