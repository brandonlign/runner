# OrbitTrace v27 — post-membership feature freeze

## Scope

This is a **pretruth feature/source freeze only**. It does not train a successor ranker, open SonotaCo truth, compare against Sugar/HDBSCAN, or authorize MAARSY/DMS/OrbitTrace target access.

The exposed-development diagnosis after v26 identified an architectural mismatch: the current 71-dimensional v22/v24 ranking matrix is built on pre-expansion family cores, while the exact frozen #461/v17 joint-conformal membership expansion is applied afterward and literature F1 is evaluated on those expanded final memberships.

v27 therefore does not change candidate generation, ordering, or membership. It freezes label-free descriptors of the **already-fixed final v19 top-100 expanded families** so a later separately named successor may rerank only those same 100 objects after membership construction.

## Two-stage architecture boundary

The future method boundary is fixed here:

1. exact v19 remains the first-stage full-catalogue ranker;
2. exact v19 top 100 only are passed through the exact frozen joint-conformal membership expansion;
3. a later post-membership ranker may reorder only those same 100 expanded families;
4. families 101+ remain in exact v19 order and are never promoted into the post-membership set without first being selected by stage 1.

This prevents a later ranker from comparing expanded top-100 families against unexpanded lower-ranked families and makes the deployment object identical to the object scored by the literature evaluator.

## Identity requirements

For each exposed matched route (`sugar`, `hdbscan`), v27 must regenerate the exact v22/v24 pre-membership state from label-free SonotaCo rows and reproduce:

- 71-dimensional base feature SHA-256:
  - Sugar: `486c247d12bd769f281444b4b3b9adf0ec3cd517dc88485f3deccffd8e395f1f`
  - HDBSCAN: `d25f5e7899b2ab5dba7e7c1d1f6269896fee34714492bb53264c659db32c310d`
- centroid SHA-256:
  - Sugar: `6f920ede2497b0cd1a5a8e303a6e87a6217fc8919deb4c81b131b1e5a5f20e91`
  - HDBSCAN: `90504db13491ba83a4dffb35892d3bd87764827b99e497bc56c80425700eab79`
- exact expanded v19 family-membership canonical SHA-256:
  - Sugar: `911bbc1d763f79ee661863a6d5c2cc98d97d0debd276e64461d45a5447c7bfeb`
  - HDBSCAN: `7137a5c0892e5d316db38915ff164f2a8fb6e8fbe8e0ed2cfa063097968a1895`

Any identity mismatch invalidates the feature freeze.

## Frozen post-membership descriptors

Exactly **16** new label-free features are frozen for each of the exact v19 top-100 expanded families. No feature subset or alternate summary is evaluated here.

### A. Seven previously defined URC-v2 cohesion descriptors

Apply the exact pre-SonotaCo URC-v2 feature definitions to the **expanded final event IDs** while retaining the original frozen family centroids:

1. `expanded_member_count_min_year`
2. `expanded_member_count_max_year`
3. `expanded_member_count_year_balance`
4. `expanded_member_distance_median`
5. `expanded_member_distance_q90`
6. `expanded_member_distance_max`
7. `expanded_year_q90_distance_max`

The physical distance function and quantile definitions are unchanged from the historical URC-v2 source.

### B. Three previously used expansion-size forms

Using the same feature forms already used in the pre-SonotaCo #846 event-membership work:

8. `log1p_core_member_count`
9. `log1p_added_member_count`
10. `added_to_core_ratio`

Core membership is the exact family membership before #461/v17 expansion. Added membership is set difference between the final expanded membership and that core.

### C. Six frozen conformal-confidence descriptors

The exact #461/v17 expansion already computes, for every accepted target-event/family pair, label-free:

- second-nearest source support distance `d2`;
- trajectory residual;
- joint conformal p-value.

v27 records those quantities for the **winning accepted assignments only**, without changing the assignment key or membership. For each family, across all accepted additions in both years, freeze:

11. `accepted_d2_median`
12. `accepted_d2_q90`
13. `accepted_trajectory_residual_median`
14. `accepted_trajectory_residual_q90`
15. `accepted_neglog_joint_p_median`
16. `accepted_neglog_joint_p_q90`

where `accepted_neglog_joint_p = -log(joint_conformal_p)`.

If a top-100 family receives no additions, fixed fail-closed sentinels are used rather than zero-valued apparent perfection:

- d2 summaries = exact frozen density ceiling `1.5`;
- trajectory summaries = exact frozen trajectory ceiling `1.5`;
- `-log(p)` summaries = `-log(0.05)`, using the exact frozen conformal alpha.

Median and q90 are reused from the existing pre-SonotaCo cohesion-summary vocabulary; no additional quantile is introduced.

## Expansion equivalence

The v27 instrumented expansion must be scientific-code equivalent to exact v17:

- same top-100 family set and order;
- same source-year seeds;
- same activity arc;
- same density/trajectory/conformal calculations;
- same `d <= 1.5`, residual `<= 1.5`, p `> 0.05` acceptance;
- same event-level winner key `(-p, Fisher score, original rank, family ID)`;
- same original-seed preservation;
- byte-for-science identical expanded event-ID sets.

Confidence collection is observational only and cannot affect assignment.

## Output

For each route, freeze:

- exact top-100 family IDs in v19 order;
- exact 71 base features restricted to those IDs;
- exact 16 post-membership features;
- combined 87-dimensional top-100 matrix;
- feature names and per-feature provenance;
- exact expanded top-100 family payload;
- identity/hash manifest with all truth/external/target access flags false.

## Prohibitions

- no truth download or label evaluation;
- no successor model fit;
- no feature selection or ablation;
- no membership threshold/assignment change;
- no expansion beyond exact v19 top 100;
- no comparator-budget-specific logic;
- no MAARSY, DMS, OrbitTrace target information, target-region event, or 20°–55° target-content access.

A successful v27 run authorizes only a separately frozen exposed-development ranking experiment using this exact 87-feature top-100 interface. It does not itself establish any scientific superiority result.
