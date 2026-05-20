"""TriCube experimental geometric hash/XOF candidate.

TriCube is research software. It is not validated for security-critical use.
"""

from __future__ import annotations

from ._version import __version__
from .api import available_backends, backend, hash, hexdigest, self_test, stream, version, xof
from .security import security_notice

__all__ = [
    "__version__",
    "available_backends",
    "backend",
    "hash",
    "hexdigest",
    "security_notice",
    "self_test",
    "stream",
    "version",
    "xof",
]
