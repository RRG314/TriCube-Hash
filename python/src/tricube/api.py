"""Public Python API for TriCube.

The public functions in this module are intentionally small. They expose the
current TriCube reference path for hashing, XOF output, and deterministic test
streams without promoting the candidate as security-ready.
"""

from __future__ import annotations

from . import _native, _reference
from ._version import __version__
from .security import security_notice

DEFAULT_STREAM_DOMAIN = b"TRICUBE/STREAM"


def _require_bytes(name: str, value: bytes | None) -> bytes:
    if value is None:
        raise TypeError(f"{name} must be bytes, not None")
    if not isinstance(value, bytes):
        raise TypeError(f"{name} must be bytes")
    return value


def _optional_domain(domain: bytes | None) -> bytes | None:
    if domain is None:
        return None
    return _require_bytes("domain", domain)


def _require_int(name: str, value: int) -> int:
    if not isinstance(value, int):
        raise TypeError(f"{name} must be an int")
    return value


def hash(data: bytes, *, domain: bytes | None = None) -> bytes:
    """Return the 32-byte TriCube digest of *data*.

    TriCube is experimental. This function is suitable for reproducible
    research tests, not for passwords, signatures, message authentication,
    key derivation, or other security-critical use.
    """

    data = _require_bytes("data", data)
    domain = _optional_domain(domain)
    if domain is None:
        return _reference.tricube_geometric256(data, outlen=32)
    return _reference.tricube_geometric256(data, outlen=32, domain=domain)


def hexdigest(data: bytes, *, domain: bytes | None = None) -> str:
    """Return the hexadecimal 32-byte TriCube digest of *data*."""

    return hash(data, domain=domain).hex()


def xof(data: bytes, n: int, *, domain: bytes | None = None) -> bytes:
    """Return *n* bytes of TriCube XOF output for *data*."""

    data = _require_bytes("data", data)
    n = _require_int("n", n)
    if n < 0:
        raise ValueError("n must be non-negative")
    domain = _optional_domain(domain)
    if domain is None:
        return _reference.tricube_geometric256(data, outlen=n, encoded_outlen=0)
    return _reference.tricube_geometric256(data, outlen=n, domain=domain, encoded_outlen=0)


def stream(seed: int, n: int, *, domain: bytes | None = None) -> bytes:
    """Return *n* deterministic stream bytes derived from *seed*.

    With the default domain this follows the public stream path used by the C CLI.
    Supplying a non-default domain uses the hash/XOF path with explicit domain
    separation. Both modes are deterministic.
    """

    seed = _require_int("seed", seed)
    n = _require_int("n", n)
    if seed < 0:
        raise ValueError("seed must be non-negative")
    if n < 0:
        raise ValueError("n must be non-negative")
    domain = _optional_domain(domain)
    if domain is None:
        domain = DEFAULT_STREAM_DOMAIN
    if domain == DEFAULT_STREAM_DOMAIN:
        return _reference.tricube_geometric256_generator(n, seed=seed)
    seed_bytes = seed.to_bytes(16, "little", signed=False)
    return _reference.tricube_geometric256(seed_bytes, outlen=n, domain=domain)


def version() -> str:
    """Return the installed TriCube package version."""

    return __version__


def available_backends() -> list[str]:
    """Return available execution backends for the Python package.

    The PyPI package always includes the pure Python reference backend. A local
    standalone C CLI may also be discoverable in a source checkout, but it is
    not required for package operation.
    """

    backends = ["reference"]
    if _native.find_cli() is not None:
        backends.append("c-cli")
    return backends


def backend() -> str:
    """Return the backend used by the public Python API."""

    return "reference"


def self_test() -> bool:
    """Run fixed vector and deterministic stream checks."""

    from .vectors import HASH_VECTORS

    for data, expected_hex in HASH_VECTORS.items():
        if hexdigest(data) != expected_hex:
            return False
    if xof(b"abc", 64) != xof(b"abc", 96)[:64]:
        return False
    if stream(seed=123, n=128) != stream(seed=123, n=128):
        return False
    if stream(seed=123, n=128) == stream(seed=124, n=128):
        return False
    return True
