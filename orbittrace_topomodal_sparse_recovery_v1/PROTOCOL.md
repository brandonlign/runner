# OrbitTrace topomodal sparse-recovery v1

## Status

**FROZEN BEFORE IMPLEMENTATION AND BEFORE ANY SHOWER-TRUTH OUTCOME FOR THIS SUCCESSOR.**

This is the one target-excluded GMN recovery/ranking successor authorized by the positive `orbittrace_topomodal_hierarchy_scale_v1` structural result (run `31955621864`, result SHA-256 `e8cf7d92e96db9a1c99578f6efc63baf1534b94ab975e94f789fa6bc4a718497`).

Its purpose is direct and limited: determine whether the already-frozen fixed-scale ToMATo hierarchy actually recovers known streams better than recurrent-EOM when the survey is thinned into the exact sparse regimes where recurrent-EOM's fixed 10/10 support becomes sample-size limited.

This is **not** another zero-label diagnostic. Shower truth is opened only after every candidate membership and rank for all eight subsets has been persisted to an immutable prelabel file.

The failed window-owned-persistence successor is not modified or rescued here. Its truth outcome does not select any radius, coordinate scale, hierarchy rule, score parameter, subset, or gate in this protocol.

## 1. Firewall

Use only target-excluded GMN 2022+2023 development data. Inclusive solar longitude `[20.0,55.0]` is removed before any geometry, candidate construction, ranking, or truth evaluation.

Forbidden:

- OrbitTrace target information or target-region events;
- SonotaCo scientific access;
- ASFN or EFN event-level access;
- AMOS scientific access;
- MAARSY or DMS scientific access;
- any result-informed radius, density transform, hierarchy subset, persistence rule, ranking feature, tie-break, sample subset, truth metric, or gate change.

SonotaCo is not authorized by this experiment regardless of outcome.

## 2. Exact sample-size stress panels

Reuse the exact already-frozen `ORBITTRACE_SCALE_STRESS_V1` nested subsets from the structural test:

`H(eid) = uint64_be(SHA256('ORBITTRACE_SCALE_STRESS_V1|' + eid)[0:8])`.

Evaluate exactly eight pooled 2022+2023 subsets:

- coarse denominator `128`, buckets `0,1,2,3` (~5.8k pooled events each);
- fine denominator `1024`, buckets `0,1,2,3` (~0.7k pooled events each).

No new bucket, salt, denominator, replicate, bootstrap, or panel is authorized.

## 3. Successor candidate hierarchy — unchanged from #1284

Candidate generation is **bit-for-bit conceptually unchanged** from `orbittrace_topomodal_hierarchy_scale_v1`:

- physical embedding:
  - `h_sol = 2 sin(5°/2)`;
  - `h_rad = 2 sin(4°/2)`;
  - `h_logv = ln(1.1)`;
  - `Z = (cos(sol)/h_sol, sin(sol)/h_sol, cos(lat)cos(lon)/h_rad, cos(lat)sin(lon)/h_rad, sin(lat)/h_rad, ln(v_g)/h_logv)`;
- exact symmetric Euclidean radius graph at `r = 1.0`;
- density `rho_i = |N_i| / n`, including self;
- GUDHI `3.12.0` ToMATo with `graph_type='manual'`, `density_type='manual'`;
- complete leaf + internal merge-node + connected-component-root memberships;
- exact membership deduplication;
- minimum candidate support `4` applied only after hierarchy construction.

For every subset, before shower truth is opened, the generated topomodal candidate summaries must match the authoritative #1284 structural artifact exactly: candidate count and the complete sorted set of `(family_hash, member_count, first_node, is_root)` rows. Any mismatch aborts before truth.

## 4. Frozen intrinsic ranking

The structural diagnostic intentionally had no ranking. This successor adds one ranking derived only from ToMATo's own prominence hierarchy. There is no fitted coefficient, learned model, threshold search, or shower-label feature.

Let:

- `L = n_leaves_`;
- `P = sort(diagram_[:,0] - diagram_[:,1])` ascending;
- `children_[i]` create internal node `L+i` at the `i`th ToMATo prominence merge;
- leaf creation prominence be `0`;
- internal-node creation prominence be `P[i]`.

Require `len(P) == len(children_)`.

Reconstruct each node's unique parent from `children_`.

For every eligible candidate node compute:

- `is_root`: whether it has no parent;
- `peak_density = max(rho_i)` over its members;
- `mean_density = mean(rho_i)` over its members;
- for a non-root node, `prominence_span = creation_prominence(parent) - creation_prominence(node)`;
- for a root, `prominence_span` is not used because the corresponding topological class has no finite merge/death in the observed graph.

Require every finite `prominence_span >= 0` up to numerical tolerance.

Rank candidates lexicographically by:

