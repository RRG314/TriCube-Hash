# TriCube Design

TriCube is an experimental geometric hash and XOF candidate. The construction is meant to be simple enough to inspect while still preserving the original geometric idea: state evolution happens over a cube-connected graph, and local mixing happens over tetrahedral subcells.

This document describes the current public construction. It does not claim that the construction is secure.

## State Model

![TriCube state layout](figures/state-layout.svg)

The internal state has 32 lanes of 64 bits each, for a total of 2048 bits.

Twenty-seven lanes are interpreted as the vertices of a 3 x 3 x 3 grid. That grid contains eight unit cube cells. Each cube cell has eight vertices. The remaining five lanes are shell lanes used to carry length, domain, and global coupling information.

The vertex index is deterministic:

```text
index(x, y, z) = x + 3 * (y + 3 * z)
```

where each coordinate is in `{0, 1, 2}`.

## Tetrahedral Decomposition

![TriCube tetrahedral decomposition](figures/tetrahedral-decomposition.svg)

Each cube cell is decomposed into six tetrahedra. For a cube with local vertices numbered from 0 to 7, the local tetrahedra are:

```text
(0, 1, 3, 7)
(0, 3, 2, 7)
(0, 2, 6, 7)
(0, 6, 4, 7)
(0, 4, 5, 7)
(0, 5, 1, 7)
```

The full 2 x 2 x 2 block therefore has 48 tetrahedral mixing groups.

This tetrahedral decomposition is the main structural distinction from a flat ARX hash. It gives the round function a fixed geometric neighborhood schedule: local tetrahedral mixing, edge propagation, shell coupling, and then a global permutation.

## Round Function

![TriCube round flow](figures/round-flow.svg)

A TriCube round applies four steps:

1. Local tetrahedral mixing over each tetrahedron.
2. Edge coupling over adjacent grid vertices.
3. Shell coupling between selected vertex lanes and shell lanes.
4. A deterministic lane permutation and round-constant injection.

The local tetrahedral mixer uses 64-bit addition, xor, and rotation. The rotation set depends on the round and the tetrahedron index. This makes the orientation of the tetrahedron matter and avoids applying exactly the same operation to every local group.

## Absorb, Finalize, and Squeeze

TriCube absorbs message blocks into selected lanes, applies partial permutation rounds, absorbs a length/finalization trailer, applies final rounds, and then squeezes bytes from the state.

Digest mode emits 32 bytes. XOF mode emits an arbitrary number of bytes by continuing the squeeze schedule. Stream mode initializes from a seed and emits deterministic stream bytes for statistical testing.

The default stream path is the released baseline. The C API also exposes
experimental faster stream variants for continued testing. `fast8x` is the
original optimized path: it is domain-separated from the baseline, uses fewer
rounds in the stream update path, widens the stream extraction rate, and adds
an xmix output layer. The newer `fast8x*mix` candidates keep the same 8-round
initialization and 4-round stream step, widen the output rate further, and add
a feedback xmix extraction layer so wider output words are chained through
state-derived carry terms.

These stream variants do not change digest mode, XOF mode, fixed hash vectors,
or the default stream behavior. They are candidates for testing speed and
statistical behavior, not security recommendations.

The construction uses domain separation strings so hash, XOF, and stream behavior do not share the same state initialization path. Some implementation domain strings retain earlier prototype labels so the May 2026 test vectors remain reproducible. The public project name is TriCube.

## What Is Not Claimed

TriCube is not a standardized sponge construction, not a proven permutation, not a keyed MAC, and not a validated random bit generator. The current design is a candidate that needs external review and stronger analysis before it can responsibly make cryptographic claims.
