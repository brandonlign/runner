# Phase-adaptive nested conformal coherence: July 2026 result

## Authoritative execution

Runner workflow `30875478565` executed the complete frozen July-only sequence from commit `1719b05cdbb1061c2628917c7387586b89e9490a`.

Preserved artifacts:

- July data audit: artifact `8879372222`, digest `sha256:2f86c61bbff8565b8b3e9683ceb63ac405ff302a73087415cd8ec620bd9eeb7c`;
- label-blind null audit: artifact `8879424932`, digest `sha256:bc905584599af002c79a0b1ec4d161f2eafc4e4755565544fca0006d5283fd88`;
- untouched power audit: artifact `8879440879`, digest `sha256:6eec7b565ed64e2567b35f2d245494de69c4cec29a0a9e0d203dce14fd64b811`.

The decoded frozen source had SHA-256 `11f7590675cca5812566a39fa11e07de7a905c0a468c45ef184246cd65c9eec7`.

## Frozen data gate: pass

The untouched official July 2026 GMN file cleared every predeclared data gate:

- eligible showers: **44**;
- strong showers: **30**;
- eligible complex units: **41**;
- multi-shower complex units: **3**;
- quality sporadic events: **63,755**;
- selected-event completeness: **1.000**;
- supported globally anchored 10-degree blocks after blindness: **4** (`90–130°`).

Verdict: `PROCEED_TO_PHASE_ADAPTIVE_JULY`.

## Label-blind null gate: pass

Eight independent batches used separate inner, outer, and audit window banks. The method passed every frozen calibration gate:

- mean batch FPR at alpha 0.05: **0.04614**;
- mean batch FPR at alpha 0.01: **0.00513**;
- one-sided 95% upper bound for mean FPR: **0.05072** at 0.05 and **0.00914** at 0.01;
- maximum batch FPR at 0.05: **0.06055**;
- maximum block-average FPR at 0.05: **0.05469**.

Verdict: `PROCEED_TO_JULY_POWER`.

This is a genuine untouched confirmation that the independent outer conformal layer controlled false alarms under July seasonal background drift.

## Untouched real-shower power gate: fail

The power panel contained:

- included showers: **38**;
- positive windows: **1,216**;
- weak positive windows (`k=4,6,8`): **912**;
- independent negative windows: **1,024**.

Raw discrimination:

- candidate weak AUROC: **0.779733**;
- fixed local-density AUROC: **0.753064**;
- fixed DBSCAN AUROC: **0.744659**.

The candidate beat both fixed comparators, but missed the frozen absolute AUROC gate of `0.78` by `0.000267`.

False positives:

- FPR at alpha 0.05: **0.064453**, above the frozen `0.060` ceiling;
- FPR at alpha 0.01: **0.002930**, pass;
- worst-block FPR at alpha 0.05: **0.089844**, pass.

Recall:

| members | p <= 0.05 | p <= 0.01 |
|---:|---:|---:|
| 4 | **0.151316** | **0.003289** |
| 6 | **0.368421** | **0.042763** |
| 8 | **0.588816** | **0.095395** |
| 12 | **0.799342** | **0.171053** |

All alpha-0.05 recall gates passed, and recall was monotonic. All three required alpha-0.01 weak-stream recall gates failed.

Complex-fold AUROCs were:

- fold 0: **0.762637**;
- fold 1: **0.834195**;
- fold 2: **0.775675**;
- fold 3: **0.746755**;
- fold 4: **0.776759**.

Every fold passed the frozen consistency gates.

Verdict: **`KILL_PHASE_ADAPTIVE_JULY_POWER`**.

## Interpretation

The candidate produced two real advances:

1. its nested phase-adaptive calibration generalized cleanly to a completely untouched month;
2. its raw coherence score beat both fixed density and DBSCAN comparators across the July weak-shower panel.

It still did not satisfy the complete discovery-method standard. July weak showers rarely reached the predeclared 1% significance endpoint, and the independent power negatives were modestly anti-conservative at 5%. The result is not rescued by the near-threshold AUROC, comparator wins, or strong 5% recall.

No block width, bank size, interpolation rule, seed, p-value threshold, AUROC threshold, comparator, fold, or shower subset will be changed. This exact candidate must not be applied to GhostStream.
