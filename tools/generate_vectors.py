from __future__ import annotations

import json

import tricube


MESSAGES = {
    "empty": b"",
    "abc": b"abc",
    "project-name": b"TriCube",
}


def main() -> int:
    payload = {
        "algorithm": "TriCube",
        "status": "experimental",
        "digest_bytes": 32,
        "hash_vectors": [
            {"name": name, "message_hex": data.hex(), "digest_hex": tricube.hexdigest(data)}
            for name, data in MESSAGES.items()
        ],
    }
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

