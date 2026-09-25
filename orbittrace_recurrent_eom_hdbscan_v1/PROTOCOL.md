# OrbitTrace recurrent-EOM HDBSCAN v1 — frozen protocol

## Status

Frozen before the first scientific outcome. This branch intentionally changes the methodological lineage: HDBSCAN is now the explicit parent framework rather than only a literature comparator. The contribution tested here is a meteor-specific modification of HDBSCAN cluster extraction, not parameter tuning and not a post-hoc reranker.

Scientific firewall remains binding:
- protected solar longitude 20°–55° is removed before labels, clustering, scoring, or diagnostics;
- no OrbitTrace target information or target-region events;
- no MAARSY or DMS scientific access;
- no SonotaCo 2013/2014 access during development;
- GMN 2022 target-excluded is development only;
- GMN 2023 remains held out until a separately frozen evaluator is authorized by a GMN-2022 PASS.

## 1. Parent algorithm

The parent is HDBSCAN* with the standard excess-of-mass (EOM) flat-cluster extraction described by Campello et al. The parent hierarchy is built once and is shared exactly by the parent and successor.

Input representation is the six-component geocentric `GEO` vector used in meteor HDBSCAN work and derived from Sugar et al.:

`[cos(sol), sin(sol), sin(sun_lon)*cos(ecl_lat), cos(sun_lon)*cos(ecl_lat), sin(ecl_lat), vg/72]`

with angles in radians and no z-score normalization.

Frozen HDBSCAN settings:
- `min_cluster_size = 10`;
- `min_samples = 10`;
- cluster selection method `eom`;
- `cluster_selection_epsilon = 0`;
- `allow_single_cluster = false`;
- Euclidean metric on the exact GEO vector;
- no alpha, metric, feature, minimum-size, minimum-samples, selection-method, epsilon, or normalization search.

The value 10 is inherited from the already-frozen RFT minimum final candidate support and is fixed here before any HDBSCAN-derived outcome; it is not selected from HDBSCAN performance.

## 2. Sole new mechanism: recurrent excess of mass

Ordinary HDBSCAN EOM assigns each condensed-tree cluster C a stability equal to the total density persistence contributed by its members and recursively retains a parent or its descendants according to which has greater total stability.

Meteor streams are different from generic density clusters because a physical shower should recur in independent observing years. Standard EOM can therefore prefer a branch whose persistence is dominated by one observing year.

For each condensed-tree cluster C and each year y in {2022, 2023 when authorized}, define annual excess of mass using the exact HDBSCAN condensed-tree birth/departure lambdas but counting only descendants from year y:

`E_y(C) = sum_rows[(lambda_row - lambda_birth(C)) * n_y(row)] / N_y`

where `n_y(row)` is the number of year-y point descendants represented by that departing condensed-tree child row and `N_y` is the total accessible event count for that year. The global division removes catalogue-size imbalance and introduces no fitted parameter.

Define the sole successor stability:

`E_rec(C) = min(E_2022(C), E_2023(C))`.

The ordinary HDBSCAN EOM dynamic-programming extraction is then run unchanged except that `E_rec` replaces ordinary total stability. Thus the successor may choose a different set of branches from the *same condensed hierarchy* because a cluster must have persistent density support in both years to obtain high extraction stability.

No weighted mean, harmonic mean, geometric mean, product, balance coefficient, year threshold, persistence threshold, post-filter, candidate rerank, or alternate annual normalization is authorized.

## 3. Why this is algorithmically distinct

This is not HDBSCAN followed by a recurrence score. Recurrence changes the objective used inside the parent-versus-children EOM tree optimization and therefore changes which hierarchy branches become output clusters. The density hierarchy, mutual-reachability construction, condensation, and all HDBSCAN numerical parameters remain inherited; the cluster-selection objective is the one new mechanism.

The intended novelty claim, if supported, is **recurrent-EOM hierarchical density clustering for repeated-observation physical streams**. HDBSCAN must be cited as the parent method.

## 4. GMN 2022/2023 development design

The first experiment is a mechanism-development comparison on target-excluded GMN using year identity only as an unsupervised recurrence variable. Shower labels are hidden until both parent and successor cluster memberships and deterministic ranking keys have been frozen for the run.

Because recurrent EOM requires two independent years, the scientific development pool is the already-authorized target-excluded GMN 2022+2023 pool. No SonotaCo information may enter architecture selection.

Both methods use exactly the same pooled events, GEO vectors, HDBSCAN hierarchy, condensed tree, and cluster-size parameters. Parent output uses ordinary EOM. Successor output uses recurrent EOM.

Clusters are converted to candidate families by exact member IDs. Candidate ranking is fixed before labels:
- successor: descending recurrent stability `E_rec`, then descending ordinary HDBSCAN stability, then descending member count, then deterministic member-hash ID;
- parent: descending ordinary HDBSCAN stability, then descending member count, then deterministic member-hash ID.

No probability score, outlier score, membership-strength trimming, soft assignment, diversity rerank, v31 fusion, or learned ranker is used.

## 5. Evaluation

Use the already-frozen OrbitTrace GMN family evaluation convention:
- eligible known shower: at least 4 labelled events in the evaluated year;
- a candidate is a qualified match when dominant shower precision >= 0.5 and overlap >= 4;
- report full-catalogue qualified known showers, recovered known showers at ranks 25/50/100/500, top-100 dominant precision, MRR, and median top-500 fragmentation.

Evaluate 2022 and 2023 separately from the same pooled clustering by restricting candidate member IDs to each year for annual truth matching; candidate order itself remains the pooled prelabel order.

## 6. Binding development gate

The first technically valid result is binding. Recurrent-EOM HDBSCAN passes only if, relative to the exact ordinary-EOM parent, it satisfies **all** of:

1. recovered@100 is strictly higher in at least one year and not lower in the other;
2. recovered@50 is not lower in either year;
3. top-100 dominant precision is not lower in either year;
4. MRR is not lower in either year;
5. median top-500 fragmentation is not higher in either year;
6. the successor emits at least one cluster whose selected hierarchy node differs from the parent, proving the mechanism is active rather than numerically inert.

If any gate fails, recurrent-EOM v1 is rejected. No alternate annual combiner, normalization, minimum cluster size, min_samples, feature vector, HDBSCAN selection mode, ranking key, or threshold rescue is permitted from that outcome.

A PASS does not authorize SonotaCo. It authorizes only a separately frozen next-stage comparator/held-out protocol.

## 7. Provenance boundary

The implementation must pin the exact `hdbscan` package version and verify that custom recurrent stability is supplied to the same EOM tree-selection routine used by the parent implementation. A zero-truth engineering audit must show that supplying ordinary HDBSCAN stability through the custom pathway reproduces parent selected labels exactly before recurrent stability is evaluated scientifically.
