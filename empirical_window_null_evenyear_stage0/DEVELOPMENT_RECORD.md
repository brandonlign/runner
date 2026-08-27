# Development record before untouched even-year testing

The untouched confirmation years are 2020, 2022, and 2024. Everything below used only development years 2019, 2021, 2023, and 2025, with solar longitude 20.0°–55.0° removed.

## Failed frozen Stage-1 formulation

PR #23 split sporadic events by a stable event-ID hash into separate calibration and audit backgrounds. Its established-shower power was strong but it failed conditional calibration:

- candidate weak AUROC: 0.80094
- local-density AUROC: 0.77483
- DBSCAN AUROC: 0.75780
- pooled FPR at alpha 0.05: 0.05241
- worst year-sector FPR at alpha 0.05: 0.16797
- failed sector: `2019:1`

The PR was closed without changing the frozen 0.120 worst-sector gate.

## Failure diagnosis

The selected artifact contained 191,170 unique unlabelled sporadic event IDs after blind-interval removal, with no blank or duplicated IDs. The problem was not an ID collision.

Within the failed `2019:1` sector, independently thinned event halves produced systematically different coherence-score distributions across most five-degree sub-bins. Calibration and audit windows were therefore not draws from one fixed empirical null distribution, despite the hash split being unbiased in expectation.

## Killed development alternatives

### Dual-scale distance ratio

Replacing absolute second-neighbor distance with a second-to-sixteenth-neighbor ratio worsened calibration and power:

- weak AUROC: 0.78828
- pooled FPR at alpha 0.05: 0.07161
- worst-sector FPR: 0.57812

Verdict: killed.

### Max over eight cross-fits

Selecting the strongest split preserved pooled calibration but reduced weak-stream recall:

- weak AUROC: 0.80129
- worst-sector FPR: 0.07812
- recall for k=4/6/8 at alpha 0.05: 0.13694 / 0.30096 / 0.43790

Verdict: killed.

### Mean of three strongest cross-fits

This raised raw AUROC slightly but again destabilized a sector and did not improve the smallest-stream endpoint:

- weak AUROC: 0.80576
- worst-sector FPR: 0.13281
- recall for k=4/6/8 at alpha 0.05: 0.14172 / 0.31131 / 0.45621

Verdict: killed.

## Selected development mechanism

Keep the original median-of-eight cross-fitted score, but generate calibration and audit windows independently from the **same fixed empirical sporadic corpus** rather than two event-level halves.

At full development resolution:

- weak AUROC: 0.80231
- local-density AUROC: 0.77817
- DBSCAN AUROC: 0.76302
- pooled FPR at alpha 0.05: 0.04297
- pooled FPR at alpha 0.01: 0.00846
- worst-sector FPR at alpha 0.05: 0.07422
- fold AUROCs: 0.81725, 0.79559, 0.79037, 0.79995, 0.80871
- recall for k=4/6/8/12 at alpha 0.05: 0.14013 / 0.32842 / 0.47452 / 0.69705
- recall for k=4/6/8/12 at alpha 0.01: 0.05693 / 0.16839 / 0.30932 / 0.51354

Four additional independent null batches all passed the frozen calibration thresholds:

| Batch | Pooled FPR 0.05 | Pooled FPR 0.01 | Worst-sector FPR 0.05 |
|---:|---:|---:|---:|
| 0 | 0.04232 | 0.00586 | 0.10938 |
| 1 | 0.04980 | 0.00651 | 0.08594 |
| 2 | 0.04329 | 0.00651 | 0.07812 |
| 3 | 0.04980 | 0.00814 | 0.10938 |

This record freezes the development choice. No untouched even-year result may be used to revisit the killed alternatives or alter the selected score.
