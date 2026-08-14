# OrbitTrace stratified-core HDBSCAN v1 — frozen protocol

## Status

Frozen before implementation and before the first technically valid scientific outcome.

This successor is rooted directly at the promoted recurrent-EOM HDBSCAN v1 GMN result commit `e3ad80dd4d685b32917af9e2e6d76cb2b76857d4`. It does not inherit consensus-EOM or EFN branch files.

Scientific firewall remains absolute:

- protected solar longitude `[20 deg,55 deg]` is inaccessible;
- no OrbitTrace target information/events;
- no MAARSY or DMS scientific access;
- no SonotaCo 2013/2014 access during development;
- no EFN access;
- permanent development data are target-excluded GMN 2022+2023 only;
- candidate memberships/ranks are frozen before shower truth evaluation;
- first technically valid outcome is binding;
- no post-result neighbor-count, year weight, distance combiner, hierarchy, HDBSCAN parameter, feature, or ranking rescue is authorized.

## 1. Scientific parent

Parent = exact recurrent-EOM HDBSCAN v1.

Pinned parent sources:

- recurrent-EOM implementation Git blob `30ac3fa3bc47910370df528fcf3ae8ecb6277b47`;
- promoted recurrent-EOM runner Git blob `fdc4f3f6e037014aadfcc3ce41b7344aa0a80b2c`;
- binding GMN result record Git blob `3d689ad900da9dd30eb9dc32c389cb508897bc05`.

Binding parent run `31827903547`, artifact `9229646556`, digest `sha256:a0b1ba017696b32cf2e19b3542430adac7bfd13fa2fb78494b6d42742aa35f6d`.

Parent configuration remains:

- GEO6 = `(cos(sol), sin(sol), sin(sun_lon)*cos(ecl_lat), cos(sun_lon)*cos(ecl_lat), sin(ecl_lat), vg/72)`;
- `min_cluster_size=10`;
- `min_samples=10`;
- Euclidean metric;
- HDBSCAN EOM;
- `cluster_selection_epsilon=0`;
- `allow_single_cluster=False`;
- `prediction_data=False`;
- pooled target-excluded GMN 2022+2023;
- annual EOM normalized by accessible year count;
- recurrent stability = minimum of annual normalized EOM values;
- recurrent-EOM ranking = recurrent stability descending, ordinary stability descending, member count descending, deterministic family ID ascending.

## 2. Motivation

In ordinary HDBSCAN, a point's core distance is determined from pooled nearest neighbors. For repeated-observation meteor discovery, a dense neighborhood can therefore be supported disproportionately by one observing year even when the desired physical structure should recur across years.

Stratified-core HDBSCAN moves recurrence into the density hierarchy itself. It requires the local density radius around every event to contain an equal share of nearest-neighbor support from each development year before mutual-reachability clustering is constructed.

This is deliberately deeper than recurrent-EOM: recurrent-EOM changes flat-cluster selection on a standard pooled HDBSCAN hierarchy, while stratified-core changes the mutual-reachability hierarchy and then reuses recurrent-EOM unchanged on that new hierarchy.

## 3. Sole new scientific mechanism: balanced two-year core distance

Keep parent `min_samples=10`.

Because there are exactly two development years and 10 is even, freeze

`k_year = min_samples / 2 = 5`.

For every pooled event `x`, under the exact parent GEO6 Euclidean distance:

- `d_2022(x)` = distance to the 5th nearest **other event** from GMN 2022;
- `d_2023(x)` = distance to the 5th nearest **other event** from GMN 2023.

If `x` itself belongs to the queried year, only that exact event identity is excluded from its same-year neighbor list. Distinct events with identical GEO6 coordinates remain valid neighbors.

Define the stratified recurrent core distance

`core_strat(x) = max(d_2022(x), d_2023(x))`.

Thus the closed ball of radius `core_strat(x)` contains at least five other 2022 events and at least five other 2023 events, preserving the parent's total 10-neighbor support budget while requiring balanced annual representation.

No year-count weighting, exposure weighting, alternate `k`, tolerance, percentile, mean, geometric mean, harmonic mean, or learned core radius is permitted.

## 4. Mutual reachability and hierarchy

For events `a,b`, define

`MR_strat(a,b) = max(core_strat(a), core_strat(b), ||GEO6(a)-GEO6(b)||_2)`.

Use the same HDBSCAN 0.8.43 Euclidean KD-tree dual-tree Boruvka minimum-spanning-tree machinery as the parent hierarchy, with:

- alpha `1.0`;
- parent default `leaf_size=40`;
- Boruvka internal leaf size `40//3`;
- `approx_min_span_tree=True`, matching parent default behavior;
- no additional distance scaling.

Pinned upstream implementation lineage:

- `scikit-learn-contrib/hdbscan` release tag `release-0.8.43` points to commit `b792840bcdfe46bbc29bdc21424a7e01f41d6416`;
- upstream `_hdbscan_boruvka.pyx` Git blob `bceae9e5a62907aaa15776d1b15e16323100f0e4`.

Sort MST edges by weight exactly as HDBSCAN does, convert to its standard single-linkage tree with `hdbscan._hdbscan_linkage.label`, and condense with the unchanged `min_cluster_size=10`.

## 5. Engineering injection path — not a scientific degree of freedom

