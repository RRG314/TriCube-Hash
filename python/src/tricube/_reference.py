"""Pure Python reference path for TriCube.

This module is the experimental path for making TriCube more than a wrapper
around established hash primitives. It keeps the geometric tetrahedral/block
spirit but uses its own public 64-bit ARX permutation, absorb rule, and squeeze
rule.

No cryptographic-security claim is made. The purpose is to create a clean
candidate that can be benchmarked, attacked, and revised. Some internal
constant names retain earlier development terminology for vector compatibility;
the public project name is TriCube.
"""

from __future__ import annotations

from collections.abc import Iterator

MASK64 = 0xFFFFFFFFFFFFFFFF
TRICUBE_GEOMETRIC256_DIGEST_BYTES = 32
TRICUBE_GEOMETRIC256_STATE_WORDS = 32
TRICUBE_GEOMETRIC256_STATE_BITS = TRICUBE_GEOMETRIC256_STATE_WORDS * 64
TRICUBE_GEOMETRIC256_BLOCK_BYTES = 64
TRICUBE_GEOMETRIC256_RATE_BYTES = 192


def _rotl64(x: int, r: int) -> int:
    r &= 63
    x &= MASK64
    return ((x << r) | (x >> (64 - r))) & MASK64


def _splitmix64_next(x: int) -> tuple[int, int]:
    x = (x + 0x9E3779B97F4A7C15) & MASK64
    z = x
    z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK64
    z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK64
    return x, (z ^ (z >> 31)) & MASK64


def _constant_stream(seed: int, n: int) -> tuple[int, ...]:
    out: list[int] = []
    x = seed & MASK64
    for _ in range(n):
        x, value = _splitmix64_next(x)
        out.append(value)
    return tuple(out)


def _vindex(x: int, y: int, z: int) -> int:
    return x + 3 * (y + 3 * z)


def _cube_vertices(cx: int, cy: int, cz: int) -> tuple[int, ...]:
    return (
        _vindex(cx, cy, cz),
        _vindex(cx + 1, cy, cz),
        _vindex(cx, cy + 1, cz),
        _vindex(cx + 1, cy + 1, cz),
        _vindex(cx, cy, cz + 1),
        _vindex(cx + 1, cy, cz + 1),
        _vindex(cx, cy + 1, cz + 1),
        _vindex(cx + 1, cy + 1, cz + 1),
    )


def _build_tetrahedra() -> tuple[tuple[int, int, int, int], ...]:
    local_tets = (
        (0, 1, 3, 7),
        (0, 3, 2, 7),
        (0, 2, 6, 7),
        (0, 6, 4, 7),
        (0, 4, 5, 7),
        (0, 5, 1, 7),
    )
    out: list[tuple[int, int, int, int]] = []
    for cz in range(2):
        for cy in range(2):
            for cx in range(2):
                verts = _cube_vertices(cx, cy, cz)
                out.extend(tuple(verts[i] for i in tet) for tet in local_tets)
    return tuple(out)


def _build_edges() -> tuple[tuple[int, int], ...]:
    edges: list[tuple[int, int]] = []
    for z in range(3):
        for y in range(3):
            for x in range(3):
                i = _vindex(x, y, z)
                if x + 1 < 3:
                    edges.append((i, _vindex(x + 1, y, z)))
                if y + 1 < 3:
                    edges.append((i, _vindex(x, y + 1, z)))
                if z + 1 < 3:
                    edges.append((i, _vindex(x, y, z + 1)))
    return tuple(edges)


TETRAHEDRA64 = _build_tetrahedra()
EDGES64 = _build_edges()
SHELL_LANES = (27, 28, 29, 30, 31)
LANE_PERM = tuple((i * 9 + 5) & 31 for i in range(32))
INV_LANE_PERM = tuple(LANE_PERM.index(i) for i in range(32))
ROUND_CONSTANTS = _constant_stream(0x5452494355424556, 32 * 24)
IV = _constant_stream(0x5445545241435542, 32)
ROTATION_SETS = (
    (17, 29, 41, 53),
    (23, 31, 47, 59),
    (19, 37, 43, 61),
    (13, 27, 39, 55),
)


def _words_from_block(block: bytes) -> tuple[int, ...]:
    padded = block + b"\x00" * (TRICUBE_GEOMETRIC256_BLOCK_BYTES - len(block))
    return tuple(
        int.from_bytes(padded[i : i + 8], "little")
        for i in range(0, TRICUBE_GEOMETRIC256_BLOCK_BYTES, 8)
    )


def _absorb_words(state: list[int], words: tuple[int, ...], block_index: int) -> None:
    for j, word in enumerate(words):
        lane = (j * 7 + block_index * 5) & 31
        mate = (lane + 11 + j) & 31
        shell = SHELL_LANES[(j + block_index) % len(SHELL_LANES)]
        state[lane] ^= (word + 0xD6E8FEB86659FD93 + block_index + j) & MASK64
        state[mate] = (state[mate] + _rotl64(word ^ state[lane], (j * 11 + block_index) % 63 + 1)) & MASK64
        state[shell] ^= _rotl64(state[lane] + state[mate] + word, (j * 13 + 7) % 63 + 1)


