# OrbitTrace window-owned persistence ranking evaluator repair v1

## Role

This is an **engineering-only evaluator repair** for the already-frozen scientific successor `window-owned persistence ranking v1`. It is not a new successor and may not generate, alter, filter, merge, split, rerank, or otherwise change any candidate membership or rank.

The original truth-bearing workflow run `31956064964` completed the frozen candidate generator and persisted its prelabel artifact before truth evaluation, but then aborted while recomputing the recurrent-EOM parent under a dependency-altered NumPy environment. The successor itself was never evaluated: the original source calls `verify_parent_metrics(parent_metrics)` before the first call that computes `successor_metrics`.

## Immutable scientific input

The only permitted successor input is:

- source run: `31956064964`
- source artifact id: `9266239856`
- source artifact name: `orbittrace-window-owned-persistence-ranking-v1`
- file: `WINDOW_OWNED_PERSISTENCE_RANKING_V1_PRELABEL.json`
- SHA-256: `beae39cc987100373d236a19e656415dd63f183cfbbb4202345e0cde7e3b6f11`
- frozen successor candidate count: `1028`
- frozen both-year candidate count: `1014`

The evaluator must preserve the candidate list in file order. The stored ranks must be exactly `1..1028`. No reconstruction with Persistable is allowed and Persistable must not be installed in the repair runtime.

## Frozen comparison

The comparator is the immutable historical recurrent-EOM HDBSCAN v1 result, not a fresh parent recomputation:

### 2022
- recovered@25: 22
- recovered@50: 45
- recovered@100: 89
- recovered@500: 193
- top-100 dominant precision: 0.7856486013
- MRR: 0.0224982696
- qualified matches: 236
- fragmentation median top500: 1.0

### 2023
- recovered@25: 23
- recovered@50: 46
- recovered@100: 89
- recovered@500: 192
- top-100 dominant precision: 0.7867680237
- MRR: 0.0220239289
- qualified matches: 244
- fragmentation median top500: 1.0

These are exactly the `EXPECTED_PARENT` constants frozen in the original successor source. They may not be recomputed or changed.

## Frozen evaluator and gates

Use the same historical `parent.metrics(...)` evaluator from the recurrent-EOM source on the frozen successor candidate list and the same sealed target-excluded GMN 2022/2023 shower truth used by the original workflow.

For each year, all original gates remain mandatory:

- recovered@25 not lower
- recovered@50 not lower
- recovered@100 not lower
- recovered@500 not lower
- top-100 dominant precision not lower
- MRR not lower
- qualified matches not lower
- fragmentation median top500 not higher

Additionally, at least one year must have a strict recovered@100 improvement. This is the exact original implementation gate and is not changed in the repair.

## Runtime repair

Use the historical parent evaluation runtime with NumPy `2.1.3`; do not install Persistable. The only engineering change is removal of the dependency-induced NumPy downgrade and removal of the unnecessary fresh parent reconstruction. The frozen successor prelabel is evaluated directly against the immutable parent controls.

## Firewall

Protected solar longitude `[20°,55°]` remains excluded. OrbitTrace target information/events, SonotaCo 2013/2014, ASFN/EFN event rows, AMOS, MAARSY, and DMS may not be accessed. The repair may access only the already-authorized target-excluded GMN 2022/2023 truth required for this frozen development endpoint.

## Interpretation

The first technically valid repair result is binding for this exact successor. A FAIL closes this ranking architecture; no result-informed ranking/gate/membership rescue is allowed. A PASS authorizes only a separately frozen exposed SonotaCo benchmark if that benchmark protocol was frozen before this repaired result is opened.
