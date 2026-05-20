from __future__ import annotations

import tricube


def test_hash_vectors() -> None:
    assert isinstance(tricube.hash(b"abc"), bytes)
    assert len(tricube.hash(b"abc")) == 32
    assert len(tricube.hexdigest(b"abc")) == 64
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


def test_domain_separation() -> None:
    assert tricube.hash(b"abc", domain=b"domain-a") != tricube.hash(b"abc", domain=b"domain-b")
    assert tricube.xof(b"abc", 32, domain=b"domain-a") != tricube.xof(b"abc", 32, domain=b"domain-b")
    assert tricube.stream(123, 64, domain=b"domain-a") != tricube.stream(123, 64, domain=b"domain-b")


def test_invalid_inputs() -> None:
    for call in (
        lambda: tricube.hash("abc"),  # type: ignore[arg-type]
        lambda: tricube.hexdigest("abc"),  # type: ignore[arg-type]
        lambda: tricube.xof(b"abc", "64"),  # type: ignore[arg-type]
        lambda: tricube.stream("123", 64),  # type: ignore[arg-type]
        lambda: tricube.hash(b"abc", domain="domain"),  # type: ignore[arg-type]
    ):
        try:
            call()
        except TypeError:
            pass
        else:
            raise AssertionError("expected TypeError")

    for call in (
        lambda: tricube.xof(b"abc", -1),
        lambda: tricube.stream(123, -1),
        lambda: tricube.stream(-1, 64),
    ):
        try:
            call()
        except ValueError:
            pass
        else:
            raise AssertionError("expected ValueError")


def test_package_status_helpers() -> None:
    assert tricube.version() == tricube.__version__
    assert "reference" in tricube.available_backends()
    assert tricube.backend() == "reference"
    assert tricube.self_test() is True
    assert "experimental research primitive" in tricube.security_notice()
