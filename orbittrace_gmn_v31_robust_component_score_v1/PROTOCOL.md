# OrbitTrace GMN v31 robust component-score v1 — frozen protocol

## Status

**PRE-OUTCOME SCIENTIFIC FREEZE.** This defines exactly one target-excluded GMN 2022/2023 successor to exact v31 before any candidate score, rank, or performance outcome is calculated.

Parent is the immutable 226-family v31 GMN offline-development package. Parent controls are recovered@25 `23`, recovered@50 `41`, recovered@100 `66`, top-100 dominant precision `0.7229521515453452`, MRR `0.050244164168646674`, qualified matches `95`.

No SonotaCo, protected target-region events, OrbitTrace target information/events, MAARSY, or DMS may enter this experiment.

## Scientific motivation

The frozen detector computes, for every retained within-year connected component, both:

- `best_score`: the maximum raw detector score among the component's retained quartets;
- `median_score`: the median raw detector score among those retained quartets.

Exact family construction keeps only the maximum component `best_score`; `median_score` is discarded before the hard-family payload and therefore is absent from exact v31. A family can consequently receive the same strong maximum score whether that evidence is broadly supported across its component's retained quartets or produced by one exceptional quartet.

This successor tests one distinct robustness principle: **a recurrent family should contain, in each independent year, at least one component whose detector evidence is broadly strong rather than merely having a high single maximum.**

The annual and cross-year aggregation is not searched. It is fixed to mirror the detector's already-established `year_strengths` semantics: strongest component within each year, then conservative minimum across years.

This is not robust feature scaling (closed v60), not activity/radial distribution recurrence, not component-count balance, not covariance/topology, and not a modification of memberships or detector thresholds.

## Sole scientific change

Reconstruct the exact frozen target-excluded 2022/2023 hard-family components using the same support source, catalogue source, candidate scorer, calibration, blind exclusion, and family builder that produced the immutable hard-family lineage.

For every exact hard family `f`:

1. Require its exact `component_ids` to resolve to frozen reconstructed component records and require the reconstructed family/component identity to match the immutable hard payload.
2. For each year `y in {2022,2023}`, compute

   `robust_y = max(component['median_score'] for component in f from year y)`.

3. Require at least one component in each year and every `median_score` finite; otherwise fail closed before scoring.
4. Append exactly one 24th coordinate:

   `robust_component_score_min = min(robust_2022, robust_2023)`.

No normalization by `best_score`, detector threshold, calibration maximum, component strength, event/quartet/anchor count, or source rank is permitted. No log, rank, percentile, ratio, balance, difference, p-value, clipping, or transform is used.

The exact existing 23 v31 coordinates remain byte-identical.

## Exact inherited v31 architecture

Everything except the appended coordinate remains exact v31:

- immutable 226 hard-family universe and memberships;
- exact v31 23D matrix and 8D centroid matrix;
- exact strict-whole-shower five-fold OOF split and frozen development labels;
- fold-training mean / population-standard-deviation scaling, zero std -> `1.0`;
- ordinary Euclidean distance;
- k=1 nearest positive and nearest nonpositive reference;
- margin `d_nonpositive - d_positive`;
- exact diversity lambda `0.8`, scale `1.0`, immutable hard-order tie semantics;
- exact equal 1-based rank-sum fusion with immutable P19 hard order;
- exact monotone GMN evaluator.

A technically valid run must reproduce exact hard family/component identity, exact parent 23D feature SHA, centroid SHA, parent OOF margin SHA, hard control, and fused parent control before evaluating the candidate.

## Binding PASS gate

The first technically valid candidate result is binding. PASS requires all:

1. recovered@100 > `66`;
2. recovered@25 >= `23`;
3. recovered@50 >= `41`;
4. top-100 dominant precision >= `0.7229521515453452`;
5. MRR >= `0.050244164168646674`;
6. qualified matches exactly `95`;
7. all provenance and protected-data checks pass.

A FAIL terminates this mechanism without SonotaCo access.

## No-rescue closure

After the first technically valid result, do **not** retry:

- maximum/minimum/mean/quantile of component `median_score` with another annual or cross-year aggregation;
- median/mean/trimmed/quantile score over all family quartets directly;
- `median_score / best_score`, score gaps, score ratios, threshold-normalized or calibration-normalized scores;
- component-strength blends or weights;
- score transforms, ranks, percentiles, clipping, bins, thresholds, source/year-specific rules;
- event/quartet/anchor/component count weighting;
- alternate detector score statistic or another robust-score summary motivated by this outcome;
- feature subsets, metric/k/scaling/fold/reference changes;
- diversity/fusion/weight/rank-window/budget changes;
- blending with activity-KS, radial-KS, component-balance, stability, or another failed successor;
- any post-result identity-specific correction or second search.

Any later successor after a binding FAIL must change mechanism class and be independently motivated/frozen.

## Firewall

Scientific role: `TARGET_EXCLUDED_GMN_2022_2023_V31_SUCCESSOR_DEVELOPMENT_ONLY`.

Required assertions: protected blind exclusion `[20.0,55.0]`; SonotaCo 2013/2014 access=false; target-information access=false; target-region event access=false; MAARSY scientific access=false; DMS scientific access=false.