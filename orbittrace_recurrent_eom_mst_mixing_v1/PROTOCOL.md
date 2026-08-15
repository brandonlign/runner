# OrbitTrace recurrent-EOM MST year-mixing v1 — frozen protocol

## Status

Frozen before implementation and before the first scientific outcome of this successor.

The scientific parent is exact recurrent-EOM HDBSCAN v1, selected as the current OrbitTrace paper/development method on PR #1243. This experiment tests one new **rank-only** mechanism. It does not alter the pooled GEO6 representation, HDBSCAN hierarchy, core distances, mutual-reachability distances, selected recurrent-EOM nodes, candidate memberships, minimum cluster size, minimum samples, or any truth definition.

Scientific firewall remains binding:

- protected solar longitude `[20 deg,55 deg]` is inaccessible;
- no OrbitTrace target information/events;
- no MAARSY or DMS scientific access;
- no SonotaCo scientific value enters this GMN development selection;
- no AMOS access or outreach;
- development data are target-excluded GMN 2022+2023 only;
- the complete successor order must be frozen before shower truth is opened;
- the first technically valid result is binding;
- no post-result cap, exponent, weight, threshold, blend, alternate graph statistic, HDBSCAN parameter, rank fusion, or other rescue is allowed.

## 1. Exact parent

Pinned recurrent-EOM implementation Git blob:

`30ac3fa3bc47910370df528fcf3ae8ecb6277b47`

Pinned recurrent-EOM development runner Git blob:

`fdc4f3f6e037014aadfcc3ce41b7344aa0a80b2c`

Binding parent GMN run `31827903547`, artifact `9229646556`, result SHA-256 `433c641f57122b244b9476f5cbcb5e6f82956d9467270a9f24945600a32d2106`.

Exact parent configuration:

- GEO6 = `(cos(sol), sin(sol), sin(sun_lon)*cos(ecl_lat), cos(sun_lon)*cos(ecl_lat), sin(ecl_lat), vg/72)`;
- `min_cluster_size=10`;
- `min_samples=10`;
- Euclidean metric;
- HDBSCAN EOM hierarchy;
- `cluster_selection_epsilon=0`;
- `allow_single_cluster=False`;
- one pooled target-excluded GMN 2022+2023 hierarchy;
- recurrent stability `E_rec(C)=min(E_2022(C),E_2023(C))`;
- recurrent-EOM selected nodes and memberships are fixed by that scalar stability;
- parent ranking is descending recurrent stability, descending ordinary HDBSCAN stability, descending member count, ascending deterministic family ID.

The binding recurrent parent emitted 2,097 candidates. Exact parent metrics that must reproduce before this successor is interpreted:

### 2022

- recovered@25 = 22
- recovered@50 = 45
- recovered@100 = 89
- recovered@500 = 193
- top-100 dominant precision = 0.7856486012780942
- MRR = 0.022498269587309373
- qualified matches = 236
- median top-500 fragmentation = 1.0

### 2023

- recovered@25 = 23
- recovered@50 = 46
- recovered@100 = 89
- recovered@500 = 192
- top-100 dominant precision = 0.7867680236864514
- MRR = 0.0220239288966045
- qualified matches = 244
- median top-500 fragmentation = 1.0

Any failure to reproduce the exact recurrent parent is an engineering no-result, not a scientific result for this successor.

## 2. Motivation

Recurrent-EOM measures whether both observing years contribute density persistence to the same hierarchy branch. It does not distinguish two geometrically different situations that can have similar annual persistence:

1. 2022 and 2023 members are locally interleaved throughout the same density structure; or
2. 2022 members occupy one geometric subregion and 2023 members another, while both remain inside the same selected HDBSCAN branch.

A physical recurring meteor stream should preferentially exhibit the first pattern: repeated observations sample the same local phase-space structure rather than two year-segregated pieces.

The exact HDBSCAN mutual-reachability minimum-spanning tree already encodes the local density geometry used to create the hierarchy. Therefore year-label mixing can be measured on that existing graph without introducing a new neighborhood radius, k, feature representation, clustering fit, or learned model.

This mechanism is distinct from prior closed lanes:

- it does not alter core distance or the hierarchy as cross-year-core did;
- it does not require reciprocal annual cluster matches as reciprocal-transfer did;
- it does not change the EOM stability combiner as consensus-EOM or density-synchronous EOM did;
- it is not the prior member-cloud MST bottleneck feature: that experiment constructed separate family-year Prim trees in a different residual representation. Here the graph is the **exact pooled HDBSCAN mutual-reachability MST**, and the statistic is cross-year edge mixing.

## 3. Sole new statistic: fixed-count year mixing on the HDBSCAN MST

Fit the exact parent HDBSCAN model to the exact pooled GEO6 matrix with the sole engineering flag `gen_min_span_tree=True` so the already-computed mutual-reachability MST is exposed. This flag must not change the condensed hierarchy, recurrent selected nodes, labels, memberships, or parent metrics. Those identities are mandatory pre-outcome checks.

