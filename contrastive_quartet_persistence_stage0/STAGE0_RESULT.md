# Contrastive quartet persistence: authoritative Stage-0 result

Runner workflow `30874855776` completed the full frozen 2019/2021/2023/2025 development benchmark from source SHA-256 `b5ca098781ae505d9cd091ceb2036ffcacb1e0a7269a6aaed6c3b816b4e13baa`.

Evidence artifact:

- artifact ID: `8879205304`;
- artifact digest: `sha256:a81f0e9ea0e4444eee9f5d5b985b3afcd478b0fb7c3e6fd0120921d91d8170dd`;
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

- contrastive quartet persistence candidate: **0.75619**;
- raw partition-invariant quartet: **0.80633**;
- unchanged LCC: **0.79813**;
- fixed local density: **0.77534**;
- fixed DBSCAN: **0.75971**.

Candidate fold AUROCs were **0.79876, 0.74302, 0.74189, 0.74202, 0.75605**. No fold fell below 0.70, but only two reached 0.75 and the candidate was weaker than the raw quartet and LCC in every fold.

Calibration passed every frozen gate:

- pooled FPR at alpha 0.05: **0.04297**;
- pooled FPR at alpha 0.01: **0.01042**;
- worst year-sector FPR at alpha 0.05: **0.10938**.

Candidate recall:

- k=4: **0.16720 / 0.06051** at alpha 0.05 / 0.01;
- k=6: **0.31051 / 0.15207**;
- k=8: **0.37898 / 0.20064**;
- k=12: **0.29220 / 0.13535**.

The candidate uniquely rescued 135 k=4 positives at alpha 0.05, or **10.75%** of all k=4 positives. It also exceeded LCC k=4 recall at both thresholds. However, k=8 sensitivity was materially below LCC and k=12 sensitivity collapsed, violating monotonicity at both thresholds.

## Frozen-gate outcome

The method passed 11 of 19 gates. It failed:

- minimum weak AUROC;
- AUROC proximity to the raw quartet;
- AUROC proximity to the strongest fixed comparator;
- four-of-five fold consistency;
- preservation of k=8 recall at alpha 0.05;
- preservation of k=8 recall at alpha 0.01;
- recall monotonicity at alpha 0.05;
- recall monotonicity at alpha 0.01.

Verdict: **`KILL_CONTRASTIVE_QUARTET_PERSISTENCE`**.

## Interpretation

The fixed 13th-neighbor normalization genuinely repaired conditional calibration and retained sparse k=4 sensitivity. It failed because the denominator is contaminated by the signal for richer streams: as the coherent population grows, the anchor's 13th-neighbor radius contracts, reducing the contrast score even though the stream is real. The resulting non-monotonic response is structural rather than a threshold accident.

Do not change the context rank, core size, ratio transform, anchor aggregation, calibration sample, seed, threshold, fold, or gate. No 2018 data gate, catalogue scan, or GhostStream application is authorized by this result.
