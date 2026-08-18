# OrbitTrace recurrent-EOM direct GMN literature benchmark v1

## Status
FROZEN BEFORE IMPLEMENTATION OUTCOME AND BEFORE THIS BENCHMARK OPENS GMN SHOWER TRUTH.

Question: on the exact protected-region-excluded GMN 2022/2023 development universe, does the already-selected recurrent-EOM HDBSCAN v1 outperform portable published catalogue clustering baselines under a common annual shower-matching evaluation?

This benchmark does not change or select the OrbitTrace method. Recurrent-EOM is immutable from binding GMN run 31827903547, artifact 9229646556, digest sha256:a0b1ba017696b32cf2e19b3542430adac7bfd13fa2fb78494b6d42742aa35f6. Its prelabel and result SHA-256 are e304f6660697ed27a7e2e546ba2b9f2ecdb43f923745cb7424a3781ad55b9ad1 and 433c641f57122b244b9476f5cbcb5e6f82956d9467270a9f24945600a32d2106.

## Firewall
Use only GMN 2022/2023 rows after inclusive solar-longitude [20,55] removal. Candidate construction must finish and be SHA-frozen before shower truth is loaded. OrbitTrace target information/events, SonotaCo scientific values, AMOS, MAARSY, DMS and ASFN/EFN event-level data are forbidden.

## Common geometry
Use the exact target-excluded GMN observation-space geometry already used by recurrent-EOM development: solar longitude, Sun-centered geocentric ecliptic radiant longitude/latitude, and geocentric speed. No orbital elements or shower labels enter clustering.

## Literature baseline A: Sugar et al. 2017 DBSCAN core
Implement the published central-value DBSCAN clustering core using the six-dimensional GEO vector
[cos(sol), sin(sol), sin(lon)cos(lat), cos(lon)cos(lat), sin(lat), Vg/72].
Use min_samples=5. For each year independently, compute exact Euclidean fourth-nearest-neighbor distances and set epsilon to the 23rd percentile, as published. Run scikit-learn DBSCAN with Euclidean metric. Negative labels are noise.

This is explicitly the portable deterministic clustering core of Sugar et al. 2017. The paper's 1000 measurement-error resampling cannot be reproduced without importing survey-specific uncertainty metadata into this benchmark, so no claim of reproducing the full uncertainty-retained-master procedure is allowed.

## Literature baseline B: Peña-Asensio & Ferrari 2025 HDBSCAN GEO
Use the published GEO vector above, unnormalized, HDBSCAN EOM, min_cluster_size=100, min_samples=100, Euclidean metric, cluster_selection_epsilon=0, allow_single_cluster=False. This is the paper's principal maximum-agreement GEO/EOM configuration at minimum cluster size 100. No parameter sweep or GMN-label selection is allowed.

## Pretruth freeze
For each year and comparator, serialize every non-noise cluster membership, parameters, event-universe hash, cluster count/noise count, and exact source identities. Also serialize the immutable recurrent-EOM pooled candidate list from run 31827903547. SHA-freeze and upload the complete payload before truth evaluation.

## Common evaluation
For each year separately, eligible known showers have >=4 accessible GMN members. Restrict each recurrent-EOM pooled family to that year. For every eligible shower and every returned candidate/cluster compute precision, recall and F1; use a Hungarian maximum-F1 one-to-one assignment for each method. Report macro-F1 over all eligible showers, assigned showers with F1>0.5 and >0.8, macro precision/recall, candidate/cluster count, and noise fraction where defined.

Because the published literature catalogues are unordered, MRR is NOT invented for them. Recurrent-EOM's existing zero-filled MRR is reported only as an OrbitTrace retrieval diagnostic, not as a head-to-head literature metric.

## Binding interpretation
Recurrent-EOM beats a literature baseline on GMN only if in BOTH 2022 and 2023 it has strictly higher macro-F1 and at least as many assigned showers with F1>0.5. Report the four year-by-baseline pair gates and an overall 4/4 count. No aggregate rescue, threshold tuning, parameter sweep, reranking, or post-result method modification is allowed.

A valid result is descriptive for target-excluded GMN and does not replace the existing SonotaCo 4/4 result or establish superiority to every method in the literature.