For a recurrent-EOM selected cluster `C`, let:

- `n(C)` be its member count;
- `n_1(C)` and `n_2(C)` be its two annual member counts;
- `m(C)` be the number of edges in the exposed global HDBSCAN MST whose two endpoints are both members of `C`;
- `x(C)` be the number of those internal edges whose endpoints come from different observing years.

Conditioning on the cluster's fixed graph and fixed annual counts, a random permutation of the year labels gives any edge cross-year probability

`q(C) = 2 n_1(C) n_2(C) / [ n(C) (n(C)-1) ]`.

Therefore the exact expected number of cross-year internal edges under random year mixing is

`mu(C) = m(C) q(C)`.

Define the parameter-free mixing enrichment

`M(C) = x(C) / mu(C)`

when `m(C)>0` and both annual counts are positive. Otherwise `M(C)=0`.

Interpretation:

- `M≈1`: year mixing is approximately random on the local density graph;
- `M<1`: years are locally segregated;
- `M>1`: years are more interleaved than random assignment with the same annual counts.

No clipping, log transform, pseudocount, variance normalization, p-value conversion, edge-weighting, distance cutoff, k, radius, or alternate null is permitted.

## 4. Successor score and ordering

Candidate memberships remain exactly those of recurrent-EOM. The sole changed scalar used for ordering is

`S_mix(C) = E_rec(C) * M(C)`.

The complete successor order is:

1. descending `S_mix`;
2. descending exact parent `E_rec`;
3. descending ordinary HDBSCAN stability;
4. descending member count;
5. ascending deterministic membership-derived family ID.

The deterministic successor ID prefix is `REOMMST1`; the prefix is only provenance and cannot influence membership or the preceding numeric ordering keys.

No candidate is deleted or added. No EOM selection decision is changed. No v31 score, literature identity, shower label, probability, HDBSCAN outlier score, or learned feature enters the ordering.

## 5. Pretruth engineering invariants

Before shower truth can be opened, the binding runner must prove all of:

1. exact event counts `315024 / 423658` and pooled `738682`;
2. exact protected `[20,55]` exclusion;
3. exact recurrent-EOM implementation identity;
4. HDBSCAN with `gen_min_span_tree=True` produces the exact recurrent selected-node set obtained through the frozen parent method;
5. recurrent candidate memberships are exact and candidate count is 2,097;
6. the parent recurrent order and metrics reproduce the binding parent after truth is eventually opened;
7. the successor contains the same 2,097 membership sets exactly, with no additions/deletions;
8. every MST endpoint is a valid pooled event index and every recorded mixing statistic is finite;
9. successor complete order is persisted and hash-frozen before truth access.

A mismatch before truth is an engineering no-result. It does not authorize any scientific modification.

## 6. Development evaluation

Use the exact recurrent-EOM GMN truth convention:

- eligible known shower = at least 4 labelled events in the evaluated year;
- qualified match = dominant shower precision >= 0.5 and overlap >= 4;
- evaluate 2022 and 2023 separately by restricting each pooled candidate's exact members to the relevant year while preserving pooled rank;
- report recovered known showers @25/@50/@100/@500, top-100 dominant precision, MRR, median top-500 fragmentation, and full-catalogue qualified matches.

## 7. Binding promotion gate versus recurrent-EOM

The first technically valid GMN outcome is binding.

MST year-mixing v1 passes only if all conditions hold:

1. recurrent selected nodes and candidate membership sets are exactly unchanged;
2. the complete successor order differs from the recurrent parent order, proving the mechanism is active;
3. recovered@100 is strictly higher in at least one year and not lower in the other;
4. recovered@50 is not lower in either year;
5. top-100 dominant precision is not lower in either year;
6. MRR is not lower in either year;
7. median top-500 fragmentation is not higher in either year.

Recovered@25, recovered@500, and full-catalogue qualified matches are reporting-only, matching the established recurrent-EOM promotion convention.

PASS token:

`PASS_RECURRENT_EOM_MST_YEAR_MIXING_V1_GMN_DEVELOPMENT`

FAIL token:

`FAIL_RECURRENT_EOM_MST_YEAR_MIXING_V1_GMN_DEVELOPMENT`

A failure permanently closes this exact raw MST year-mixing product ranker. No cap, exponent, additive blend, rank fusion, p-value, edge weighting, threshold, alternate graph, or parameter rescue may be selected from the failure.

A PASS authorizes a separately frozen direct exposed SonotaCo benchmark against recurrent-EOM, v31, and the already-frozen matched literature comparators. It does not authorize target-region access.

## 8. Potential novelty claim if supported

If the frozen test succeeds, the methodological contribution is **density-hierarchy recurrence with graph-local temporal mixing**: HDBSCAN supplies the pooled mutual-reachability hierarchy, recurrent-EOM supplies repeated-observation branch selection, and the new rank criterion tests whether independent observing years are locally interleaved on the same density graph rather than merely co-present in a cluster.

HDBSCAN remains the explicit parent method and must be cited.