def _absorb_bytes(state: list[int], data: bytes, block_index: int) -> None:
    _absorb_words(state, _words_from_block(data), block_index)


def _mix_tetra64(state: list[int], tet: tuple[int, int, int, int], rnd: int, tet_index: int) -> None:
    a, b, c, d = tet
    if (rnd + tet_index) & 1:
        b, d = d, b
    if (rnd + tet_index) & 2:
        a, c = c, a
    x0, x1, x2, x3 = state[a], state[b], state[c], state[d]
    base = (rnd * 32 + tet_index) % len(ROUND_CONSTANTS)
    rc0 = ROUND_CONSTANTS[base]
    rc1 = ROUND_CONSTANTS[(base + 7) % len(ROUND_CONSTANTS)]
    rc2 = ROUND_CONSTANTS[(base + 13) % len(ROUND_CONSTANTS)]
    rc3 = ROUND_CONSTANTS[(base + 21) % len(ROUND_CONSTANTS)]
    r0, r1, r2, r3 = ROTATION_SETS[(rnd + tet_index) & 3]

    x0 = (x0 + x1 + rc0) & MASK64
    x3 = _rotl64(x3 ^ x0, r0)
    x2 = (x2 + x3 + rc1) & MASK64
    x1 = _rotl64(x1 ^ x2, r1)
    x0 = (x0 + x1 + (rc2 ^ tet_index)) & MASK64
    x3 = _rotl64(x3 ^ x0, r2)
    x2 = (x2 + x3 + (rc3 + rnd)) & MASK64
    x1 = _rotl64(x1 ^ x2, r3)

    state[a], state[b], state[c], state[d] = x0, x1, x2, x3


def _edge_couple64(state: list[int], rnd: int) -> None:
    for edge_index, (a, b) in enumerate(EDGES64):
        rc = ROUND_CONSTANTS[(rnd * 37 + edge_index * 5) % len(ROUND_CONSTANTS)]
        left = state[a]
        right = state[b]
        state[a] = (left + _rotl64(right ^ rc, (edge_index + rnd * 3) % 61 + 1)) & MASK64
        state[b] = right ^ _rotl64(state[a] + rc + edge_index, (edge_index * 7 + rnd) % 61 + 1)


def _shell_couple64(state: list[int], rnd: int) -> None:
    for j, lane in enumerate(SHELL_LANES):
        vertex = (rnd * 5 + j * 7) % 27
        opposite = (vertex * 11 + 3) % 27
        rc = ROUND_CONSTANTS[(rnd * 11 + j * 17) % len(ROUND_CONSTANTS)]
        state[lane] = (state[lane] + state[vertex] + rc) & MASK64
        state[opposite] ^= _rotl64(state[lane] ^ state[vertex], (rnd + j * 9) % 61 + 1)


def _permute64(state: list[int], rounds: int = 16) -> None:
    for rnd in range(rounds):
        for tet_index, tet in enumerate(TETRAHEDRA64):
            _mix_tetra64(state, tet, rnd, tet_index)
        _edge_couple64(state, rnd)
        _shell_couple64(state, rnd)
        state[:] = [state[LANE_PERM[i]] for i in range(32)]
        rc_offset = rnd * 32
        for i in range(32):
            state[i] ^= _rotl64(ROUND_CONSTANTS[(rc_offset + i) % len(ROUND_CONSTANTS)] + i + rnd, (i * 5 + rnd) % 61 + 1)


def _init_state(domain: bytes, tweak: bytes, outlen: int) -> list[int]:
    state = list(IV)
    header = (
        b"TriCube-Tetra256-" b"v" b"2-native"
        + len(domain).to_bytes(2, "little")
        + len(tweak).to_bytes(2, "little")
        + outlen.to_bytes(4, "little")
        + domain
        + tweak
    )
    for block_index, off in enumerate(range(0, len(header) or 1, TRICUBE_GEOMETRIC256_BLOCK_BYTES)):
        _absorb_bytes(state, header[off : off + TRICUBE_GEOMETRIC256_BLOCK_BYTES], block_index)
        _permute64(state, 4)
    return state


def _fold64(state: list[int], counter: int) -> bytes:
    out = bytearray()
    for j in range(8):
        a = state[(j * 3 + counter) & 31]
        b = state[(j * 7 + 11) & 31]
        c = state[(j * 13 + 19) & 31]
        word = (a + _rotl64(b, (j * 9 + counter) % 61 + 1)) & MASK64
        word ^= _rotl64(c + ROUND_CONSTANTS[(counter + j) % len(ROUND_CONSTANTS)], (j * 11 + 5) % 61 + 1)
        out.extend(word.to_bytes(8, "little"))
    return bytes(out)


