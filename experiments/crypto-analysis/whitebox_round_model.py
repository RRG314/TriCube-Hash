#!/usr/bin/env python3
"""White-box schedule and word-dependency analysis for TriCube.

This is structural analysis, not cryptanalysis.  It models which original
64-bit lanes can influence which later 64-bit lanes under the specified
round schedule.  It does not model bit-level modular-addition differentials,
rotational probabilities, algebraic degree, or attack cost.
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

from common import environment, markdown_table, write_csv, write_json
from models.tricube_schedule import (
    STATE_WORDS,
    SHELL_LANES,
    TETRA_ROTATION_SETS,
    build_edges,
    build_tetrahedra,
    edge_rotations,
    lane_permutation,
    oriented_tetrahedron,
    permutation_rotation,
    shell_targets,
    validate_schedule,
)


CHECK_ROUNDS = [0, 1, 2, 3, 4, 6, 8, 12, 16, 24]


def apply_round(deps: list[set[int]], rnd: int, tetrahedra: list[tuple[int, int, int, int]], edges: list[tuple[int, int]]) -> list[set[int]]:
    deps = [set(d) for d in deps]
    sr = rnd % 24

    for t, tet in enumerate(tetrahedra):
        a, b, c, d = oriented_tetrahedron(tet, sr, t)
        merged = deps[a] | deps[b] | deps[c] | deps[d]
        deps[a] = set(merged)
        deps[b] = set(merged)
        deps[c] = set(merged)
        deps[d] = set(merged)

    for a, b in edges:
        merged = deps[a] | deps[b]
        deps[a] = set(merged)
        deps[b] = set(merged)

    for lane, vertex, opposite in shell_targets(sr):
        lane_dep = deps[lane] | deps[vertex]
        deps[lane] = set(lane_dep)
        deps[opposite] = deps[opposite] | lane_dep | deps[vertex]

    return [set(deps[source]) for source in lane_permutation()]


def dependency_row(round_number: int, deps: list[set[int]]) -> dict[str, object]:
    sizes = [len(d) for d in deps]
    influence = [sum(1 for d in deps if src in d) for src in range(STATE_WORDS)]
    return {
        "rounds": round_number,
        "min_lane_dependency": min(sizes),
        "mean_lane_dependency": round(statistics.mean(sizes), 4),
        "max_lane_dependency": max(sizes),
        "fully_mixed_lanes": sum(1 for size in sizes if size == STATE_WORDS),
        "min_source_influence_lanes": min(influence),
        "mean_source_influence_lanes": round(statistics.mean(influence), 4),
        "max_source_influence_lanes": max(influence),
    }


def output_dependency_rows(round_number: int, deps: list[set[int]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for j in range(4):
        lanes = [
            (j * 5) & 31,
            (j * 11 + 7) & 31,
            (j * 17 + 13) & 31,
            (j * 23 + 19) & 31,
        ]
        merged: set[int] = set()
        for lane in lanes:
            merged |= deps[lane]
        rows.append(
            {
                "rounds": round_number,
                "output_word": j,
                "state_lanes_read": ",".join(str(x) for x in lanes),
                "dependency_size": len(merged),
                "depends_on_all_initial_lanes": len(merged) == STATE_WORDS,
            }
        )
    return rows


def schedule_coverage_rows(tetrahedra: list[tuple[int, int, int, int]], edges: list[tuple[int, int]], rounds: int) -> list[dict[str, object]]:
    from collections import Counter

    tet_counts = Counter(lane for tet in tetrahedra for lane in tet)
    edge_counts = Counter(lane for edge in edges for lane in edge)
    shell_vertex_counts = Counter()
    shell_opposite_counts = Counter()
    tetra_rotations = Counter()
    observed_edge_rotations = Counter()
    perm_rotations = Counter()
    for rnd in range(rounds):
        sr = rnd % 24
        for t in range(len(tetrahedra)):
            tetra_rotations.update(TETRA_ROTATION_SETS[(sr + t) & 3])
        for e in range(len(edges)):
            observed_edge_rotations.update(edge_rotations(sr, e))
        for i in range(STATE_WORDS):
            perm_rotations[permutation_rotation(sr, i)] += 1
        for _lane, vertex, opposite in shell_targets(sr):
            shell_vertex_counts[vertex] += 1
            shell_opposite_counts[opposite] += 1

    return [
        {
            "metric": "tetrahedra_per_round",
            "value": len(tetrahedra),
            "notes": "six tetrahedra for each of eight cube cells",
        },
        {
            "metric": "edges_per_round",
            "value": len(edges),
            "notes": "all positive-axis grid adjacencies in the 3x3x3 vertex grid",
        },
        {
            "metric": "min_tetra_incidence_per_vertex",
            "value": min(tet_counts.values()),
            "notes": "per round, vertex lanes only",
        },
        {
            "metric": "max_tetra_incidence_per_vertex",
            "value": max(tet_counts.values()),
            "notes": "per round, vertex lanes only",
        },
        {
            "metric": "min_edge_degree_per_vertex",
            "value": min(edge_counts.values()),
            "notes": "corners are lower degree, center is highest degree",
        },
        {
            "metric": "max_edge_degree_per_vertex",
            "value": max(edge_counts.values()),
            "notes": "axis-adjacent grid graph degree",
        },
        {
            "metric": "shell_vertex_lanes_touched",
            "value": len(shell_vertex_counts),
            "notes": f"over {rounds} modeled rounds",
        },
        {
            "metric": "shell_opposite_lanes_touched",
            "value": len(shell_opposite_counts),
            "notes": f"over {rounds} modeled rounds",
        },
        {
            "metric": "distinct_tetra_rotation_constants",
            "value": len(tetra_rotations),
            "notes": ",".join(str(x) for x in sorted(tetra_rotations)),
        },
        {
            "metric": "distinct_edge_rotation_constants",
            "value": len(observed_edge_rotations),
            "notes": "edge coupling uses rotations 1..61 over a 24-round period",
        },
        {
            "metric": "distinct_permutation_rotation_constants",
            "value": len(perm_rotations),
            "notes": "constant-injection rotations used after lane permutation",
        },
    ]


def run(rounds: int) -> dict[str, object]:
    validate_schedule()
    tetrahedra = build_tetrahedra()
    edges = build_edges()
    deps = [{i} for i in range(STATE_WORDS)]
    dependency_rows: list[dict[str, object]] = []
    output_rows: list[dict[str, object]] = []
    for r in range(rounds + 1):
        if r in CHECK_ROUNDS or r == rounds:
            dependency_rows.append(dependency_row(r, deps))
            output_rows.extend(output_dependency_rows(r, deps))
        if r < rounds:
            deps = apply_round(deps, r, tetrahedra, edges)
    coverage_rows = schedule_coverage_rows(tetrahedra, edges, rounds)
    first_full = next((row["rounds"] for row in dependency_rows if row["fully_mixed_lanes"] == STATE_WORDS), None)
    first_output_full = next(
        (
            row["rounds"]
            for row in output_rows
            if row["rounds"] > 0
            and all(
                out_row["depends_on_all_initial_lanes"]
                for out_row in output_rows
                if out_row["rounds"] == row["rounds"]
            )
        ),
        None,
    )
    return {
        "metadata": {},
        "summary": {
            "rounds_modeled": rounds,
            "tetrahedra_per_round": len(tetrahedra),
            "edges_per_round": len(edges),
            "first_round_in_table_all_state_lanes_full_dependency": first_full,
            "first_round_in_table_first_32_output_bytes_full_dependency": first_output_full,
            "interpretation": "word-level dependency reaches all modeled source lanes quickly, but this is not a differential, rotational, or algebraic security bound",
        },
        "dependency_by_round": dependency_rows,
        "output_dependency": output_rows,
        "schedule_coverage": coverage_rows,
    }


def write_markdown(path: Path, data: dict[str, object]) -> None:
    summary = data["summary"]
    dependency_rows = data["dependency_by_round"]
    output_rows = data["output_dependency"]
    coverage_rows = data["schedule_coverage"]
    text = [
        "# TriCube White-Box Round-Model Summary",
        "",
        "This report analyzes the specified round schedule at word-lane granularity. It uses the TriCube tetrahedron, edge, shell, and permutation rules directly instead of treating the primitive as a black box.",
        "",
        "This is not cryptanalysis. It does not model modular-addition differential probabilities, rotational trails, SAT/SMT/MILP constraints, algebraic invariants, or attack complexity. It answers a narrower question: which original 64-bit lanes can influence which later 64-bit lanes under the current schedule.",
        "",
        "## Summary",
        "",
        markdown_table([summary]),
        "## State Dependency by Round",
        "",
        markdown_table(dependency_rows),
        "## First 32 Output Bytes Dependency",
        "",
        markdown_table(output_rows),
        "## Schedule Coverage",
        "",
        markdown_table(coverage_rows),
    ]
    path.write_text("\n".join(text), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run TriCube white-box schedule dependency analysis.")
    parser.add_argument("--rounds", type=int, default=24)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    data = run(args.rounds)
    data["metadata"] = environment()
    data["metadata"]["rounds"] = args.rounds
    write_json(args.out / "summary.json", data)
    write_csv(args.out / "dependency_by_round.csv", data["dependency_by_round"])
    write_csv(args.out / "output_dependency.csv", data["output_dependency"])
    write_csv(args.out / "schedule_coverage.csv", data["schedule_coverage"])
    write_markdown(args.out / "summary.md", data)
    print(f"wrote {args.out}")
    print(json.dumps(data["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