The installed HDBSCAN Boruvka class computes standard pooled core distances during construction. The implementation may inject a frozen externally computed core-distance vector only through the following equivalence-audited path:

1. construct the same Euclidean `KDTree(X, leaf_size=40)`;
2. construct `KDTreeBoruvkaAlgorithm` with `min_samples=0`, alpha `1.0`, internal leaf size `40//3`, and `approx_min_span_tree=True`; with zero min-samples its initialization adds no scientific nearest-neighbor edge;
3. overwrite the already-allocated public `core_distance_arr` **in place** with the desired Euclidean core distances converted to HDBSCAN's internal Euclidean reduced-distance representation (`distance**2`);
4. call the unchanged compiled `spanning_tree()` implementation;
5. sort returned edges and construct the linkage/condensed tree using unchanged HDBSCAN functions.

Before any binding scientific truth outcome, this injection path must pass a zero-truth equivalence audit:

- on multiple synthetic datasets, injecting ordinary pooled HDBSCAN core distances must reproduce the standard HDBSCAN canonical partition exactly;
- on the full target-excluded GMN 2022+2023 geometry, before shower truth evaluation, injecting ordinary pooled core distances must reproduce the standard parent HDBSCAN canonical partition exactly;
- the recurrent-EOM candidate partition obtained from that injected-standard hierarchy must reproduce the exact recurrent parent candidate partition in the same run before truth evaluation.

If equivalence fails, the run is an engineering no-result. Only injection plumbing may be repaired; the balanced two-year core-distance definition above cannot change.

## 6. Successor cluster extraction

The stratified-core successor changes the density hierarchy only.

On its stratified condensed tree:

1. compute ordinary HDBSCAN stability unchanged;
2. compute annual normalized EOM contributions using the exact recurrent-EOM v1 `recurrent_stability` function and aligned 2022/2023 year vector;
3. recurrent scalar stability remains `min(E_2022,E_2023)`;
4. select nodes with the exact recurrent-EOM v1 `eom_labels` / `selected_eom_nodes` path;
5. assign candidate memberships exactly as recurrent-EOM v1 does.

No consensus-EOM, leaf selection, post-filter, merge/split rule, or alternate flat extraction is permitted.

## 7. Ranking

Selection hierarchy changes; ranking does not.

Stratified-core candidate ID prefix: `SCORE1`.

Rank every successor candidate by the exact recurrent-EOM parent ranking:

1. recurrent scalar stability descending;
2. ordinary stability descending;
3. member count descending;
4. deterministic family ID ascending.

Parent recurrent-EOM candidates retain exact `REOM1` membership and ranking construction on the standard hierarchy.

## 8. Binding development evaluation

Use exactly the recurrent-EOM target-excluded GMN evaluator:

- 2022 accessible events: 315,024;
- 2023 accessible events: 423,658;
- pooled: 738,682;
- eligible shower label support >=4 in evaluated year;
- qualified match = dominant-shower precision >=0.5 and overlap >=4;
- pooled rank is fixed, annual evaluation restricts members only;
- report recovered @25/@50/@100/@500, qualified matches, top-100 dominant precision, MRR, and median top-500 fragmentation.

Persist before truth evaluation:

- standard parent selected nodes/candidates/ranks;
- injection-equivalent standard hierarchy selected nodes/candidates/ranks;
- stratified-core hierarchy identity;
- stratified core-distance vector SHA-256 and summary counts only;
- stratified selected nodes/candidates/ranks;
- canonical membership-partition hashes;
- mechanism-active flag.

## 9. Frozen gate versus recurrent-EOM parent

PASS only if all hold:

1. recovered@100 strictly higher in at least one year and not lower in the other;
2. recovered@50 not lower in either year;
3. top-100 dominant precision not lower in either year;
4. MRR not lower in either year;
5. median top-500 fragmentation not higher in either year;
6. successor candidate membership partition differs from recurrent-EOM parent, proving the hierarchy change is scientifically active;
7. full-GMN injected-standard-core recurrent parent exactly reproduces the standard recurrent parent partition before truth evaluation.

@25, @500, and full qualified-match count are reporting metrics only.

PASS token:

`PASS_STRATIFIED_CORE_HDBSCAN_V1_GMN_DEVELOPMENT`

FAIL token:

`FAIL_STRATIFIED_CORE_HDBSCAN_V1_GMN_DEVELOPMENT`

A failed binding outcome permanently closes stratified-core v1. No 4/6 split, 6/4 split, `k_year` variant, sample-count weighting, core-distance mean, soft balance, alternate MST approximation, HDBSCAN parameter change, or ranking rescue is authorized.

A PASS authorizes only a separately frozen exposed SonotaCo comparison. EFN is not pristine validation for this successor because its unlabeled geometry/hierarchy behavior was observed before this successor was designed.

## 10. Novelty statement if supported

If successful, the method is explicitly HDBSCAN-derived: its contribution is a **stratified recurrent core distance** that alters HDBSCAN's mutual-reachability density hierarchy so local density must be supported across repeated observing periods, followed by the already-promoted recurrent-EOM selection rule.

HDBSCAN remains cited as the parent algorithm; originality lies in the repeated-observation core-distance construction and its integration into the hierarchy, not in claiming independence from HDBSCAN.