def _squeeze_rate64(state: list[int], counter: int, n_bytes: int = TRICUBE_GEOMETRIC256_RATE_BYTES) -> bytes:
    """Return up to the public rate from the native state.

    The rate is capped at 192 bytes, leaving at least 512 bits of the 2048-bit
    state unsqueezed per permutation call. This is a design choice for the
    experimental candidate, not a security proof.
    """

    if n_bytes < 0 or n_bytes > TRICUBE_GEOMETRIC256_RATE_BYTES:
        raise ValueError("n_bytes must be between 0 and TRICUBE_GEOMETRIC256_RATE_BYTES")
    out = bytearray()
    groups = (n_bytes + 7) // 8
    for j in range(groups):
        a = state[(j * 5 + counter) & 31]
        b = state[(j * 11 + 7) & 31]
        c = state[(j * 17 + 13) & 31]
        d = state[(j * 23 + 19) & 31]
        word = (a + _rotl64(b ^ ROUND_CONSTANTS[(counter + j) % len(ROUND_CONSTANTS)], (j * 7 + 9) % 61 + 1)) & MASK64
        word ^= _rotl64((c + d + j + counter) & MASK64, (j * 13 + 3) % 61 + 1)
        out.extend(word.to_bytes(8, "little"))
    return bytes(out[:n_bytes])


def tricube_geometric256(
    data: bytes,
    outlen: int = TRICUBE_GEOMETRIC256_DIGEST_BYTES,
    tweak: bytes = b"",
    domain: bytes = b"TC-TETRA256-" b"V" b"2",
    rounds: int = 16,
    encoded_outlen: int | None = None,
) -> bytes:
    """Return a native TriCube digest or XOF output.

    The primitive path does not call SHA, BLAKE, or another existing hash. It
    uses a custom public 2048-bit tetrahedral ARX permutation. This is an
    experimental research candidate, not a validated cryptographic hash.
    """

    if outlen < 0:
        raise ValueError("outlen must be non-negative")
    if rounds <= 0:
        raise ValueError("rounds must be positive")
    if encoded_outlen is None:
        encoded_outlen = outlen
    if encoded_outlen < 0:
        raise ValueError("encoded_outlen must be non-negative")
    state = _init_state(domain, tweak, encoded_outlen)
    block_index = 0
    if not data:
        _absorb_bytes(state, b"\x80" + (0).to_bytes(8, "little"), block_index)
        _permute64(state, max(6, rounds // 2))
    else:
        for off in range(0, len(data), TRICUBE_GEOMETRIC256_BLOCK_BYTES):
            block = data[off : off + TRICUBE_GEOMETRIC256_BLOCK_BYTES]
            _absorb_bytes(state, block, block_index)
            _permute64(state, max(6, rounds // 2))
            block_index += 1
    trailer = (
        len(data).to_bytes(16, "little")
        + encoded_outlen.to_bytes(8, "little")
        + block_index.to_bytes(8, "little")
        + b"\x80"
    )
    _absorb_bytes(state, trailer, block_index + 1)
    _permute64(state, rounds)
    out = bytearray()
    counter = 0
    while len(out) < outlen:
        out.extend(_squeeze_rate64(state, counter, min(TRICUBE_GEOMETRIC256_RATE_BYTES, outlen - len(out))))
        counter += 1
        if len(out) < outlen:
            _absorb_words(
                state,
                (counter, encoded_outlen, len(data), counter ^ 0xA5A5A5A5A5A5A5A5),
                block_index + counter + 2,
            )
            _permute64(state, max(6, rounds // 2))
    return bytes(out[:outlen])


def iter_tricube_geometric256_blocks(
    seed: int = 0,
    block_size: int = 1 << 16,
    rounds: int = 12,
) -> Iterator[bytes]:
    """Yield deterministic native TriCube stream blocks.

    This stream uses only the TriCube permutation and squeeze path. It is
    intended for testing the novel primitive path directly.
    """

    if block_size <= 0:
        raise ValueError("block_size must be positive")
    state = _init_state(b"TC-TETRA256-" b"V" b"2/STREAM", seed.to_bytes(16, "little", signed=False), 64)
    _absorb_bytes(state, seed.to_bytes(16, "little", signed=False), 0)
    _permute64(state, rounds)
    counter = 0
    while True:
        out = bytearray()
        while len(out) < block_size:
            _absorb_words(
                state,
                (
                    counter,
                    counter ^ 0x9E3779B97F4A7C15,
                    (seed + counter) & MASK64,
                    (seed * 0xD6E8FEB86659FD93 + counter) & MASK64,
                ),
                counter + 1,
            )
            _permute64(state, max(6, rounds // 2))
            out.extend(_squeeze_rate64(state, counter))
            counter += 1
        yield bytes(out[:block_size])


def tricube_geometric256_generator(n_bytes: int, seed: int = 0) -> bytes:
    """Generate a native TriCube byte stream."""

    if n_bytes < 0:
        raise ValueError("n_bytes must be non-negative")
    out = bytearray(n_bytes)
    pos = 0
    blocks = iter_tricube_geometric256_blocks(seed)
    while pos < n_bytes:
        block = next(blocks)
        take = min(len(block), n_bytes - pos)
        out[pos : pos + take] = block[:take]
        pos += take
    return bytes(out)
