# Solver Model Work Plan

This note is a short checklist for building real TriCube solver models. It is
not a result report and it is not evidence of security.

The custom work is the model. Z3, SageMath, CryptoMiniSat, CLAASP, CryptoSMT,
and related tools do not know TriCube's tetrahedral schedule, shell lanes,
domain separation, or output extraction. A solver result is only useful after
the TriCube model has been checked against the specification and fixed vectors.

## Model Foundations

1. Encode the 32-lane state, including 27 vertex lanes and 5 shell/global
   lanes.
2. Encode the 3 x 3 x 3 vertex mapping, 8 cube cells, 48 tetrahedral
   neighborhoods, 54 grid edges, shell coupling schedule, lane permutation, and
   round constants.
3. Add reduced-round hooks for 1, 2, 3, 4, 6, 8, and full baseline rounds.
4. Validate every reduced-round implementation against a small executable
   reference before using it for search.
5. Record whether the model is bit-exact, word-level, truncated-difference, or
   dependency-only. Never mix those labels.

## Differential Model

The first useful differential model should be reduced-round and explicitly
limited. It should model modular addition, XOR, rotations, constants, and the
in-place tetrahedral update order. The goal is to search for low-weight or
high-probability reduced-round trails, not to claim full-round resistance.

## Rotational Model

The rotational model must track how word rotations interact with constants,
modular addition, lane permutation, shell coupling, and output extraction.
Black-box rotational-distance tests are not enough for this.

## Algebraic Model

The algebraic model should start with reduced-round components and a small
number of lanes. SageMath can help with Boolean polynomial experiments, but the
state size makes naive full ANF expansion impractical. Any low-degree or
invariant result must be independently reproduced.

## Collision and Preimage Model

A reduced-round collision/preimage model can be built with SMT or SAT once the
bit-exact round model is validated. The first target should be deliberately
small: short messages, reduced rounds, and truncated outputs.

## Validation

Incorrect models are dangerous because they create false confidence. Every
solver model needs:

- known-answer checks against the C implementation or a clean reduced-round
  reference;
- test vectors for the exact reduced-round variant under study;
- clear labels for assumptions and approximations;
- command lines, tool versions, and status labels in every generated summary.

