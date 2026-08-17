# OrbitTrace annual-density bifiltration v1 — target-excluded GMN ranking/recovery protocol

## Scientific role

This is the **one GMN truth endpoint** authorized by the positive zero-label annual-density bifiltration scale diagnostic.

It tests whether the already-frozen bifiltration candidate universe and already-frozen persistence-area order convert the structural cross-scale gain into known-shower recovery **without reproducing TopoModal's recurring early-ranking/MRR failure**.

This is permanent target-excluded GMN 2022/2023 development data, not pristine external validation. It is not a full-GMN comparison against the density-synchronous recurrent-EOM champion. SonotaCo must not be accessed here.

## Frozen successor input

The successor candidates are not regenerated or reranked in this endpoint. They must be downloaded from the binding zero-label run:

- source run: `32036777809`
- artifact: `9291012921`
- artifact digest: `sha256:0c44eb4039a2504ba815ad0511538300b576f7edc5a90bb1b8dee33d5be53605`
- required file: `ANNUAL_DENSITY_BIFILTRATION_PRETRUTH_V1.json`
- required file SHA-256: `63519bbd8a95b0bd5db0d0f5fdccbdb67b3f1dac0158529bb808f4c798170b0b`
- required structural result: `ANNUAL_DENSITY_BIFILTRATION_SCALE_V1.json`
- required structural result SHA-256: `d930e9a8221cbe6b56026618f513f3f8b84143f2f43deb0a5b1ccc1ca7e4bbe7`
- required interpretation: `SUPPORTS_ANNUAL_DENSITY_BIFILTRATION_CROSS_SCALE_COHERENCE`

The successor order is exactly the order frozen before the structural result:

1. bifiltration persistence area descending;
2. member count descending;
3. membership SHA-256 ascending.

The candidate rows in the frozen artifact already carry that rank. This endpoint must verify the ordering but may not recompute, transform, blend, prune, quota, interleave, or otherwise modify it.

## Frozen GMN panel construction

Reconstruct only the exact event universes and exact recurrent-EOM comparator required for evaluation, using the authoritative frozen sparse-recovery runtime.

- years: `2022, 2023`
- inclusive protected interval `[20°,55°]` excluded before all method operations
- denominators: `128` and `1024`
- buckets: `0,1,2,3`
- subset rule: `SHA256('ORBITTRACE_SCALE_STRESS_V1|' + event_id) mod denominator == bucket`
- exact recurrent-EOM HDBSCAN v1 comparator
- exact GMN metrics implementation already used by the TopoModal sparse-recovery endpoint

Required source pins:

- `orbittrace_topomodal_sparse_recovery_v1/run_development.py` blob `752df8212ce601227f6e9170b0fe994ba06b515d`
- recurrent-EOM implementation blob `30ac3fa3bc47910370df528fcf3ae8ecb6277b47`
- recurrent development wrapper blob `fdc4f3f6e037014aadfcc3ce41b7344aa0a80b2c`
- GMN utility SHA-256 `dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990`
- pooled-year-centroid support result SHA-256 `fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b`

Before truth evaluation, reconstruct all eight pooled subset universes and recurrent-EOM candidate lists, and freeze a new endpoint prelabel file containing:

- exact subset event-universe SHA-256;
- annual event-ID sets;
- exact recurrent candidate memberships/order;
- exact successor candidate memberships/order copied from the immutable bifiltration artifact;
- equal-budget `K` for each subset.

The endpoint must fail closed before truth unless every successor event ID belongs to the corresponding reconstructed subset universe, every successor rank is contiguous and follows the already-frozen order, and every successor list has at least `K` candidates.

## Equal-budget evaluation

For each denominator/bucket subset:

`K = complete recurrent-EOM candidate count for that pooled subset`.

Evaluate:

- recurrent-EOM: all `K` recurrent candidates;
- bifiltration successor: first `K` frozen persistence-area-ranked candidates.

For each year independently, evaluate both pooled candidate lists after intersection with that year's event universe using the exact existing GMN metric implementation.

This gives `2 scales × 4 buckets × 2 years = 16` truth panels.

Record:

- qualified matches;
- recovered@25;
- recovered@50;
- recovered@100;
- recovered@500;
- MRR;
- top-100 dominant precision;
- median top-500 fragmentation.

The full bifiltration list may also be evaluated as a clearly labeled diagnostic ceiling, but it cannot affect the verdict.

## Frozen promotion gate

Use the exact established TopoModal sparse-recovery gate structure. This avoids inventing a success standard after the bifiltration structural result.

For the **fine scale (`d=1024`)**, all five must pass:

1. successor total qualified matches is **strictly greater** than recurrent-EOM;
2. successor qualified matches are nonlower in at least `6/8` annual panels;
3. mean MRR is not lower;
4. mean top-100 dominant precision is not lower;
5. mean median-fragmentation is not higher.

For the **coarse scale (`d=128`)**, all five must pass:

6. successor total qualified matches is not lower than recurrent-EOM;
7. successor qualified matches are nonlower in at least `6/8` annual panels;
8. mean MRR is not lower;
9. mean top-100 dominant precision is not lower;
10. mean median-fragmentation is not higher.

All ten gates are mandatory.

Exact PASS verdict:

`PASS_ANNUAL_DENSITY_BIFILTRATION_V1_GMN_RANKING_RECOVERY`

Otherwise:

`FAIL_ANNUAL_DENSITY_BIFILTRATION_V1_GMN_RANKING_RECOVERY`

A PASS means the pre-frozen persistence-area ordering survives the same sparse-scale recovery/early-ranking standard that prior TopoModal selectors failed. It still does not establish superiority to the full-GMN density-synchronous recurrent-EOM champion; a separately preregistered full-GMN endpoint would be required before promotion.

A FAIL permanently closes the persistence-area-ranked bifiltration v1 lane. The positive structural result remains valid but may not be rescued by a different ranking.

## No-rescue rule

After a technically valid result, do not try:

- support × area, log area, square-root area, normalized area, rank transforms;
- Pareto layers/frontiers;
- alternate membership-size tie rules;
- density, station, orbit, annual-confirmation, predictive-edge, significance, or recurrence score blends;
- lineage quotas/interleaving;
- alternate threshold grids or one-parameter slices;
- route/scale/year/bucket-specific rules;
- alternate equal-budget definitions;
- changing support, graph, physical scales, subset denominators/buckets/salt;
- another SonotaCo-informed reranker.

## Firewall

Forbidden throughout:

- OrbitTrace target information/events;
- protected `[20°,55°]` events;
- SonotaCo 2013/2014;
- ASFN/EFN event-level data;
- AMOS;
- MAARSY;
- DMS;
- any pristine external endpoint;
- post-result parameter search.
