# OrbitTrace literature-method comparison: source audit

Status: source-only preparation. No meteor archive, label, score, p-value, fold endpoint, or OrbitTrace member is accessed in this stage.

## Purpose

Expose the exact reusable interfaces in the immutable SonotaCo fixed-4° final-development program before writing any literature comparator. The audit decodes the already frozen candidate source and records its AST inventory and relevant source excerpts without executing the benchmark.

## Frozen scientific boundary

- The OrbitTrace detector remains unchanged.
- The SonotaCo 2025 and SonotaCo 2023 benchmark outcomes remain frozen.
- Existing weak-positive episodes, negative windows, folds, calibration-panel sizes, seeds, and metrics must be reused exactly.
- The solar-longitude blind interval 20°–55° inclusive remains removed before labels, reservoirs, windows, scores, folds, or endpoints.
- No new detector tuning, calibration reseeding, panel selection, gate relaxation, or additional validation panel is authorized.
- OrbitTrace is not used to select, configure, or rank literature comparators.

## Comparator tiers to implement after this audit

1. Sugar et al. DBSCAN: Sun-centered ecliptic radiant, geocentric speed, and solar-longitude geometry, with the published distance construction and uncertainty treatment reproduced as closely as the SonotaCo fields permit.
2. Brown et al. CMOR-style 3D wavelet: Sun-centered ecliptic radiant and geocentric speed wavelet response in fixed solar-longitude windows. Because the original method is a multi-year catalogue search, the episode benchmark will be labelled an adapted local-detection implementation rather than a literal catalogue reproduction.
3. Peña-Asensio and Ferrari HDBSCAN: published GEO and ORBIT feature vectors, fixed cluster-selection rules, and hyperparameters selected only from the original paper or a comparator-development panel that cannot alter the frozen OrbitTrace method.
4. Classical orbital-distance linkage: exact Southworth-Hawkins D criterion and, where all required observables exist, the Jopek D_N criterion, paired with preregistered complete-link and single-link variants.

## Fairness rules

- Each comparator receives the same event rows in each frozen episode.
- Each comparator is calibrated with the same negative windows used for the fixed-4° method.
- AUROC, pooled false-positive rates, fold AUROCs, k=4/6/8/12 recall, and monotonicity are computed identically.
- Comparator parameters are fixed before the independent SonotaCo 2023 run.
- The literature method may use parameters explicitly published by its authors. When a parameter cannot be transferred directly because of survey or scale differences, the admissible choices are frozen in advance and evaluated symmetrically on SonotaCo 2025 only.
- Results will distinguish faithful reproduction, benchmark adaptation, and internal baseline.

## Interpretation boundary

This comparison can establish relative sparse-episode detection performance on the frozen SonotaCo benchmark. It cannot by itself establish complete blind catalogue rediscovery, reproduce a radar survey on optical data, or turn the targeted OrbitTrace recovery into the original discovery method.
