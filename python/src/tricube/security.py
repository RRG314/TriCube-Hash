"""Security-status text for the TriCube package."""

from __future__ import annotations

SECURITY_NOTICE = (
    "TriCube is an experimental research primitive. It has not received "
    "independent cryptanalysis and must not be used for passwords, signatures, "
    "message authentication, key derivation, encryption, blockchain consensus, "
    "production random streams, or any security-critical application."
)


def security_notice() -> str:
    """Return the public TriCube security warning."""

    return SECURITY_NOTICE

