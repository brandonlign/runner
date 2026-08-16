# OrbitTrace single-link persistence scale diagnostic v1

## Status

**FROZEN BEFORE IMPLEMENTATION AND BEFORE ANY DIAGNOSTIC OUTCOME.**

This is a zero-label structural feasibility diagnostic only. It is not a successor clustering method, does not select a support parameter, and cannot promote raw single linkage for scientific use.

PR #1272 established that fixed HDBSCAN `10/10` becomes recurrent-EOM-inert as accessible sample size falls. PR #1273 isolated a joint finite-support bottleneck: at ~700 events, neither removing only the 10-point condensation floor nor only the 10-neighbor core smoothing restores recurrence; only the joint algorithmic-minimum ablation exposes alternative structure. That ablation is not promotable.

The present diagnostic asks a distinct question: **does a dimensionless persistence coordinate from a support-free Euclidean single-linkage tree remove the dominant sample-size scaling seen in raw neighborhood/merge distances?**

The motivation is cluster-tree theory: a branch exists over a range of linkage scales, and its multiplicative lifetime can be represented by the ratio between the distance at which the branch merges into its parent and the distance at which the branch itself is formed. This ratio is exactly invariant to a global rescaling of all distances. Whether it is empirically less sample-size-sensitive on OrbitTrace geometry is tested here without labels.

A favorable result would justify developing a separately frozen **statistical pruning** layer around such a scale coordinate. It would not justify using unpruned single linkage, choosing a threshold, or opening validation data.

## 1. Scientific parent and firewall

Branch from exact selected recurrent-EOM paper/development head:

`0248177a2b4dc1f7a0969931d835097d3e86c06f`.

Use target-excluded GMN 2022+2023 geometry only under the exact parent GEO6 representation. Remove the inclusive protected solar-longitude interval `[20.0,55.0]` before geometry enters this diagnostic.

Forbidden:

- OrbitTrace target information or target-region events;
- shower labels/truth in any statistic or decision;
- SonotaCo scientific access;
- ASFN or EFN event-level access;
- AMOS scientific access;
- MAARSY or DMS scientific access;
- any clustering-method promotion, threshold selection, branch significance claim, or parameter tuning from this outcome.

## 2. Exact deterministic subsets

Reuse the immutable PR #1272 hash rule exactly:

`H(eid) = uint64_be(SHA256('ORBITTRACE_SCALE_STRESS_V1|' + eid)[0:8])`.

Event `eid` is retained for denominator `d`, bucket `b` iff:

`H(eid) mod d == b`.

Use exactly:

- denominator `128`, buckets `0,1,2,3` (~5.8k events each);
- denominator `1024`, buckets `0,1,2,3` (~0.7k events each).

These are the exact already-frozen small-scale anchors from #1272/#1273. No new salt, denominator, bucket, random seed, or subset is allowed.

## 3. Support-free tree construction

For each of the eight subsets:

1. compute exact parent GEO6 coordinates;
2. construct ordinary **Euclidean single-linkage hierarchical clustering** with no k-neighbor density smoothing and no minimum cluster-size condensation;
3. use `sklearn.cluster.AgglomerativeClustering` with:
   - `linkage='single'`;
   - `metric='euclidean'`;
   - `n_clusters=None`;
   - `distance_threshold=0`;
   - `compute_distances=True`.

This tree is used only to measure branch scale coordinates. It is not a candidate scientific detector.

For merge row `i`, node `n+i` is born/formed at exact linkage distance `d_form`. For every non-root internal node, let `d_parent` be the linkage distance at which that node is merged into its parent.

For every internal branch with finite `d_parent > 0`, `d_form > 0`, and at least 4 leaves, define:

`log_persistence = log(d_parent / d_form)`.

Also retain:

`log_formation_scale = log(d_form)`.

The lower branch-size bound `4` is fixed because this diagnostic is about the already-established weak 4+ meteor regime used throughout OrbitTrace's pre-target calibration lineage; it is not a new cluster threshold and cannot become one from this diagnostic.

## 4. Frozen dyadic branch-size strata

Analyze exactly these four branch-size bins:

- `4_7`: 4–7 leaves;
- `8_15`: 8–15 leaves;
- `16_31`: 16–31 leaves;
- `32_63`: 32–63 leaves.

Dyadic bins are frozen before outcome to separate branch-size effects without choosing a preferred cluster size.

For each denominator, pool the branch statistics from its four deterministic buckets within each size bin. Also preserve per-bucket summaries.

A size bin is `SUPPORTED` only if it contains at least 30 valid branches at **each** denominator. Otherwise it is reported but excluded from the categorical interpretation. No bin may be merged or replaced after outcome.

## 5. Threshold-free relative scale-invariance comparison

For each supported size bin compare denominator 128 versus denominator 1024.

Compute for `log_persistence`:

- two-sample Kolmogorov-Smirnov distance `KS_persistence`;
- absolute pooled-median shift `MED_persistence`;
- absolute pooled-90th-percentile shift `P90_persistence`.

Compute the same quantities for the raw log formation scale:

- `KS_formation`;
- `MED_formation`;
- `P90_formation`.

A supported bin is a strict **scale-normalization win** iff all three inequalities hold:

- `KS_persistence < KS_formation`;
- `MED_persistence < MED_formation`;
- `P90_persistence < P90_formation`.

This comparison is deliberately relative and threshold-free: the raw formation distance is the negative-control scale coordinate known to change as point density changes, while the persistence ratio is the proposed dimensionless coordinate. No numerical tolerance is selected from results.

## 6. Predeclared categorical interpretation

Let `S` be the number of supported bins and `W` the number of supported bins with strict scale-normalization wins.

- `SUPPORTS_SINGLELINK_PERSISTENCE_SCALE_NORMALIZATION` iff `S >= 3` and `W == S`;
- `REFUTES_SINGLELINK_PERSISTENCE_SCALE_NORMALIZATION` iff `S >= 3` and `W <= 1`;
- otherwise `MIXED_SINGLELINK_PERSISTENCE_SCALE_EVIDENCE`.

This is a feasibility interpretation only. A support result does **not** establish clustering power, calibration, recurrence benefit, false-positive control, or paper-method superiority.

## 7. Descriptive outputs

For every denominator/bucket/bin preserve:

- branch count;
- log-persistence median, p90, p99;
- formation-distance median, p90, p99;
- annual event counts of the source subset;
- total internal-node count.

For every pooled supported bin preserve the six frozen cross-scale comparison metrics above.

No shower recovery, precision, F1, MRR, v31 metric, literature comparator, target statistic, or candidate ranking is permitted.

## 8. Relationship to closed work

This does not rescue:

- #1271 `8/4 + local-BIC` HDBSCAN;
- #1273's diagnostic `2/2` ablation;
- old thinning/subsample family-stability ranking;
- old multiscale subset scan #35;
- trajectory/background methods such as #1221.

It introduces no HDBSCAN support count and no adaptive subset score. It asks only whether a mathematically dimensionless branch-lifetime coordinate is less sample-size-sensitive than raw linkage distance.

## 9. Closure

After the first technically valid complete run:

- preserve all exact outputs and the categorical interpretation;
- do not alter size bins, subsets, branch-size floor, or comparison rule;
- do not choose a persistence threshold from the output;
- do not evaluate real-shower truth on this tree;
- any future statistical-pruning successor requires a separate pre-outcome protocol.
