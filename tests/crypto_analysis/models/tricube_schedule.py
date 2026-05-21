"""TriCube lane schedule model used by analysis scripts.

This module describes the public TriCube lane topology and schedule at the
word-lane level. It does not model bit-level ARX probabilities, SAT/SMT
constraints, algebraic degree, or attack cost. The purpose is to provide one
tested place where later solver models can get the same lane mapping,
tetrahedra, edge set, shell schedule, and permutation used by the
specification.
"""

from __future__ import annotations

from dataclasses import dataclass


STATE_WORDS = 32
VERTEX_LANES = 27
SHELL_LANES = tuple(range(27, 32))
SCHEDULE_PERIOD = 24
LOCAL_TETRAHEDRA = (
    (0, 1, 3, 7),
    (0, 3, 2, 7),
    (0, 2, 6, 7),
    (0, 6, 4, 7),
    (0, 4, 5, 7),
    (0, 5, 1, 7),
)
TETRA_ROTATION_SETS = (
    (17, 29, 41, 53),
    (23, 31, 47, 59),
    (19, 37, 43, 61),
    (13, 27, 39, 55),
)


@dataclass(frozen=True)
class ScheduleCounts:
    vertex_lanes: int
    shell_lanes: int
    cube_cells: int
    tetrahedra: int
    edges: int
    permutation_lanes: int


def vindex3(x: int, y: int, z: int) -> int:
    """Return the vertex lane for coordinate ``(x, y, z)`` in the 3x3x3 grid."""

    if not (0 <= x < 3 and 0 <= y < 3 and 0 <= z < 3):
        raise ValueError("vertex coordinates must be in 0..2")
    return x + 3 * (y + 3 * z)


def vertex_coordinates() -> list[tuple[int, int, int, int]]:
    """Return ``(lane, x, y, z)`` rows for the 27 vertex lanes."""

    rows: list[tuple[int, int, int, int]] = []
    for z in range(3):
        for y in range(3):
            for x in range(3):
                rows.append((vindex3(x, y, z), x, y, z))
    return rows


def cube_vertices(cx: int, cy: int, cz: int) -> tuple[int, int, int, int, int, int, int, int]:
    """Return the eight vertex lanes for cube cell ``(cx, cy, cz)``."""

    if not (0 <= cx < 2 and 0 <= cy < 2 and 0 <= cz < 2):
        raise ValueError("cube coordinates must be in 0..1")
    return (
        vindex3(cx, cy, cz),
        vindex3(cx + 1, cy, cz),
        vindex3(cx, cy + 1, cz),
        vindex3(cx + 1, cy + 1, cz),
        vindex3(cx, cy, cz + 1),
        vindex3(cx + 1, cy, cz + 1),
        vindex3(cx, cy + 1, cz + 1),
        vindex3(cx + 1, cy + 1, cz + 1),
    )


def cube_cells() -> list[tuple[int, int, int]]:
    """Return cube cells in the normative iteration order."""

    return [(cx, cy, cz) for cz in range(2) for cy in range(2) for cx in range(2)]


def build_tetrahedra() -> list[tuple[int, int, int, int]]:
    """Return the 48 global tetrahedral neighborhoods."""

    out: list[tuple[int, int, int, int]] = []
    for cx, cy, cz in cube_cells():
        verts = cube_vertices(cx, cy, cz)
        out.extend(tuple(verts[i] for i in tet) for tet in LOCAL_TETRAHEDRA)
    return out


def build_edges() -> list[tuple[int, int]]:
    """Return all positive-axis grid-adjacent vertex edges."""

    out: list[tuple[int, int]] = []
    for z in range(3):
        for y in range(3):
            for x in range(3):
                i = vindex3(x, y, z)
                if x + 1 < 3:
                    out.append((i, vindex3(x + 1, y, z)))
                if y + 1 < 3:
                    out.append((i, vindex3(x, y + 1, z)))
                if z + 1 < 3:
                    out.append((i, vindex3(x, y, z + 1)))
    return out


def oriented_tetrahedron(
    tet: tuple[int, int, int, int], round_index: int, tetrahedron_index: int
) -> tuple[int, int, int, int]:
    """Return the oriented tetrahedron used in one scheduled round."""

    a, b, c, d = tet
    if (round_index + tetrahedron_index) & 1:
        b, d = d, b
    if (round_index + tetrahedron_index) & 2:
        a, c = c, a
    return a, b, c, d


def tetra_rotation_set(round_index: int, tetrahedron_index: int) -> tuple[int, int, int, int]:
    """Return the four tetrahedral rotation constants for this schedule point."""

    return TETRA_ROTATION_SETS[(round_index + tetrahedron_index) & 3]


def edge_rotations(round_index: int, edge_index: int) -> tuple[int, int]:
    """Return the two edge-coupling rotation counts for this schedule point."""

    sr = round_index % SCHEDULE_PERIOD
    return ((edge_index + sr * 3) % 61 + 1, (edge_index * 7 + sr) % 61 + 1)


def shell_targets(round_index: int) -> list[tuple[int, int, int]]:
    """Return ``(shell_lane, vertex_lane, opposite_lane)`` for one round."""

    sr = round_index % SCHEDULE_PERIOD
    rows: list[tuple[int, int, int]] = []
    for j, lane in enumerate(SHELL_LANES):
        vertex = (sr * 5 + j * 7) % VERTEX_LANES
        opposite = (vertex * 11 + 3) % VERTEX_LANES
        rows.append((lane, vertex, opposite))
    return rows


def lane_permutation() -> list[int]:
    """Return the source lane for each destination lane after permutation."""

    return [(9 * i + 5) & 31 for i in range(STATE_WORDS)]


def permutation_rotation(round_index: int, lane_index: int) -> int:
    """Return the constant-injection rotation for one lane after permutation."""

    return ((5 * lane_index + (round_index % SCHEDULE_PERIOD)) % 61) + 1


def schedule_counts() -> ScheduleCounts:
    """Return counts that should remain stable for the current public baseline."""

    return ScheduleCounts(
        vertex_lanes=VERTEX_LANES,
        shell_lanes=len(SHELL_LANES),
        cube_cells=len(cube_cells()),
        tetrahedra=len(build_tetrahedra()),
        edges=len(build_edges()),
        permutation_lanes=len(lane_permutation()),
    )


def validate_schedule() -> None:
    """Raise ``AssertionError`` if the public baseline schedule shape changes."""

    counts = schedule_counts()
    assert counts.vertex_lanes == 27
    assert counts.shell_lanes == 5
    assert counts.cube_cells == 8
    assert counts.tetrahedra == 48
    assert counts.edges == 54
    assert counts.permutation_lanes == 32
    assert sorted(lane_permutation()) == list(range(STATE_WORDS))

