# OrbitTrace v61 anomalous-fold concentration diagnostic v1

## Scientific role

This is a **post-result exposed-development mechanism diagnostic only** after binding v59 and v60 failures. It does not define, score, rank, or evaluate a successor.

Exact v31 remains the parent. v59 exposed an outcome-free geometry anomaly under the exact inherited v31 strict-OOF folds/scaling: fold 4 had mean nearest-training distance about `81.85`, whereas folds 0–3 were about `2.44–2.82`. v60's separately frozen robust-scaling test then failed 0/4 and did not remove the fold-4 distance anomaly. Robust scaling is closed; v61 does not reopen it.

The sole question here is narrower: **are the annual HDB shower groups that v31 can recover but misses at its fixed literature budget disproportionately assigned to the already-identified anomalous fold 4?**

SonotaCo remains `EXPOSED_DEVELOPMENT_ONLY`, not external validation.

## Authoritative fixed status source

Use the binding #1046 v31 HDB missed-label rank-gap diagnostic unchanged:

- workflow run `31451236076`;
- artifact `9086399760`;
- artifact digest `sha256:a2c373df77ef7e0065c1d8aceb1f6e5826f1e30b6286f2331c362d959f1d7f69`;
- result JSON SHA-256 `e4e09546e17b9a5da7ce12ad9af4bb7129533fd9b5be846ebc859719f01a9758`.

#1046 already fixes, for each annual eligible HDB shower group, whether it has any fixed candidate with annual F1>0.5 and whether such a recoverable group is surfaced or missed by exact v31 at the fixed annual budget. v61 must not recompute, alter, or replace those representatives/classes.

## Frozen anomalous fold

The anomalous fold is exactly integer `4`. This is frozen before #1046 surfaced/missed rows are loaded into the v61 diagnostic and comes from the already-observed v59 geometry anomaly, not from shower identity or v61 outcome.

Fold assignment uses the exact inherited deterministic strict-group function:

`deterministic_fold('SHOWER/' + label)`.

No alternate fold index, fold subset, distance threshold, or post-result fold search is allowed.

## Sole statistic

For each year separately (`2013`, `2014`):

1. retain only #1046 rows with `candidate_recoverable == true`;
2. classify them exactly as `SURFACED` if `v31_surfaced_recoverable == true`, otherwise `MISSED` when `recoverable_but_missed == true`;
3. compute the inherited deterministic fold for the row's frozen shower label;
4. compute

`anomalous_fold_fraction = count(fold == 4) / class_count`

for MISSED and SURFACED classes.

The year passes iff

`missed_anomalous_fold_fraction > surfaced_anomalous_fold_fraction`.

The diagnostic PASS requires this strict inequality in **both** 2013 and 2014. No effect-size threshold beyond strict direction is selected.

## Interpretation boundary

A PASS would establish only that the already-known anomalous OOF fold is overrepresented among v31's recoverable-but-missed HDB groups in both years. It would authorize consideration of a separately frozen **symmetric fold-output calibration mechanism**, not a fold-4 exception.

A FAIL closes the fold-concentration explanation. Do not rescue it with another fold, fold union, fold-specific threshold, mean-vs-median status statistic, alternate representative, budget-conditioned subset, or shower identity list.

## Explicit prohibitions

No new candidate order, successor score, literature panel, fold-specific promotion, rank window, top-k/budget exception, fold search, alternate representative, feature/model/metric/k/scaling/threshold/annual-combiner/diversity/fusion/source-quota search, target access, MAARSY/DMS access, or post-result second diagnostic.

## Firewall

Protected OrbitTrace solar longitude `20°–55°` remains inaccessible. Do not access OrbitTrace target information or target-region events. Do not access MAARSY or DMS scientifically. SonotaCo remains `EXPOSED_DEVELOPMENT_ONLY`.