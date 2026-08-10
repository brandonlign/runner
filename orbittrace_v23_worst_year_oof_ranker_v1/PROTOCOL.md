# OrbitTrace v23 — worst-year strict-group OOF ranking

## Motivation

v22 produced the first valid strict whole-shower grouped SonotaCo OOF ranking result and still lost both catalogue-HDBSCAN panels. The exposed diagnosis is specific: the v19/v22 family universe already contains enough strong candidates, and the very top HDBSCAN-route ranks are mostly different showers rather than simple duplicates, but several high-ranked representatives are highly imbalanced across 2013 and 2014. The v22 regression target was combined two-year membership F1, which can reward a family that is excellent in one year and weak in the other even though the benchmark must succeed in both years.

v23 therefore changes exactly one scientific quantity: the regression target.

## Frozen inputs and architecture

v23 must regenerate the exact v22 pretruth payloads before truth and byte-match the authoritative valid v22 run 31418293036.

Sugar route file SHA-256:
- `features.npy`: `3b5ad5b7f900b03ba45b0aadf2f1a71dab054ae56e4d7aca7a880a9216486286`
- `centroids.npy`: `afe777b62b32dc2c18b6036939b64f1f1390b0383507c157b4682c386a2c94f5`
- `family_memberships.json`: `be5f559f27c1a18dcda28c20b6197278473cdb458ddfd29ec61bc468e33c352a`
- `V22_PRETRUTH_FEATURE_MANIFEST.json`: `bea982e3b44053a785c45a5e8875dcfb64941cc6cc56ff2102905105830e9359`

HDBSCAN route file SHA-256:
- `features.npy`: `ee56b824dc59d5af1a03ccf37d77886a7adaeac18f378137de6647c000101fa6`
- `centroids.npy`: `619d13b46fb286e46135fb1984264ed2323efa36da2be516c0832962825f4452`
- `family_memberships.json`: `99640747e935df2f4a7c7983bdde843ea59e1814388b8418e040dc04628aee13`
- `V22_PRETRUTH_FEATURE_MANIFEST.json`: `2a81721343dc795e925b1ffea39e50c963a696fcca47ab7784abe6f5f10e9980`

Everything else is inherited unchanged from v22:
- exact 71-dimensional pretruth label-free feature vector;
- exact fixed v19-expanded memberships;
- exact Sugar/HDBSCAN matched row routes;
- one shared model across both routes;
- exact #839 ExtraTrees model complexity and inverse-group weighting;
- exact deterministic five-fold whole-shower grouping across both routes;
- exact diversity lambda `0.8`, scale `1.0`;
- exact parameter-free rank-sum fusion with v19;
- exact v19 fixed-membership control;
- exact #854-compatible equal-budget one-to-one maximum-total-F1 evaluation.

There is no feature, model, fold, diversity, membership, fusion, radius, threshold, or candidate search.

## Sole changed target

For each frozen family, determine its `best_label` exactly as in v22 from the combined two-year recurrent-shower comparison. This preserves grouping identity and prevents a family from choosing a different shower merely because the target definition changed.

For that fixed `best_label`, compute membership F1 separately on 2013 and 2014 using the same frozen family membership. The v23 regression target is:

`min(F1_2013, F1_2014)`

If no recurrent `best_label` exists, the target is zero. No alternative target (mean, geometric mean, harmonic mean, quantile, thresholded minimum, or weighted minimum) is evaluated in v23.

Grouping remains `SHOWER/<best_label>` whenever a best recurrent label exists, including near-misses; otherwise a route/family-specific negative group is used. Therefore all fragments and near-misses of the same known shower across both routes remain wholly absent from their own training fold.

## Frozen variants and gate

Exactly two successor orders are evaluated from the OOF predictions:
1. `worst_year_oof_quality`: exact #839 diversity ordering on v23 OOF predictions.
2. `worst_year_oof_v19_rank_sum`: parameter-free equal-weight rank-sum between that OOF order and exact v19 rank-sum.

The exact v19 order is retained as an identity control and must reproduce all four v19 metrics.

A v23 development PASS requires one frozen successor to beat the corresponding literature comparator in **all four** comparator/year panels: strictly higher macro-F1 and recovered-F1>0.5 count at least equal to the comparator in every panel. Selection uses the same robust four-panel lexicographic key used by v22.

Only an OOF all-panel PASS may fit and fingerprint the identical model architecture on all exposed SonotaCo development families. Any full-fit in-sample score is ineligible as promotion evidence. A v23 OOF failure freezes v23 as a no-go and does not authorize another target search.

## Firewall

SonotaCo 2013/2014 is exposed development only. No MAARSY, DMS, OrbitTrace target information, target-region event, or 20°–55° protected content is authorized. A later protected cross-survey validation requires a separate candidate-specific pretruth protocol after a v23 OOF PASS.
