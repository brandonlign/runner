# Relative exact-quartet coherence: authoritative Stage-0 result

Runner workflow `30875750795` completed the frozen 2019/2021/2023/2025 development screen from source SHA-256 `56b184abcfc11c095e376cb50f9e18fb0d351e854de5e2ad7228177338da841f`.

Artifact `8879530323` was preserved with digest `sha256:eb09e5df4340a9bbf08c196b19959ec9eae5eec3cbf0b1bc46e11457a8450f29`.

## Result

- relative exact-quartet weak AUROC: **0.75597**;
- exact K4 / nearest-neighbor quartet / LCC / density / DBSCAN: **0.76921 / 0.77016 / 0.77363 / 0.76978 / 0.74248**;
- pooled FPR at 0.05 / 0.01: **0.05013 / 0.00651**;
- worst year-sector FPR at 0.05: **0.15625**;
- k=4 recall at p ≤0.05 / 0.01: **0.15303 / 0.06061**;
- k=6 recall at p ≤0.05: **0.29924**;
- k=8 recall at p ≤0.05: **0.42576**.

The candidate failed worst-sector calibration, the 0.80 AUROC gate, density and LCC preservation, fold consistency, k=4 recall/gain, and k=8 preservation.

Verdict: **`KILL_RELATIVE_EXACT_QUARTET`**.

Normalizing the strongest exact quartet by the window's median four-neighbor scale removed useful stream signal faster than it removed structured background. No scale statistic, threshold, sector, seed, gate, or endpoint will be changed, and no confirmation-year or GhostStream application is authorized.
