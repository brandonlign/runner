# OrbitTrace cross-year-core HDBSCAN v1 — frozen protocol

## Status

Protocol-only freeze before implementation and before any technically valid scientific outcome.

This successor starts from the already-qualified recurrent-EOM HDBSCAN v1 GMN lineage at commit `e3ad80dd4d685b32917af9e2e6d76cb2b76857d4`. It does not use SonotaCo, AMOS, EFN, GMN 2020/2021, OrbitTrace target information/events, MAARSY, or DMS to choose its mechanism.

The permanent development panel is the exact target-excluded GMN 2022+2023 pool used by recurrent-EOM v1. The protected solar-longitude interval `[20 deg,55 deg]` remains inaccessible.

The first technically valid GMN scientific outcome is binding. No result-informed threshold, k, metric, feature, transform, weight, blend, hierarchy rule, extraction rule, or ranking rescue is authorized.

## 1. Scientific parent

The parent comparator is exact recurrent-EOM HDBSCAN v1:

- implementation Git blob `30ac3fa3bc47910370df528fcf3ae8ecb6277b47`;
- GMN runner Git blob `fdc4f3f6e037014aadfcc3ce41b7344aa0a80b2c`;
- binding GMN run `31827903547`;
- artifact `9229646556`;
- result SHA-256 `433c641f57122b244b9476f5cbcb5e6f82956d9467270a9f24945600a32d2106`.

Parent configuration:

- GEO6 = `(cos(sol), sin(sol), sin(sun_lon)*cos(ecl_lat), cos(sun_lon)*cos(ecl_lat), sin(ecl_lat), vg/72)`;
- `min_cluster_size=10`;
- `min_samples=10`;
- Euclidean metric;
- pooled 2022+2023 hierarchy;
- annual EOM contributions normalized by accessible event count in each year;
- recurrent stability `E_rec(C)=min(E_2022(C),E_2023(C))`;
- EOM extraction using recurrent stability;
- ranking by descending recurrent stability, descending ordinary stability, descending member count, deterministic family ID.

## 2. Independent scientific motivation

Ordinary HDBSCAN defines a point's core distance from local density in the pooled sample. In a repeated-observation discovery problem, a dense patch that exists primarily in only one observing year can therefore help create a low mutual-reachability path even when the corresponding physical structure has weak support in the other year.

A distinct way to encode recurrence is to move the repeated-observation requirement **into the density geometry before the hierarchy exists**.

For every event, estimate its local density scale only from the opposite observing year. A point is therefore considered locally dense only when the other year's point cloud independently provides nearby support. This changes HDBSCAN's mutual-reachability geometry and hence the minimum-spanning tree and hierarchy itself; it is not a new scalar EOM combiner, hierarchy post-filter, component matcher, rank fusion, or consensus-EOM rescue.

The neighborhood order `k=10` is inherited exactly from the parent's already-fixed `min_samples=10`; it is not selected from a new search.

## 3. Sole new mechanism: opposite-year core distance

Let `X_22` and `X_23` be the exact target-excluded GEO6 points for GMN 2022 and 2023.

For every point `x` in year `y`, define its cross-year core distance

`c_cross(x) = distance from x to its 10th nearest GEO6 point in the opposite year`.

Rules:

- Euclidean GEO6 distance is unchanged;
- nearest-neighbor order uses exact floating distance, then deterministic event ID for ties;
- self-exclusion is irrelevant because the search pool is the opposite year;
- no radius cutoff, clipping, winsorization, normalization, year weighting, or density rescaling is used;
- if the opposite-year pool has fewer than 10 points, execution fails closed (this cannot occur in the intended GMN panel).

For every unordered pair of pooled points `(x_i,x_j)`, define cross-year mutual reachability

`mrd_cross(i,j) = max(c_cross(x_i), c_cross(x_j), ||x_i-x_j||_2)`.

The complete pooled hierarchy is then the exact single-linkage hierarchy induced by the minimum-spanning tree of the complete graph under `mrd_cross`.

This replaces only HDBSCAN's ordinary pooled core-distance geometry. No event is deleted or reweighted.

## 4. Condensation and extraction

After the cross-year mutual-reachability MST and single-linkage hierarchy are constructed:

- condense with exact `min_cluster_size=10`;
- preserve `allow_single_cluster=False`;
- compute the same per-year normalized EOM contributions on the resulting condensed hierarchy as recurrent-EOM v1;
- compute `E_rec(C)=min(E_2022(C),E_2023(C))` exactly as in the parent;
- perform the exact same recurrent-EOM scalar EOM extraction;
- rank candidates by the exact inherited recurrent-EOM ranking rule.

