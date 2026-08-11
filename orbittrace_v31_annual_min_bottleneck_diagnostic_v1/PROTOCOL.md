# OrbitTrace v31 annual-min bottleneck diagnostic v1

## Scientific role

Post-v56 exposed-development **mechanism diagnostic only**. This diagnostic does not create or evaluate a successor order.

Binding v56 showed that equal-total weighting of the four frozen 71D feature blocks materially worsens HDB, so block-weight geometry is closed. Earlier v51/v52/#1157/v54/v55 work also closes further algebra over the final local/v19 constituent ranks. One distinct unresolved quantity remains inside exact v31 before diversity/fusion: the fixed annual local-geometry combiner

`combined_margin = min(margin_2013, margin_2014)`.

The literature panels are annual, while v31 deliberately uses one conservative two-year quality coordinate. This diagnostic asks one narrow question: **among already-fixed annual-recoverable HDB groups, are groups missed by v31 held back more strongly by the other year's margin than groups surfaced by v31?**

A PASS is mechanism evidence only. It does not authorize `max`, mean, geometric mean, weighted mean, annual-specific ranking, a threshold, or any successor automatically.

SonotaCo 2013/2014 remains `EXPOSED_DEVELOPMENT_ONLY`.

## Immutable parent

Use exact v31 source blob `917e3cd6f9310ca1282e0efa58ed0924d03ed4da` and the immutable #950 71D payload / memberships / v19 order / centroids.

Exact v31 controls must reproduce first:

- Sugar 2013 `0.2719801488280529 / 16`;
- Sugar 2014 `0.31529041952487225 / 17`;
- HDB 2013 `0.14888037368183737 / 9`;
- HDB 2014 `0.15198123772301594 / 9`.

The diagnostic recomputes exact v31's stacked-route strict whole-shower 5-fold OOF geometry:

- 71 immutable features;
- fold-training mean/population-std z-score, zero std -> 1;
- annual positive iff exact annual fixed-label `F1 > 0.5`;
- ordinary Euclidean k=1 nearest positive and nearest nonpositive;
- `margin_y = d_nonpositive - d_positive`;
- exact parent `combined_margin = min(margin_2013, margin_2014)`;
- exact #839 diversity `lambda=0.8`, `scale=1.0`;
- one equal rank-sum with immutable v19.

The recomputed HDB annual-margin array hashes, combined-margin hash, local-diversity order hash, and final fused order hash must exactly equal the parent v31 result. Any mismatch is an engineering/provenance failure, not a diagnostic result.

## Freeze before status attachment

Before the #1046 surfaced/missed diagnostic is loaded, freeze the complete 229-family HDB vector containing only:

- family ID;
- exact v31 rank;
- `margin_2013`;
- `margin_2014`;
- `combined_margin = min(margin_2013, margin_2014)`;
- `bottleneck_gap_2013 = margin_2013 - combined_margin`;
- `bottleneck_gap_2014 = margin_2014 - combined_margin`.

Each gap is nonnegative by construction. A positive `bottleneck_gap_y` means the candidate's own-year geometry is better than the coordinate actually used by v31 because the other year is the bottleneck.

No #1046 group label, surfaced/missed flag, candidate-recoverable flag, annual F1, literature budget, or outcome identity may enter this frozen vector.

## Outcome/status source

Only after the full 229-family margin vector is frozen, restore authoritative #1046:

- run `31451236076`;
- artifact `9086399760`;
- artifact digest `sha256:a2c373df77ef7e0065c1d8aceb1f6e5826f1e30b6286f2331c362d959f1d7f69`;
- `diag/V31_HDB_MISSED_LABEL_RANKGAP_DIAGNOSTIC.json` SHA-256 `e4e09546e17b9a5da7ce12ad9af4bb7129533fd9b5be846ebc859719f01a9758`;
- verdict `PASS_V31_HDB_MISSED_LABEL_RANKGAP_DIAGNOSTIC`;
- role `POST_RESULT_DIAGNOSTIC_ONLY_NO_SUCCESSOR_SELECTED`.

#1046 already fixes, for every eligible annual HDB shower group, whether a fixed candidate is recoverable, whether v31 surfaces a recoverable candidate, and the first recoverable family under the exact v31 fused order. This diagnostic reuses those frozen representatives/statuses only; it does not inspect or redefine shower identity.

Expected annual recoverable-group populations are fixed by #1046:

- 2013: 18 candidate-recoverable groups = 9 surfaced + 9 recoverable-but-missed;
- 2014: 19 candidate-recoverable groups = 9 surfaced + 10 recoverable-but-missed.

Any mismatch fails closed.

## Sole statistic

For each annual candidate-recoverable #1046 group, use exactly its already-frozen

`first_recoverable_family_id_by_v31_fused_rank`.

For year `y`, attach that family's frozen

`G_y = margin_y - min(margin_2013, margin_2014)`.

No alternate representative is evaluated.

For each year separately, compare:

- median `G_y` among `recoverable_but_missed=true` groups;
- median `G_y` among `v31_surfaced_recoverable=true` groups.

## Binding diagnostic gate

PASS requires **both** conditions in **both 2013 and 2014**:

1. missed-recoverable median `G_y` is strictly positive; and
2. missed-recoverable median `G_y` is strictly greater than surfaced-recoverable median `G_y`.

Thus all four strict inequalities must hold. Empty classes fail closed.

This is a direction-only mechanism test. There is no p-value, AUC, correlation, effect-size threshold, nonzero-gap cutoff, quantile, top-k, rank window, literature-budget action, or multiple-statistic selection.

## Interpretation boundary

If PASS: conclude only that exact v31's conservative annual `min` disproportionately bottlenecks the already-recoverable HDB groups it misses in both exposed years. Any successor must still be separately motivated and freeze one complete route-general total order before its first panel outcome.

If FAIL: the exact annual-min-bottleneck mechanism is closed. Do not rescue it by changing the representative, conditioning on gap magnitude, selecting a subset/year, or trying multiple annual-combiner diagnostics after the result.

## Explicit non-search commitments

No:

- new candidate order or score used for ranking;
- alternate annual combiner (`max`, mean, median, geometric/harmonic mean, soft-min, weighted mean, rank consensus);
- annual-specific catalogue;
- threshold, quantile, top-k, rank window, budget/year rule;
- alternate recoverable-group representative;
- feature, metric, k, scaling, diversity, fusion, model, component, topology, cross-route, source-quota search;
- oracle/literature identity used for ranking;
- successor selection;
- post-result second diagnostic in this annual-combiner family.

## Firewall

- SonotaCo 2013/2014 is `EXPOSED_DEVELOPMENT_ONLY`.
- Protected OrbitTrace solar longitude `20°–55°` remains inaccessible.
- No OrbitTrace target information or target-region events may be accessed.
- No MAARSY or DMS scientific access is authorized.
