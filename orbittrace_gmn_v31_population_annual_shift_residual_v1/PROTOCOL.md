# v31 population annual-shift residual v1

**PRE-OUTCOME FREEZE.** Exact parent: frozen v31 GMN offline package, 226 hard families. Parent fused controls: @25=23, @50=41, @100=66, precision=0.7229521515453452, MRR=0.050244164168646674, qualified=95.

## Sole change
Append one feature to exact v31 23D X. From each frozen annual centroid block `[sol,sun_lon,ecl_lat,log(vg)]`, use the exact active centroid embedding for one year:
`[18 cos(sol),18 sin(sol),45 cos(sun_lon),45 sin(sun_lon),ecl_lat/4,log(vg)/log(1.10)]` with angles in radians.
For family i let `d_i = E_i,2023 - E_i,2022`. Let `mu_-i` be the ordinary mean of `d_j` over the other 225 families. Append exactly `r_i = ||d_i-mu_-i||_2`.

This is label-free population calibration of annual centroid displacement. No raw-event access, threshold, fitted hyperparameter, alternate population center, or external scientific outcome is used.

## Inherited architecture
Exact v31 folds, fold-training z-score, Euclidean k=1 nearest positive/nonpositive margin, diversity lambda=0.8 scale=1.0, hard-order ties, equal rank-sum with immutable P19 hard order, evaluator, candidate universe and memberships are unchanged. Exact parent hashes/metrics must reproduce before the candidate is valid.

## Binding gate
First technically valid outcome is binding. PASS requires @100>66, @25>=23, @50>=41, precision>=0.7229521515453452, MRR>=0.050244164168646674, qualified=95, and all provenance/firewall checks.

FAIL closes this exact mechanism. No median/trimmed/weighted/source-conditioned population center, in-sample centering, alternate embedding/scales/norm, companion raw displacement, k/fold/scaling/reference/diversity/fusion/weight/budget rescue, or identity-specific correction.

Protected 20-55 remains excluded. SonotaCo 2013/2014, OrbitTrace target information/events, MAARSY and DMS are not accessed. Scientific role: target-excluded GMN 2022/2023 v31 successor development only.