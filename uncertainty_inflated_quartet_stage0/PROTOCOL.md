# Uncertainty-inflated exact-quartet coherence: frozen development screen

Status: frozen runner reproduction of a development-only formulation. It uses GMN 2019, 2021, 2023, and 2025 from the exact PR #14 artifact. No 2020/2022/2024 or 2026 event, label, score, or endpoint is read.

## Scientific question

Can reported event-level radiant and speed uncertainties improve partition-invariant sparse-subset discovery by penalizing apparent four-event coherence that is not precise relative to its measurement error?

## Fixed feature geometry

Preserve the successful physical space:

- relative solar longitude / 2 degrees;
- Sun-centered ecliptic radiant longitude / 2 degrees;
- Sun-centered ecliptic radiant latitude / 2 degrees;
- geocentric speed / 2 km/s.

No orbit, shower identity, absolute date, or absolute solar longitude enters the candidate statistic.

## Candidate statistic

For each event `i`, define normalized reported measurement variance

`q_i = ((sigma_RA,i cos(dec_i))/2 degrees)^2 + (sigma_Dec,i/2 degrees)^2 + (sigma_Vg,i/2 km/s)^2`.

For every pair, inflate the observed squared physical distance by independent reported error:

`D_u(i,j) = sqrt(D_obs(i,j)^2 + q_i + q_j)`.

The window score is the negative exact minimum diameter among every four-event clique under `D_u`. The exact K4 search is partition invariant and is computed by adding pairwise edges in increasing distance order until the first complete four-clique exists.

## Mandatory quality-proxy ablation

Compute a quality-only score from the four smallest `sqrt(q_i)` values in each window. The candidate may continue only if this ablation has weak AUROC at most 0.65 and the physical candidate exceeds it by at least 0.10. This prevents a result driven merely by established-shower labels having smaller reported uncertainties.

## Frozen benchmark

- remove solar longitude 20 degrees through 55 degrees before all pools, windows, scores, folds, and endpoints;
- 128-event windows drawn from one year and a plus-or-minus 10-degree local neighborhood;
- same-corpus empirical calibration within year and fixed 60-degree sector;
- 256 calibration and 64 independent audit windows per sector;
- two deterministic positive replicates for `k in {4,6,8,12}`;
- comparators: uninflated exact K4, PR #32 anchored quartet diameter, unchanged PR #31 LCC, radius-2.5 local density, and epsilon-2.5 connected-component/DBSCAN analogue;
- five deterministic event-count-balanced folds of complete MDC complex/parent units.

## Frozen continuation gates

Every source-encoded gate must pass:

1. pooled FPR at 0.05 at most 0.060;
2. pooled FPR at 0.01 at most 0.020;
3. worst year-sector FPR at 0.05 at most 0.120;
4. weak AUROC at least 0.80;
5. beat fixed density and DBSCAN comparators;
6. quality-only AUROC at most 0.65 and candidate gain over quality at least 0.10;
7. candidate AUROC no more than 0.01 below LCC;
8. at least four of five folds at least 0.75 and no fold below 0.70;
9. k=4 recall at least 0.17 at p <=0.05 and 0.05 at p <=0.01;
10. k=4 recall at p <=0.05 exceeds LCC by at least 0.01;
11. k=6 and k=8 recall at p <=0.05 remain within 0.04 of LCC;
12. recall is nondecreasing through k=12 at both thresholds.

Any failed gate kills the exact formulation. No uncertainty formula, feature scale, clique size, calibration count, seed, threshold, comparator, fold, blind interval, or endpoint may change after the run.

Source SHA-256: `12cc8c9b0bcf674e918cca35bc572accd4b4139f0c16989d719df6857f6daf5b`.
