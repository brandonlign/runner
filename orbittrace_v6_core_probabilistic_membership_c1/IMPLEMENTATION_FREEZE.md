# C1 implementation freeze

Frozen before the current fanout-v2 v6 scientific verdict and before any v6 matched-literature result.

## Canonical C1 source

- `run_development.py` SHA-256: `113c579f2058126e93b93a3534aaa6108d3e827c667552ecd41ff321d7a5e3da`
- repaired catalogue-v6 source SHA-256 required at runtime: `257aab9d0f4d710a1b62af6088cfb9c0939062018d44dbacd074b4e7898eaa24`
- frozen P1 scientific source SHA-256 required at runtime: `e7847e067bab8d07038c998359ccbf0ca6e2ccf257f27f27f4aef999cc7a0508`
- exact promoted-v8 evaluator source commit: `c9d6c44704013ba0c9430100e98a29a56b453304`

## Exact shared P1 membership engine

C1 does not maintain a second copy of the probabilistic membership equations. It imports the already source-audited transfer implementation:

- commit `785554905113626bebffecdd441616238eb76b04`
- file `orbittrace_probabilistic_membership_p1_literature/run_pretruth_panel.py`
- Git blob `498daf762bc82a664679998ea751feecff8033de`
- function `apply_exact_p1_membership`

The only adaptation is setting that module's frozen year tuple from `(2023, 2025)` to `(2022, 2023)` before calling the function. The inner/outer probabilities, OAS covariance, Garwood background, stream amplitude, conflict ordering, posterior responsibility threshold, immutable-seed rule, and non-recursive semantics therefore share executable code with P1 rather than being reimplemented for C1.

## Exact v6 family and rank interface

C1 reconstructs the primary v6 family list from the two fanout year checkpoints using the repaired-v6 function:

`build_family_track_v6(old, all_components, base, "v3")`

The returned primary-family list is the exact frozen primary rank. fixed4 rescue components are never passed to the C1 seed universe.

## Evaluator integrity

Before C1 can receive a scientific verdict, the inherited exact `mult.evaluate_order` evaluator is run on the original reconstructed v6 seed families/order and must reproduce the authoritative v6 result's qualified matches, recovery@100, top-100 dominant precision, MRR, and macro F1 to the frozen tolerances in source.

The C1 expanded membership payload, v6 rank hash, and v6 seed-family hash are serialized and SHA-256 frozen **before** the first `evaluate_order` call or the first access to `v6_result["evaluation"]`.

Any baseline mismatch is a technical/integrity failure, not a C1 scientific failure and not permission to change the evaluator.

No C1 scientific data have been executed by this freeze.