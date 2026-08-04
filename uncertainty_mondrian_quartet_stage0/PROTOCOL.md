# Uncertainty-inflated exact quartet with fixed 10° Mondrian calibration

Status: frozen before any score from this composition is computed.

## Scientific question

Can event-level radiant/speed uncertainty preserve the sparse strict-tail gains seen in PR #57 while the independently validated globally anchored 10° Mondrian calibration removes the coarse-sector false-positive instability?

This is a distinct composition candidate. It does not rescue or relabel PR #57, which remains killed under its fixed 60° calibration and source-encoded gates. It also does not alter PR #38 or the killed July confirmation.

## Development and confirmation boundary

- Development data: exact PR #14 GMN 2019, 2021, 2023, and 2025 selected-event artifact.
- Retired data excluded from this run: 2020, 2022, 2024, and all 2026 panels.
- GhostStream is excluded before every reservoir, support check, window, score, fold, and endpoint by removing solar longitude 20.0°–55.0° inclusive.
- A complete development pass authorizes only a prospectively frozen August 2026 GMN confirmation after an adequate fixed snapshot exists. It does not authorize GhostStream, a catalogue scan, or a discovery claim.

## Exact input and episode construction

- selected-event artifact from runner workflow `30855193522`;
- selected-event SHA-256 `63e1389e2666d10b05138044f428609266b367cabab2542295c154a510e40f01`;
- audit SHA-256 `f8ba2446dce96d69652727092189903c40493e2fe741eb746f7fb5181edea778`;
- preserve the PR #14 parser, quality filters, MDC complex/parent grouping, and eligible-shower definition;
- 128 events per window from one year and a ±10° solar-longitude neighborhood;
- positives contain `k in {4,6,8,12}` real members from one eligible shower plus local real IAU `-1` meteors;
- two deterministic positive replicates per shower/member count;
- calibration and audit windows contain only local real IAU `-1` meteors.

## Frozen physical geometry

Observed pairwise distance uses the unchanged four-dimensional space:

- relative solar longitude / 2°;
- Sun-centered ecliptic radiant longitude / 2°;
- Sun-centered ecliptic radiant latitude / 2°;
- geocentric speed / 2 km/s.

For event `i`, normalized reported measurement variance is

`q_i = ((sigma_RA,i cos(dec_i))/2°)^2 + (sigma_Dec,i/2°)^2 + (sigma_Vg,i/2 km/s)^2`.

The uncertainty-inflated pairwise distance is

`D_u(i,j) = sqrt(D_obs(i,j)^2 + q_i + q_j)`.

No uncertainty multiplier, covariance fit, orbit, shower identity, absolute date, or absolute solar longitude enters the score.

## Frozen candidate statistic

Compute the exact minimum complete-link diameter among all four-event cliques under `D_u` by adding pairwise edges in increasing distance order until the first complete four-clique appears. Negate that diameter so larger values indicate stronger sparse coherence.

The uncertainty formula and exact-clique implementation are unchanged from PR #57.

## Fixed 10° Mondrian calibration

Replace only PR #57's 60° calibration strata with globally anchored 10° strata:

`[0°,10°), [10°,20°), ..., [350°,360°)`.

For every supported year-bin:

- require at least 20 retained sporadic anchor events;
- test 20 deterministic anchor probes and require at least 10 to have a feasible 128-event ±10° neighborhood;
- draw 256 deterministic same-corpus calibration windows;
- draw 64 independent deterministic audit windows;
- compute conservative rank p-values `(1 + count(calibration score >= test score)) / 257`.

Unsupported bins are not shifted, merged, widened, or borrowed from adjacent years. At least 20 supported 10° bins are required independently in every development year.

False-positive robustness is judged in fixed 60° reporting sectors aggregated from the 10° calibrated bins. The worst individual 10°-bin FPR is diagnostic only because 64 audit windows per bin make its maximum intrinsically noisy.

Frozen seed prefixes:

- `uncertainty-mondrian-calibration`;
- `uncertainty-mondrian-audit`;
- `uncertainty-mondrian-positive`;
- `uncertainty-mondrian-lcc`.

## Fixed comparators and ablation

On identical windows compute:

- quality-only score from the four smallest `sqrt(q_i)` values;
- uninflated exact K4 diameter;
- anchored nearest-neighbor quartet diameter;
- unchanged eight-split LCC;
- radius-2.5 local density;
- epsilon-2.5 connected-component/DBSCAN analogue;
- five deterministic event-count-balanced folds of complete MDC complex/parent units.

The quality-only ablation must remain non-predictive, and the candidate must preserve a measurable advantage over the uninflated quartet rather than succeeding only because of Mondrian calibration.

## Frozen continuation gates

Every gate must pass:

1. pooled candidate FPR at `p <= 0.05` is at most 0.060;
2. pooled candidate FPR at `p <= 0.01` is at most 0.020;
3. every development year has at least 20 supported 10° bins;
4. at least 3,000 weak positive windows are evaluated;
5. worst year-by-60° reporting-sector FPR at `p <= 0.05` is at most 0.120;
6. candidate weak AUROC is at least 0.80;
7. candidate AUROC beats density and DBSCAN;
8. quality-only AUROC is at most 0.65 and candidate gain over quality is at least 0.10;
9. candidate AUROC is no more than 0.005 below LCC;
10. candidate AUROC is not below uninflated exact K4 or anchored quartet AUROC;
11. at least four of five candidate fold AUROCs are at least 0.75 and none is below 0.70;
12. candidate k=4 recall is at least 0.17 at 0.05 and 0.05 at 0.01;
13. candidate k=4 recall at 0.05 exceeds LCC by at least 0.01;
14. candidate k=4 recall at 0.01 exceeds uninflated exact K4 by at least 0.005;
15. candidate k=6 recall is at least 0.30 at 0.05 and 0.15 at 0.01;
16. candidate k=8 recall is at least 0.45 at 0.05 and 0.25 at 0.01;
17. k=6 and k=8 recall at 0.05 remain within 0.04 of LCC;
18. k=6 and k=8 recall at 0.01 are not below uninflated exact K4;
19. recall is nondecreasing from k=4 to 6 to 8 to 12 at both thresholds.

## Kill rule

Any failed gate kills this exact composition. Do not change the uncertainty equation, bin width, support rule, calibration/audit counts, seeds, clique size, feature scales, comparator parameters, fold assignment, blind interval, thresholds, or endpoints after the result.

A complete pass yields `PROCEED_TO_PROSPECTIVE_AUGUST_2026_CONFIRMATION`. A failure yields `KILL_UNCERTAINTY_MONDRIAN_QUARTET`.

Exact candidate source SHA-256: `7aad1aadd9ae3674abd9c175ae141982ab4463d7e63520fed9660fbfcc12b9c6`.
