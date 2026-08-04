# Partition-invariant multiscale subset scan: authoritative Stage-0 result

Runner workflow `30874121620` completed the full frozen 2019/2021/2023/2025 development benchmark from source SHA-256 `660f436e173ff01fbd3af6e5cf88df6e1caa2dbfbc63f499875327ecd597dcce`.

Evidence artifact:

- artifact ID: `8878959234`;
- artifact digest: `sha256:8750ae4455308a34507e5824d7905da742ecd3e9a3e73d195bc35f97f9c7e7f9`;
- selected-event SHA-256: `63e1389e2666d10b05138044f428609266b367cabab2542295c154a510e40f01`;
- audit SHA-256: `f8ba2446dce96d69652727092189903c40493e2fe741eb746f7fb5181edea778`.

GhostStream solar longitude 20.0°–55.0° was removed before all reservoirs, windows, calibration samples, scores, folds, and endpoints.

## Frozen panel

- 181 eligible established showers;
- 24 supported year-by-60° groups;
- 5,024 positive windows, including 3,768 weak k=4/6/8 windows;
- 1,536 independent negative windows;
- 256 same-corpus calibration windows per group;
- five complete complex-disjoint folds.

## Result

Weak-window AUROC:

- fully transductive adaptive multiscale candidate: **0.75483**;
- unchanged LCC: **0.80762**;
- marginal four-event scale: **0.81352**;
- marginal six-event scale: **0.77719**;
- marginal eight-event scale: **0.72919**;
- fixed local density: **0.78111**;
- fixed DBSCAN: **0.76828**.

Candidate fold AUROCs were **0.75926, 0.75434, 0.76495, 0.74720, 0.74889**. No fold collapsed below 0.70, but only three reached 0.75 and every fold was materially weaker than LCC and the single four-event scan.

Calibration was mixed:

- pooled FPR at alpha 0.05: **0.05339** — pass;
- pooled FPR at alpha 0.01: **0.00195** — pass;
- worst year-sector FPR at alpha 0.05: **0.17188** — fail against 0.120.

Candidate recall:

- k=4: **0.15446 / 0.02946** at alpha 0.05 / 0.01;
- k=6: **0.31290 / 0.10908**;
- k=8: **0.45701 / 0.23487**;
- k=12: **0.69984 / 0.45780**.

The candidate uniquely rescued 5.25% of k=4 positives at alpha 0.05, but its overall k=4 gain over LCC was only +0.00239 and its alpha-0.01 k=4 recall was lower than LCC. It also lost substantial k=6/k=8 sensitivity.

## Frozen-gate outcome

The method passed 9 of 19 gates. It failed:

- worst-sector false-positive control;
- minimum weak AUROC;
- AUROC proximity to both fixed and single-scale comparators;
- four-of-five fold threshold;
- both required k=4 gains over LCC;
- absolute k=4 recall at alpha 0.01;
- preservation of k=6 and k=8 recall at alpha 0.01.

Verdict: **`KILL_MULTISCALE_SUBSET_SCAN`**.

## Interpretation

The result rejects the hypothesis that combining 4-, 6-, and 8-event complete-link scans through a fully transductive adaptive maximum improves discovery. The four-event scale already carries the useful weak-stream signal. The six- and eight-event scales add weaker, correlated extremes; conformally calibrating their maximum reduces power and still leaves one conditionally unstable background sector.

Do not change scale weights, remove a scale, alter the transductive p-value construction, replace seeds, relax the worst-sector gate, or rerun this source. No 2018 data gate, catalogue scan, or GhostStream application is authorized by this result.
