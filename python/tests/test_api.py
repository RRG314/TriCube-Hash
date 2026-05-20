from __future__ import annotations

import tricube


def test_hash_vectors() -> None:
    assert tricube.hexdigest(b"") == "7fcaaa35165277bcaca583e23ef1d3545705e14d39f3ed7a802b1275d920cf49"
    assert tricube.hexdigest(b"abc") == "779403a9c748fc3213493953fc17309367b37161c00dc19059c14db63774e11e"
    assert tricube.hexdigest(b"TriCube") == "5b4c461fe975dfba72fc9b2fbcf04e3a1a807c83fa4502c238ee4fe48b736d13"


def test_xof_lengths_and_prefix_determinism() -> None:
    out_64 = tricube.xof(b"abc", 64)
    out_96 = tricube.xof(b"abc", 96)
    assert len(out_64) == 64
    assert len(out_96) == 96
    assert out_96[:64] == out_64


def test_stream_determinism_and_seed_separation() -> None:
    a = tricube.stream(123, 256)
    b = tricube.stream(123, 256)
    c = tricube.stream(124, 256)
    assert a == b
    assert a != c
    assert len(a) == 256
    assert any(a)

