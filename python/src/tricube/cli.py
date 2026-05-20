"""Command line interface for the Python TriCube package."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .api import hash as tricube_hash
from .api import stream as tricube_stream
from .api import xof as tricube_xof


def _bytes_from_hex(value: str) -> bytes:
    try:
        return bytes.fromhex(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def _cmd_hash(args: argparse.Namespace) -> int:
    if (args.hex is None) == (args.file is None):
        raise SystemExit("provide exactly one of a file path or --hex")
    data = _bytes_from_hex(args.hex) if args.hex is not None else Path(args.file).read_bytes()
    print(tricube_hash(data).hex())
    return 0


def _cmd_xof(args: argparse.Namespace) -> int:
    data = _bytes_from_hex(args.hex)
    print(tricube_xof(data, args.bytes).hex())
    return 0


def _cmd_stream(args: argparse.Namespace) -> int:
    data = tricube_stream(args.seed, args.bytes)
    if args.out == "-":
        sys.stdout.buffer.write(data)
    else:
        Path(args.out).write_bytes(data)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tricube-py", description="TriCube experimental hash/XOF tools")
    sub = parser.add_subparsers(dest="command", required=True)

    p_hash = sub.add_parser("hash", help="hash a file or hexadecimal message")
    p_hash.add_argument("file", nargs="?", help="file to hash")
    p_hash.add_argument("--hex", help="hex-encoded message")
    p_hash.set_defaults(func=_cmd_hash)

    p_xof = sub.add_parser("xof", help="emit XOF output for a hex-encoded message")
    p_xof.add_argument("--hex", required=True, help="hex-encoded message")
    p_xof.add_argument("--bytes", required=True, type=int, help="number of bytes to emit")
    p_xof.set_defaults(func=_cmd_xof)

    p_stream = sub.add_parser("stream", help="write deterministic stream bytes")
    p_stream.add_argument("--seed", required=True, type=int)
    p_stream.add_argument("--bytes", required=True, type=int)
    p_stream.add_argument("--out", required=True, help="output path or '-' for stdout")
    p_stream.set_defaults(func=_cmd_stream)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
