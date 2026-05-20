from __future__ import annotations

import json
from importlib import resources

import tricube


def test_json_vectors_match_python_api() -> None:
    vector_text = resources.files("tricube").joinpath("data/tricube_vectors.json").read_text(encoding="utf-8")
    vectors = json.loads(vector_text)
    for item in vectors["hash_vectors"]:
        data = bytes.fromhex(item["message_hex"])
        assert tricube.hexdigest(data) == item["digest_hex"]


def test_cli_vectors_are_public_json() -> None:
    vector_text = resources.files("tricube").joinpath("data/tricube_vectors.json").read_text(encoding="utf-8")
    vectors = json.loads(vector_text)
    assert vectors["algorithm"] == "TriCube"
    assert vectors["digest_bytes"] == 32
