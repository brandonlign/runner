# Dual-coherence quartet rescue: authoritative Stage-0 result

Runner workflow `30873117568` completed the full frozen 2019/2021/2023/2025 development screen from source SHA-256 `d03c5013e0e75bea7c4ddf896a0f3c0fa108df1bff192e836144674287840dbc`.

Evidence artifact:

- artifact ID: `8878584136`
- artifact digest: `sha256:0f64499ab4435847d66bf8d9ddba2db927de3a93ab191165e8dad77793d2f349`
- exact odd-year event artifact SHA-256: `63e1389e2666d10b05138044f428609266b367cabab2542295c154a510e40f01`
- exact audit SHA-256: `f8ba2446dce96d69652727092189903c40493e2fe741eb746f7fb5181edea778`

## Frozen panel

- 24 supported year-sector groups;
- 181 eligible established showers;
- 5,024 positive windows, including 3,768 weak k=4/6/8 windows;
- 1,536 independent audit-negative windows;
- 128 inner-calibration and 128 outer-calibration windows per group;
- GhostStream solar longitude 20.0°–55.0° removed before every pool, score, calibration set, fold, and endpoint.

## Result

Weak-window AUROC:

- nested union: **0.77592**;
- unchanged LCC: **0.80332**;
- quartet cover alone: **0.80881**;
- fixed local density: **0.78222**;
- fixed DBSCAN: **0.76743**.

The nested outer calibration remained conservative and stable:

- pooled union FPR at alpha 0.05: **0.03190**;
- pooled union FPR at alpha 0.01: **0.00195**;
- worst year-sector FPR at alpha 0.05: **0.09375**.

However, it lost the exact sensitivity it was designed to recover:

- union k=4 recall at alpha 0.05: **0.12102**;
- unchanged LCC k=4 recall: **0.12261**;
- quartet-alone k=4 recall: **0.14889**;
- union k=4 recall at alpha 0.01: **0.02787**;
- unchanged LCC k=4 recall: **0.03503**;
- quartet-alone k=4 recall: **0.04299**.

The union uniquely rescued 39 k=4 positives at alpha 0.05, or 3.11%, but lost more LCC detections than it gained. It also materially reduced k=6 and k=8 recall, especially at alpha 0.01.

Fold AUROCs were stable but uniformly weaker than the component scores:

- fold 0: **0.78881**;
- fold 1: **0.76642**;
- fold 2: **0.78337**;
- fold 3: **0.77198**;
- fold 4: **0.77006**.

## Frozen-gate outcome

The method passed 10 of 19 gates. It failed:

- union weak AUROC at least 0.79;
- AUROC within 0.01 of unchanged LCC;
- both absolute k=4 recall gates;
- both required k=4 gains over LCC;
- preservation of k=8 recall at alpha 0.05;
- preservation of k=6 and k=8 recall at alpha 0.01.

Verdict: **`KILL_DUAL_COHERENCE_RESCUE`**.

## Interpretation

The partition-invariant quartet score contains real weak-shower signal and, as a raw score, slightly exceeded LCC AUROC. The proposed nested minimum-p union did not exploit that complementarity. Its independent outer calibration correctly controlled false positives, but the combination became too conservative and discarded more LCC detections than the quartet channel rescued.

This exact candidate is closed. Do not change component weights, p-value aggregation, calibration counts, seeds, thresholds, or gates and rerun it. No fresh-year data gate, catalog scan, or GhostStream application is authorized by this result.