1. roots before non-roots (the disconnected-component classes are the hierarchy's infinite-persistence classes);
2. among roots: decreasing `peak_density`, then decreasing `mean_density`, then decreasing member count;
3. among non-roots: decreasing `prominence_span`, then decreasing `peak_density`, then decreasing `mean_density`, then decreasing member count;
4. deterministic `family_hash` ascending as the final tie-break.

No cross-year label, shower identity, truth-trained ranker, recurrence fit, diversity model, learned score, or tunable weighting is permitted.

### Ranking implementation invariant

Before truth, verify the interpretation of the ToMATo merge sequence without labels: for every distinct finite prominence interval represented by the fitted hierarchy, the number of clusters implied by the first `m` `children_` merges must equal the number returned by ToMATo's own prominence-threshold cluster-count rule. This is an engineering invariant only; it cannot change the ranking.

## 5. Exact recurrent-EOM comparator

On each identical subset reconstruct selected recurrent-EOM HDBSCAN v1 unchanged:

- GEO6 exactly;
- `min_cluster_size=10`;
- `min_samples=10`;
- Euclidean;
- ordinary HDBSCAN condensed tree;
- exact annual-normalized recurrent-EOM contribution;
- exact FOSC/EOM extraction using recurrent stability.

Rank comparator candidates exactly as the selected parent:

1. decreasing recurrent stability;
2. decreasing ordinary stability;
3. decreasing member count;
4. deterministic family ID.

Its generated unordered memberships must match the authoritative #1284 structural artifact exactly before truth is opened.

## 6. Immutable prelabel boundary

For all eight subsets, persist before truth:

- exact event-universe hash;
- all successor candidate event IDs, hierarchy metadata, intrinsic score fields, and final ranks;
- all comparator candidate event IDs and final ranks;
- exact candidate-summary matches to #1284;
- exact source/artifact hashes and firewall flags.

Write `TOPOMODAL_SPARSE_RECOVERY_V1_PRELABEL.json`, compute SHA-256, print it, and only then evaluate shower labels. Candidate generation/ranking may not be rerun after truth to alter the result.

## 7. Truth metric — exact parent semantics

Use the selected recurrent-EOM parent's existing `metrics(...)` function unchanged, separately for 2022 and 2023 within every pooled subset.

For a given subset:

- let `K` be the number of recurrent-EOM comparator candidates;
- evaluate the comparator's complete ranked list (length `K`);
- evaluate exactly the first `K` topomodal candidates, giving equal candidate-reporting budget;
- also evaluate the complete topomodal list only as a diagnostic coverage measure, never as a promotion gate.

The parent's truth semantics remain unchanged:

- annual shower eligibility requires at least 4 events in that subset-year;
- a candidate/shower match is positive only at precision `>= 0.5` with overlap `>= 4`;
- report qualified matches, recovered@25/@50/@100/@500, top-100 dominant precision, MRR, and median top-500 fragmentation.

Because all sparse lists are shorter than some fixed budgets, the primary recovery quantity is `qualified_matches` at equal candidate budget; the standard recovered@K fields are retained exactly for auditability.

## 8. Frozen aggregate gates

There are 16 year-panels: four buckets x two years at each of two sample scales.

For each scale aggregate across its eight bucket-year panels:

- `qualified_total = sum(qualified_matches)`;
- `mrr_mean = mean(MRR)`;
- `precision_mean = mean(top100_dominant_precision)`;
- `fragmentation_mean = mean(fragmentation_median_top500)`.

Also count panelwise `qualified_matches` wins/ties/losses.

Return

`PASS_TOPOMODAL_SPARSE_RECOVERY_V1`

iff **all** of the following hold:

### Fine sparse scale (`d=1024`)

1. equal-budget topomodal `qualified_total` is **strictly greater** than recurrent-EOM;
2. topomodal has at least as many qualified matches as recurrent-EOM in at least `6/8` fine bucket-year panels;
3. `mrr_mean` is at least recurrent-EOM;
4. `precision_mean` is at least recurrent-EOM;
5. `fragmentation_mean` is no higher than recurrent-EOM.

### Coarse scale (`d=128`)

6. equal-budget topomodal `qualified_total` is at least recurrent-EOM;
7. topomodal has at least as many qualified matches as recurrent-EOM in at least `6/8` coarse bucket-year panels;
8. `mrr_mean` is at least recurrent-EOM;
9. `precision_mean` is at least recurrent-EOM;
10. `fragmentation_mean` is no higher than recurrent-EOM.

Otherwise return

`FAIL_TOPOMODAL_SPARSE_RECOVERY_V1`.

There is no mixed verdict and no post-result rescue.

## 9. Interpretation

A PASS means the #1284 architecture has crossed the missing truth boundary: it not only preserves candidate identity under ~8x thinning, but also improves actual known-stream recovery at equal candidate budget in the sparse regime while not regressing at the coarser regime. Only then is exact full-catalog engineering/scaling worth pursuing, followed by a separately frozen full-GMN comparison.

A FAIL closes this exact fixed-scale topomodal hierarchy + intrinsic prominence-span ranking architecture. Do not change the ranking, root treatment, density score, radius, hierarchy membership, scale, minimum support, truth metric, or gates after outcome.