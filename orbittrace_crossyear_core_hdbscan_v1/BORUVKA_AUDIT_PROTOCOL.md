# Cross-year-core HDBSCAN v1 — scalable Boruvka exactness audit

## Status

Frozen before the first technically valid scalable-equivalence outcome. This is a **zero-scientific-data engineering audit only**. It authorizes no GMN catalogue access, no shower truth, no SonotaCo, no AMOS, no OrbitTrace target information/events, no MAARSY, and no DMS.

The parent scientific protocol remains the already-frozen `orbittrace_crossyear_core_hdbscan_v1/PROTOCOL.md` at Git blob `980d2f26d6477ff80d1b57606ee86ae96bebe972`. Nothing in this audit may change its cross-year-core mathematics, `k=10`, GEO6 metric, condensation, recurrent-EOM extraction, ranking, or promotion gate.

## Frozen source identities

- dense mathematical reference: `orbittrace_crossyear_core_hdbscan_v1/reference.py`, Git blob `5380dd68a01c0f35c3e212972b840ae7b9dea7aa`;
- scalable Boruvka adapter: `orbittrace_crossyear_core_hdbscan_v1/boruvka_adapter.py`, Git blob `a7fec249d82fef23158ae52897ae28f9d0126153`;
- inherited recurrent-EOM implementation: `orbittrace_recurrent_eom_hdbscan_v1/recurrent_eom.py`, Git blob `30ac3fa3bc47910370df528fcf3ae8ecb6277b47`;
- HDBSCAN runtime: exact package version `0.8.43`;
- NumPy `2.1.3`, SciPy `1.14.1`, scikit-learn `1.7.1`, Python `3.11`.

The dense reference itself already passed its separate zero-data audit in run `31846715847`, artifact `9236150866`, digest `sha256:dca493b29b9a5a1004fb621fddcfc17ae33ee6b71106d1878812e93b98ba1bea`.

## Audit fixtures

Exactly five deterministic synthetic two-year fixtures are used, all fixed before outcome:

1. two recurrent clusters plus background/noise;
2. a tight one-year-only structure with diffuse/missing opposite-year support;
3. unequal annual sample sizes;
4. exact geometric distance ties with deterministic event IDs;
5. nested-density structure.

No scientific catalogue row or label may be loaded by the audit process or workflow.

## Exact comparison contract

For every fixture, compute both the dense reference and the scalable Boruvka result from the identical `X`, year vector, IDs, `k=10`, and `min_cluster_size=10`.

The Boruvka result must satisfy all of the following:

1. every cross-year core distance matches the dense reference with `rtol=0` and absolute tolerance **`1e-12`**, fixed here before execution;
2. the sorted MST edge-weight multiset matches with the same `1e-12` tolerance;
3. sorted single-linkage merge-distance/component-size pairs match with the same tolerance;
4. the condensed hierarchy matches after canonicalizing every cluster node by its exact descendant event-ID set, allowing only arbitrary numeric node relabeling;
5. the recurrent-EOM selected partition is exactly identical after canonicalizing by member event IDs;
6. the complete recurrent-EOM candidate ordering is identical in membership and member count, with recurrent and ordinary stability scores equal within `1e-12`;
7. on the exact-tie fixture, two independent Boruvka adapter executions are deterministic under the same canonical comparisons.

Different MST edge endpoints are permitted only when the MST weight multiset, single-linkage hierarchy, condensed hierarchy, partition, and ranking remain equivalent under the rules above. This handles mathematically non-unique equal-weight MSTs without weakening any scientific endpoint.

## Outcome semantics

Pass token:

`PASS_CROSSYEAR_CORE_BORUVKA_EXACTNESS_AUDIT_V1`

Any mismatch produces a technical engineering failure/no-result. Such a failure may justify only an implementation repair that preserves every scientific formula, parameter, and comparison tolerance above. It may not alter `k`, distance metric, cross-year core definition, mutual reachability, condensation, EOM extraction, ranking, or the future GMN promotion gate.

A PASS proves only that the scalable implementation reproduces the frozen synthetic mathematical reference. It is a prerequisite to a separately frozen one-shot target-excluded GMN 2022+2023 development execution; it does **not** itself authorize that execution or any protected-data access.
