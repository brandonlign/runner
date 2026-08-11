# OrbitTrace v31 HDB representative-ceiling diagnostic v1

## Scientific role

Post-result diagnostic only after v31 (#1027) produced the strongest HDBSCAN-2014 near miss: 9/9 recovered showers with macro-F1 0.1519812377 versus HDBSCAN 0.1568959558, while HDBSCAN-2013 remained 9/10. This diagnostic does not define, evaluate, or select a deployable successor ranker.

The question is deliberately narrow: **holding fixed the shower-label set that exact v31 actually surfaced, is the remaining HDBSCAN macro-F1 gap attributable to choosing weaker candidate representatives for those already-surfaced showers?**

## Frozen v31 reproduction

Use the immutable #950 v22 71-dimensional pretruth payload and exact v31 scientific rule unchanged:
- deterministic strict whole-shower five-fold OOF;
- fold-training mean / population standard deviation (`ddof=0`) over all 71 dimensions, zero standard deviation replaced by 1;
- annual positives defined by the already-frozen event `F1_y > 0.5` for the exact fixed v22 recurrent label;
- one-nearest positive and one-nearest nonpositive ordinary Euclidean distance;
- annual margin `d_nonpositive - d_positive`;
- annual combination `min(margin_2013, margin_2014)`;
- exact #839 diversity lambda 0.8 / scale 1.0;
- one equal rank-sum with immutable v19.

Exact v31 HDBSCAN panel metrics must reproduce before any ceiling statistic is accepted:
- 2013: macro-F1 `0.14888037368183737`, recovered `9`, budget `11`;
- 2014: macro-F1 `0.15198123772301594`, recovered `9`, budget `9`.

## Exact v31 assignment set

For each HDBSCAN year, run the exact existing equal-budget Hungarian evaluator on v31's top-budget active families. Retain only **positive-overlap assignments** (`assigned F1 > 0`) from that exact Hungarian solution. This fixed label set is the `v31_assigned_label_set` for that year. Zero-F1 padded/tied assignments are excluded because they do not represent a shower actually surfaced by v31.

The exact v31 assignment table (label, selected family ID, selected family rank, F1) is preserved.

## Representative ceiling

Holding `v31_assigned_label_set` fixed, form an F1 matrix between those labels and **all fixed HDBSCAN-route candidate families in the immutable #950 universe that contain at least one event from that year's truth universe**. Use one-to-one Hungarian assignment to maximize total F1 over the fixed label set.

For direct comparability with literature macro-F1, every eligible HDBSCAN truth shower not in `v31_assigned_label_set` remains exactly zero. Therefore:

`same_label_representative_ceiling_macro_f1 = sum(best one-to-one F1 for fixed assigned labels) / number of all eligible HDBSCAN truth showers`.

The ceiling recovered count is the number of those fixed-label oracle assignments with F1 > 0.5. The diagnostic reports whether this same-label representative ceiling would clear the frozen HDBSCAN macro-F1 and recovery count, but **this is an oracle diagnostic, not a candidate method or superiority result**.

For each fixed assigned label, report the v31 selected family/rank/F1, oracle family/original fixed-universe rank/F1, F1 gain, and whether the oracle representative was already inside the v31 top-budget set.

## Interpretation boundary

- If the same-label representative ceiling clears HDBSCAN, then representative choice is sufficient in principle for that year's remaining gap, and a future separately frozen successor may investigate a **label-free hierarchical representative-quality rule** after group discovery.
- If it cannot clear HDBSCAN, then perfect representative choice for v31's surfaced labels is insufficient and the remaining failure necessarily includes shower-label/group discovery.

This diagnostic does **not** define the future representative selector, inspect alternative selector features, tune a hierarchy, re-rank families, alter memberships, or evaluate any deployable graph/quality rule.

## Explicit prohibitions

No new ranking order, representative selector, graph transform, feature subset, model, threshold, source quota, annual route rule, parameter search, literature promotion candidate, MAARSY/DMS access, OrbitTrace target information, target-region event, or protected solar-longitude 20-55 degree content is authorized.

SonotaCo 2013/2014 remains exposed development-only.
