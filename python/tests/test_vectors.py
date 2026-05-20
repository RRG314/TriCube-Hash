from __future__ import annotations

import json
from pathlib import Path

import tricube


def test_json_vectors_match_python_api() -> None:
    root = Path(__file__).resolve().parents[2]
    vectors = json.loads((root / "tests" / "vectors" / "tricube_vectors.json").read_text())
    for item in vectors["hash_vectors"]:
        data = bytes.fromhex(item["message_hex"])
        assert tricube.hexdigest(data) == item["digest_hex"]

