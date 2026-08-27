# Recurrent-EOM versus catalogue-HDBSCAN fairness recalibration v1

## Why this correction is required

This is an **exposed corrective fairness adjudication**, not pristine validation. The earlier equal-temporal SonotaCo comparison used the published paper's highlighted GEO/eom configuration with `min_cluster_size = 100`. Peña-Asensio & Ferrari (2025), however, explicitly vary the HDBSCAN minimum cluster size from 10 to 1000 and state that the parameter requires careful selection; their CAMS maximum-agreement configuration happens to use 100. Transferring 100 unchanged to another survey can therefore handicap ordinary HDBSCAN in the same way that transferring Sugar's 23% shower-fraction parameter handicapped Sugar.

No OrbitTrace target information is used here.

## Immutable recurrent-EOM side

Use the exact frozen recurrent-EOM pooled SonotaCo pretruth catalogue from run `31829200215`, artifact `orbittrace-recurrent-eom-sonotaco-v31-benchmark-v1`. No recurrent-EOM membership, feature, hierarchy, recurrence rule, rank, or parameter may change.

## Ordinary HDBSCAN side

Use the same pooled 2013+2014 label-free HDBSCAN-route rows as recurrent-EOM and the same published GEO feature representation already audited in the project:

`[cos(sol), sin(sol), sin(lon)cos(lat), cos(lon)cos(lat), sin(lat), Vg/72]`.

Use the exact package/configuration family:

- `hdbscan == 0.8.44`;
- Euclidean metric;
- `cluster_selection_method = eom`;
- `min_samples = None` so it follows `min_cluster_size`, matching the frozen published-configuration adapter;
- `allow_single_cluster = False`;
- every non-noise HDBSCAN label is a reported catalogue family.

## Cross-year minimum-cluster-size calibration

All candidate catalogues for the complete grid are generated from pooled label-free rows **before truth-based selection**.

Grid:

`10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 120, 150, 200, 300, 500, 750, 1000`.

This spans the published 10–1000 range, includes the paper's highlighted 30–50 and 100 regions, and is deliberately favorable to ordinary HDBSCAN.

For evaluation on 2013, choose the minimum cluster size using **2014 truth only**. For evaluation on 2014, choose it using **2013 truth only**. Selection maximizes calibration-year Hungarian macro F1, then recovered showers at assigned F1 > 0.5, then chooses the smaller minimum cluster size as a deterministic tie break.

This gives ordinary HDBSCAN supervised cross-year calibration while recurrent-EOM remains label-free and frozen. It is therefore conservative with respect to any recurrent-EOM superiority claim.

## Evaluation

Ordinary HDBSCAN produces a flat catalogue rather than a native ranked top-K list. Do not invent a ranking for it.

For each held-out year:

1. take the cross-year-selected HDBSCAN catalogue;
2. count HDBSCAN families containing at least one event in the held-out truth universe; call this `B`;
3. score the complete HDBSCAN catalogue using one-to-one Hungarian F1;
4. score recurrent-EOM using its frozen top `B` active candidates;
5. report macro F1, recovered showers with assigned F1 > 0.5, and candidate count.

The year verdict is:

- `RECURRENT_EOM_WIN` only if recurrent-EOM has strictly greater macro F1 and no recovered-shower loss;
- `HDBSCAN_WIN` only if ordinary HDBSCAN has strictly greater macro F1 and no recovered-shower loss;
- otherwise `MIXED`.

The overall result requires the same winner in both years; otherwise it is `NO_UNAMBIGUOUS_WINNER`.

## Claim firewall

Allowed if supported:

> Under an exposed cross-year-calibrated SonotaCo audit, recurrent-EOM [outperformed / did not outperform] ordinary GEO/eom HDBSCAN when ordinary HDBSCAN was allowed to select its minimum cluster size on the other year.

Not allowed:

- treating the old fixed-100 result as sufficient proof of recurrent-EOM superiority;
- calling this pristine external validation;
- claiming universal superiority over HDBSCAN;
- changing recurrent-EOM after seeing the calibrated result;
- using the result to retune OrbitTrace target recovery.
