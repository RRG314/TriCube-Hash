"""TriCube experimental geometric hash/XOF candidate.

TriCube is research software. It is not validated for security-critical use.
"""

from __future__ import annotations

from .api import hash, hexdigest, stream, xof

__version__ = "0.1.0"

__all__ = ["__version__", "hash", "hexdigest", "stream", "xof"]

