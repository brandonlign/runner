# OrbitTrace physical-scale modal-basin cross-scale diagnostic v1

## Status

**FROZEN BEFORE IMPLEMENTATION AND BEFORE ANY DIAGNOSTIC OUTCOME.**

This is a zero-label structural diagnostic only. It is not a shower-recovery successor and cannot promote a paper method.

It follows the target-excluded evidence in PRs #1272–#1278 and the preserved earlier field/wavelet lineage:

- fixed HDBSCAN point-support resolution collapses as catalogue size falls;
- stable density coordinates have repeatedly failed when discrete family membership is defined by sample-sensitive point trees;
- the old local-contrast histogram detector failed because shared persistent background structure generated excess false alarms;
- multi-anchor wavelet v3 produced a strong transferable continuous ranking, but its catalogue construction percolated 67,584 anchors into only 23 recurrent families;
- low-rank/group-sparse background decomposition is already closed because it absorbed weak recurring streams.

The present diagnostic therefore changes only the **membership topology**: families are attraction basins of a smooth physical-scale density estimate rather than connected point components, overlap families, or background-subtracted residuals.

No shower truth is used.

## 1. Firewall

Use only target-excluded GMN 2022+2023 geometry. Inclusive solar longitude `[20.0,55.0]` is removed before geometry.

Forbidden:

- OrbitTrace target information or target-region events;
- shower labels/truth in any statistic, fit, gate, or interpretation;
- SonotaCo scientific access;
- ASFN or EFN event-level access;
- AMOS scientific access;
- MAARSY or DMS scientific access;
- any result-informed bandwidth, support, feature weight, center-merging rule, subset, salt, metric, or gate change.

## 2. Frozen nested subsets

Reuse the exact PR #1272 hash rule:

`H(eid) = uint64_be(SHA256('ORBITTRACE_SCALE_STRESS_V1|' + eid)[0:8])`.

Use exactly four nested pairs:

- coarse denominator `128`, buckets `0,1,2,3` (~5.8k events);
- fine denominator `1024`, the same buckets (~0.7k events).

For each bucket, the fine universe is a strict subset of the coarse universe.

No other denominator, bucket, salt, or replicate is authorized.

## 3. Frozen physical coordinate map

The modal field uses only physical scales already present in the preserved Brown/multi-anchor wavelet lineage:

- 10° solar-longitude local episode window -> **5° half-width**;
- **4° radiant** scale;
- **10% speed** scale.

For each event define a six-coordinate embedding `Z`:

- solar longitude circle: `(cos(sol), sin(sol)) / h_sol` where `h_sol = 2 sin(5°/2)`;
- Sun-centered ecliptic radiant unit vector `(cos(lon)cos(lat), sin(lon)cos(lat), sin(lat)) / h_rad` where `h_rad = 2 sin(4°/2)`;
- speed coordinate `ln(v_g) / ln(1.1)`.

Thus a 5° solar-longitude displacement, a 4° radiant displacement, or a 10% multiplicative speed displacement is approximately one unit in its inherited physical coordinate. No empirical standardization is applied.

The exact embedding is frozen before outcome.

## 4. Modal clustering

Use `sklearn.cluster.MeanShift` as a direct mode-basin estimator on `Z`:

- `bandwidth = 1.0`;
- `seeds = None` (every observation is a seed);
- `bin_seeding = False`;
- `min_bin_freq = 1`;
- `cluster_all = True`;
- `max_iter = 300`;
- `n_jobs = 1`.

Before fitting, sort events by exact event ID so input order is deterministic.

No bandwidth estimation, quantile estimation, seed thinning, mode-count target, post-fit center merging, or alternate kernel/scale is allowed.

MeanShift's own frozen center-consolidation and basin-assignment rules are used unchanged.

## 5. Candidate memberships

Every MeanShift basin with at least **4** observed events is an eligible modal membership. The value four is the project's established minimum evaluable shower support and does not affect the fitted density modes.

Basins with fewer than four events are reported but excluded from candidate comparison.

No ranking or significance score is introduced in this diagnostic.

## 6. Exact recurrent-EOM comparator

On every same subset reconstruct exact selected recurrent-EOM HDBSCAN v1 unchanged:

- exact GEO6;
- `min_cluster_size=10`;
- `min_samples=10`;
- Euclidean metric;
- exact annual-normalized recurrent-EOM stability;
- exact FOSC/EOM extraction.

No truth is opened.

## 7. Cross-scale membership metric

For each bucket and each method separately:

1. let `F` be eligible memberships on denominator 1024;
2. let `C` be eligible memberships on denominator 128;
3. restrict each coarse membership to the fine event universe and discard restricted sets with fewer than four events;
4. for each fine membership `f`, compute its best Jaccard similarity to any retained restricted coarse membership;
5. record:
   - **candidate-unweighted mean** best Jaccard;
   - median best Jaccard;
   - exact restricted-match fraction;
   - candidate counts.

Candidate-unweighted mean is primary so a single broad modal basin cannot dominate the result by event count.

## 8. Non-collapse condition

For every fine denominator-1024 subset, the number of eligible modal basins must be **at least** the number of exact recurrent-EOM candidates on that same subset.

This is a relative structural condition, not a fitted numerical threshold. A method with fewer candidate regions than the already-coarse recurrent-EOM baseline cannot plausibly solve the small-survey resolution problem.

## 9. Frozen interpretation gate

Return

`SUPPORTS_PHYSICAL_MODAL_BASIN_CROSS_SCALE_COHERENCE`

iff all of the following hold:

1. modal clustering produces at least one eligible basin in all eight subsets;
2. the non-collapse condition holds in all four fine subsets;
3. pooled candidate-unweighted mean best Jaccard across the four nested pairs is strictly greater for modal basins than recurrent-EOM;
4. median of the four bucket-level candidate-unweighted mean best Jaccards is strictly greater for modal basins than recurrent-EOM; and
5. modal basins have a strictly greater bucket-level candidate-unweighted mean best Jaccard in at least three of four buckets.

Otherwise return

`REFUTES_PHYSICAL_MODAL_BASIN_CROSS_SCALE_COHERENCE`.

There is no mixed verdict and no post-result rescue.

## 10. Consequence

A positive result establishes only that fixed-physical-scale modal basins are structurally more stable than recurrent-EOM under the exact sparse-sampling stress. It would authorize one separately frozen follow-up that adds statistically justified mode significance/recurrence before any shower truth.

A negative result closes this exact inherited-scale MeanShift modal-basin architecture. It may not be rescued using a different bandwidth, solar/radiant/speed scale, empirical rescaling, seed rule, center-merging rule, kernel, minimum basin size, subset, salt, or gate after seeing the result.
