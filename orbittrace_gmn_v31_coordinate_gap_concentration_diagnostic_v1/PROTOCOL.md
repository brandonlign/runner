# OrbitTrace GMN v31 coordinate-gap concentration diagnostic v1

## Role

GMN 2022+2023 target-excluded **parent diagnostic only**. It creates no successor score/rank and authorizes no SonotaCo access.

Frozen prior diagnostics establish that the dominant exact-v31 top-100 failure is constituent/representation overlap: 21 of 29 fused misses are outside both parent constituents, all 21 have no positive-side v31 representative, and 17/21 have multiple nonpositive references ahead of their best nearest positive.

This diagnostic asks one narrower question before any new representation architecture is proposed:

> Is the wrong-side nearest-positive-versus-nearest-nonpositive geometry for those hard misses driven by a small number of coordinates, or is the distance disadvantage distributed across many of the frozen 23 coordinates?

The diagnostic is frozen before first output. It never removes, weights, transforms, names as a candidate, or ranks features.

## Authoritative package and exact parent reproduction

Use only offline package run `31663453082`, artifact `9167087908`, digest `sha256:e8b019d84002e182d31399eb96cccbd96d47c3e4411ba7053b93ee2954f259e6`.

Require:

- manifest SHA-256 `16fb5ef3cd8dbbb3873e9bc23874fe7da3db68498772a5e992fbceed6cb980d7`;
- feature SHA-256 `fea3b063772c75b675e37a227b53a4aa3c5b86fdcbfcef1487b1e1448689cdf5`;
- centroid SHA-256 `a53b9862f1ec3d751745f80aec2625d7904128474c9263c55ea953cf60d0621f`;
- parent raw OOF margin SHA-256 `f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`;
- exact hard metrics @25/@50/@100 `21/38/59`, precision `0.6884631112636006`, MRR `0.046734076055452344`, qualified `95`;
- exact fused metrics @25/@50/@100 `23/41/66`, precision `0.7229521515453452`, MRR `0.050244164168646674`, qualified `95`.

Recompute exact five-fold strict-whole-shower parent geometry with fold-training mean/population-SD z-scaling, Euclidean distance, exact positive/nonpositive semantics, exact diversity `lambda=0.8, scale=1.0`, and equal hard/local rank fusion.

Any mismatch fails before diagnosis.

## Exact coordinate contribution identity

For every held-out positive family `z`, select the exact parent nearest positive `p*` and nearest nonpositive `n*` using deterministic `(Euclidean distance, immutable hard rank, family ID)` ordering.

For standardized coordinate `j`, define

`g_j(z) = (z_j - n*_j)^2 - (z_j - p*_j)^2`.

Then require numerically that

`sum_j g_j = d_neg^2 - d_pos^2 = (d_neg-d_pos)(d_neg+d_pos)`.

Because `d_neg+d_pos > 0`, `sum_j g_j` has the same sign as the exact parent raw margin. Thus:

- `g_j > 0` is a coordinate contribution favoring the positive reference;
- `g_j < 0` is a coordinate contribution favoring the nonpositive reference.

For any family with negative total gap, define nonpositive-favoring magnitudes

`c_j = max(-g_j,0)`.

Require `sum c_j > 0`.

No coordinate identity is used to choose or modify a method.

## Frozen concentration statistics

For each negative-margin positive family, compute only:

- `top1_negative_share = max(c_j)/sum(c_j)`;
- `top3_negative_share = sum(3 largest c_j)/sum(c_j)`;
- `top5_negative_share = sum(5 largest c_j)/sum(c_j)`;
- `negative_effective_dimension = (sum c_j)^2 / sum(c_j^2)`;
- `negative_contributor_count = count(c_j > 0)`.

The effective dimension is the inverse Herfindahl concentration of nonpositive-favoring contribution mass. No cutoff on these values is used to score, filter, or select anything.

## Exact label subsets

For each qualified label, choose its **best parent-margin positive representative**: maximal exact raw v31 margin; ties break by immutable hard rank then family ID. This is descriptive and cannot define a future rank.

At top 100 require exact reproduction of:

- 29 fused-missed qualified labels;
- 25 fused-missed labels with no positive-side representative;
- 21 constituent-absent/sign-rejected labels (`hard rank >100`, `local rank >100`, no positive-side representative).

For the exact 21-label subset, require every chosen best representative to have negative margin.

## Sole summaries

For the exact 21 constituent-absent/sign-rejected labels, report for each of the five concentration statistics:

- min;
- 25th percentile;
- median;
- 75th percentile;
- max.

Report the same summaries for the exact 25 no-positive-support top-100 misses and all 29 top-100 misses whose chosen best representative has negative margin.

Also report only these aggregate count summaries for the 21-label subset:

- number with negative contributor count `<=5`;
- number with negative contributor count `6..11`;
- number with negative contributor count `>=12`.

These bins are descriptive breadth bins only and are not an outcome gate or authorization for a feature subset.

## Interpretation boundary

No PASS/FAIL successor conclusion is permitted. The allowed interpretation is only whether the preserved distance disadvantage appears concentrated or distributed at the family level, based on the preregistered descriptive statistics.

This diagnostic may **not** be used to identify a feature for deletion, downweighting, clipping, transformation, or tuning. A future representation successor requires independent methodological motivation and freezing before outcome.

## No-search rules

No new rank, score, threshold, feature subset, feature identity selection, block selection, transform, metric, scaling, k, reference editing, diversity variant, fusion variant, source/year subgroup, or post-result second diagnostic is evaluated.

## Firewall

Protected solar longitude 20°–55° remains inaccessible. No OrbitTrace target information/events, SonotaCo 2013/2014, MAARSY, DMS, raw GMN event rows, raw event IDs, or raw hidden event-label mapping are accessed.