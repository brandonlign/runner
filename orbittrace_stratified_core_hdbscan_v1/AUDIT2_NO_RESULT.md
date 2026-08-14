# Stratified-core HDBSCAN v1 zero-truth audit 2 — Boruvka initialization no-result

**Classification: engineering-only synthetic equivalence failure. No GMN catalogue/truth, SonotaCo, EFN, OrbitTrace target information/events, protected target-region data, MAARSY, or DMS access.**

Run `31844583132`, job `94908307589`, head `4022894ffd79d7e1cb642a9d4137b256355ed637` passed frozen source pins and the corrected brute-force balanced-core mechanics. It then failed the first synthetic standard-core injection identity case:

`seed 1103: injected standard-core partition differs from HDBSCAN`

The supplied core distances were the ordinary pooled `min_samples=10` HDBSCAN core distances. Therefore this is an injection-state failure, not a failure of the frozen balanced 5+5 scientific core definition.

Upstream HDBSCAN 0.8.43 source shows why: the normal `KDTreeBoruvkaAlgorithm(min_samples=10)` constructor performs a special first candidate-edge pass over the pooled 10-nearest-neighbor list and immediately calls compiled `update_components()` before `spanning_tree()`. The frozen min_samples=0 injection constructor intentionally suppresses that pass, so simply overwriting `core_distance_arr` and calling `spanning_tree()` does not recreate the same approximate-Boruvka initialization state when `approx_min_span_tree=True`.

No scientific outcome exists. Only exact initialization/injection plumbing may be repaired. The 5+5 neighbor split, max annual core, HDBSCAN parameters, recurrent-EOM extraction, ranking, and binding gate remain frozen.
