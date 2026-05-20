from __future__ import annotations

import tricube


def test_security_notice_is_explicit() -> None:
    notice = tricube.security_notice()
    assert "experimental research primitive" in notice
    assert "must not be used" in notice
    assert "security-critical" in notice
