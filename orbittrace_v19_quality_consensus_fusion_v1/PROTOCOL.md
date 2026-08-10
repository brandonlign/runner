# OrbitTrace v19 — quality / cross-generator-consensus fusion

## Status and motivation

v17 proved that the broad hard/P19/P20 candidate universe plus fixed full-membership expansion can beat Sugar in both matched SonotaCo years, but its very top ranks remain inefficient against catalogue HDBSCAN at budgets 11 and 9. v18 exhausted the complete pre-existing #839 diversity grid: all 15 settings still won only the two Sugar panels.

A truth-aware diagnostic on the already-exposed v17 family universe establishes that proposal recall is no longer the binding problem: there exists a single nested top-9/top-11 subset of already-detected v17 families whose exact #854 F1 beats HDBSCAN in both 2013 and 2014. That oracle is diagnostic only and may not enter deployment ranking.

The next admissible target is therefore **truth-free top-budget ranking**, not another detector or membership change.

## Pre-SonotaCo signal reused

PR #843, created before this SonotaCo result, froze a label-free cross-generator consensus score over the hard/P19/P20 union. Its pure greedy consolidation failed the GMN recall gate, but it materially increased top-100 dominant precision to ~0.811 and reduced fragment burden. The exact best GMN setting was radius `1.0`, source-quality weight `2.0`.

v19 does not revive #843 consolidation and never deletes a family. It reuses only its already-defined **per-family pre-suppression consensus score** as a second independent ranking signal.

For each family, using the exact raw hard/P19/P20 proposal union before membership expansion:

- neighbors are built exactly as in #843, generalized only from years `(2022,2023)` to the explicit canonical two-year input pair;
- both-year centroid distance is the maximum frozen support-module centroid distance across the pair;
- prefilter: first-year solar-longitude separation <=7 deg, ecliptic-latitude separation <=4 deg, geocentric-speed separation <=4 km/s;
- consensus radius is fixed at `1.0`;
- exact #843 score is
  `3*(number_of_neighbor_sources-1) + 1.5*log1p(cross_source_neighbors) + 0.35*log1p(degree) - 2.0*source_rank_percentile`;
- source-rank percentile is computed in the original generator order exactly as #843 did;
- no truth enters edge construction or scoring.

## Frozen v19 ranking candidates

The v17 quality/diversity rank and the raw #843 consensus-score rank are each complete orders over the same union. v19 freezes exactly three successor orders plus one control:

1. `consensus_only`: raw #843 consensus-score order;
2. `rank_sum`: ascending `quality_rank + consensus_rank`;
3. `rank_product`: ascending `quality_rank * consensus_rank`;
4. `v17_control`: unchanged v17 quality/diversity order, used only as an identity control and never eligible to be called a new successor.

Rank-sum and rank-product are the same two parameter-free equal-weight rank-fusion forms already used in the pre-existing OrbitTrace v10 rank-consensus laboratory (#353). No fusion weight, cutoff, exponent, radius, or local search is introduced.

Ties are deterministic and frozen before truth:

- rank sum: `(sum, quality_rank, consensus_rank, family_id)`;
- rank product: `(product, sum, quality_rank, consensus_rank, family_id)`;
- consensus-only: exact #843 score tuple order, then stable family ID.

## Candidate membership

Detector proposals and membership are unchanged from v17. For each frozen order:

- same exact #862 pair-portable hard/P19/P20 universe;
- same v15 adaptive hard-family rank input and exact #853/#860 learned quality score;
- same fixed #461/v16 joint density+trajectory conformal membership expansion for ranks 1–100;
- same alpha `0.05`, k=2, affine order 1, +/-6 degree activity padding, density/residual ceilings 1.5, equal Fisher weights, empirical joint recalibration, and no recursive support;
- original members are never removed.

Thus v19 changes only final family order.

## Exposed-development evaluation

SonotaCo 2013/2014 is already exposed and is development-only. For each matched row route, all four rank variants are generated and hash-frozen before the immutable exposed truth/comparator artifact is loaded.

The `v17_control` must reproduce the exact v17 family memberships and all four exact v17 metrics; otherwise the run is invalid.

Each of the three successor variants is evaluated with exact #854 equal-budget one-to-one F1 semantics on Sugar 2013/2014 and HDBSCAN 2013/2014.

Selection is one-shot and lexicographic, maximized in this order:

1. number of panels satisfying both literature-superiority conditions;
2. minimum macro-F1 ratio candidate/comparator;
3. minimum recovery ratio candidate/comparator;
4. mean macro-F1 ratio;
5. mean recovery ratio;
6. deterministic method preference `rank_sum`, then `rank_product`, then `consensus_only` only as a final exact tie-break.

A panel passes only if candidate macro-F1 is strictly greater than the frozen literature comparator and recovered showers with F1>0.5 is at least the comparator count.

No second fusion family, radius, weight, threshold, membership change, or post-result local search is permitted in v19. If all three fail four-panel superiority, preserve the result and diagnose the next ranking architecture separately.

## Claim boundary and firewalls

Even an all-four-panel v19 win is **exposed SonotaCo development superiority only**. It is not external validation. A winning successor would have to be frozen before any protected validation dataset is opened.

No MAARSY scientific values, DMS scientific values, OrbitTrace target information, or target-region event access is authorized here. Solar longitude 20°–55° remains inaccessible to target-containing work. Original OrbitTrace discovery provenance remains historical blind HDBSCAN.