Thus the **only scientific change** relative to recurrent-EOM v1 is the core-distance / mutual-reachability geometry used to construct the hierarchy.

No consensus-EOM selection, componentwise objective, alternate annual combiner, balance term, extra feature, post-filter, or reranker is allowed.

Deterministic candidate prefix: `XYCORE1`.

## 5. Mandatory engineering exactness gate before GMN science

The production implementation may use an optimized nearest-neighbor/MST algorithm, but no optimized result is scientifically eligible until it passes a zero-truth exactness audit against a dense mathematical reference on fixed synthetic panels.

The reference implementation must:

1. explicitly construct the full pairwise Euclidean matrix for small synthetic two-year panels;
2. compute each point's exact opposite-year 10th-neighbor core distance;
3. construct the full dense `mrd_cross` matrix;
4. compute a deterministic MST;
5. construct the single-linkage hierarchy;
6. condense at min cluster size 10;
7. apply the exact inherited recurrent-EOM stability and extraction logic.

The optimized implementation must match the dense reference on every preregistered synthetic fixture in:

- all `c_cross` values bitwise or, if a library's deterministic floating reduction order prevents bit identity, within an absolute tolerance fixed in the engineering audit **before** any GMN execution;
- sorted MST edge-weight multiset;
- single-linkage merge distances and component sizes;
- condensed-tree parent/child/lambda/child-size structure up to deterministic node relabeling;
- selected cluster partition;
- complete candidate memberships and ranking.

Synthetic fixtures must include:

- two separated recurrent clusters plus noise;
- one dense one-year-only cluster with diffuse opposite-year support;
- unequal annual sample sizes;
- exact-distance ties;
- nested-density structure.

Any mismatch is an engineering no-result. It may be repaired only without changing the mathematical protocol above.

## 6. Binding GMN development evaluation

Only after the exactness gate passes, run once on the exact recurrent-EOM target-excluded GMN 2022+2023 development panel.

Before shower truth is opened, persist and hash-freeze for parent and successor:

- exact input IDs and GEO6 hash;
- cross-year core-distance hash;
- MST identity sufficient to reproduce the hierarchy;
- condensed-tree identity;
- selected nodes;
- every candidate membership;
- every ranking score;
- complete deterministic pooled candidate order.

Evaluation semantics are copied from the recurrent-EOM parent:

- eligible known shower = at least 4 labeled events in the evaluated year;
- qualified match = dominant-shower precision >=0.5 and overlap >=4;
- pooled candidate order is held fixed and memberships are restricted by year only for evaluation;
- report recovered @25/@50/@100/@500, full-catalogue qualified matches, top-100 dominant precision, MRR, and median top-500 fragmentation.

## 7. Frozen promotion gate versus recurrent-EOM v1

`PASS_CROSSYEAR_CORE_HDBSCAN_V1_GMN_DEVELOPMENT` requires all of:

1. recovered@100 strictly higher in at least one year and not lower in the other;
2. recovered@50 not lower in either year;
3. top-100 dominant precision not lower in either year;
4. MRR not lower in either year;
5. median top-500 fragmentation not higher in either year;
6. successor hierarchy differs from parent hierarchy, proved by a different MST edge-weight/condensed-tree identity and at least one candidate-membership or selected-node difference.

Recovered@25, recovered@500, and full-catalogue qualified matches are reporting-only.

Failure token:

`FAIL_CROSSYEAR_CORE_HDBSCAN_V1_GMN_DEVELOPMENT`

A valid failure permanently closes this exact opposite-year-10NN core-distance mechanism. No k sweep, same/opposite-year blend, min/max/geometric core-distance combiner, local scaling, clipping, radius threshold, metric change, EOM alteration, or ranking rescue may be selected from the result.

A PASS authorizes only a separately frozen next-stage benchmark. It does not authorize protected target access.

## 8. Novelty boundary

If supported, the methodological claim is limited and explicit: **cross-year-core hierarchical density clustering**, an HDBSCAN-derived method in which local core density is estimated exclusively from an independent repeated-observation panel before mutual-reachability hierarchy construction, followed by the already-defined recurrence-aware EOM extraction.

HDBSCAN and recurrent-EOM remain explicit parents. No claim of inventing density clustering from scratch is permitted.
