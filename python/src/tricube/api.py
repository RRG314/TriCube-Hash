"""Public Python API for TriCube.

The public functions in this module are intentionally small. They expose the
current TriCube reference path for hashing, XOF output, and deterministic test
streams without promoting the candidate as security-ready.
"""

from __future__ import annotations

from . import _reference

DEFAULT_STREAM_DOMAIN = b"TRICUBE/STREAM"


def hash(data: bytes) -> bytes:
    """Return the 32-byte TriCube digest of *data*.

    TriCube is experimental. This function is suitable for reproducible
    research tests, not for passwords, signatures, message authentication,
    key derivation, or other security-critical use.
    """

    return _reference.tricube_geometric256(data, outlen=32)


def hexdigest(data: bytes) -> str:
    """Return the hexadecimal 32-byte TriCube digest of *data*."""

    return hash(data).hex()


def xof(data: bytes, n: int) -> bytes:
    """Return *n* bytes of TriCube XOF output for *data*."""

    if n < 0:
        raise ValueError("n must be non-negative")
    return _reference.tricube_geometric256(data, outlen=n, encoded_outlen=0)


def stream(seed: int, n: int, domain: bytes = DEFAULT_STREAM_DOMAIN) -> bytes:
    """Return *n* deterministic stream bytes derived from *seed*.

    With the default domain this follows the stream path used by the C CLI.
    Supplying a non-default domain uses the hash/XOF path with explicit domain
    separation. Both modes are deterministic.
    """

    if seed < 0:
        raise ValueError("seed must be non-negative")
    if n < 0:
        raise ValueError("n must be non-negative")
    if domain == DEFAULT_STREAM_DOMAIN:
        return _reference.tricube_geometric256_generator(n, seed=seed)
    seed_bytes = seed.to_bytes(16, "little", signed=False)
    return _reference.tricube_geometric256(seed_bytes, outlen=n, domain=domain)
