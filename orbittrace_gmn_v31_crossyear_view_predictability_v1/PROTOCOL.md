# v31 cross-year paired-view predictability v1

**PRE-OUTCOME FREEZE.** Exact parent: frozen v31 GMN offline package, 226 hard families. Exact P19 prelabel payload SHA-256 `276129ef8f9f31a1f8e7b1570c15f5e67ed1a7274f293f5da65bab60f86e32b8`. Parent fused controls: @25=23, @50=41, @100=66, precision=0.7229521515453452, MRR=0.050244164168646674, qualified=95.

## Independent mechanism
This is a self-supervised paired-year representation test, not a variant of the failed KS, centroid-width, population-mean-shift, or #1216 within-year event-trajectory predictive score. A recurrent family should have a 2022 annual state that predicts its 2023 annual state, and vice versa, under the population-wide relation learned from other families.

## Annual view
For each family/year use exactly 8 coordinates:
1-6. the exact active centroid embedding for that year: `[18 cos(sol),18 sin(sol),45 cos(sun_lon),45 sin(sun_lon),ecl_lat/4,log(vg)/log(1.10)]`;
7. `log1p(number of frozen family members in that year)`;
8. exact frozen `year_strengths[year]`.
No raw event values beyond year membership counts are read; no shower truth is used.

## Leave-one-family-out paired prediction
For held-out family i, use the other 225 family pairs only. Standardize the 2022 and 2023 annual views separately using ordinary training mean and population standard deviation; zero sd would map to 1.0 but the pre-outcome audit found none requiring a scientific fallback. Fit ordinary affine least squares from standardized 2022 view to standardized 2023 view using design `[1,Z2022]`, and separately the reverse map `[1,Z2023] -> Z2022`, via the unique full-rank least-squares solution.

The pre-outcome truth-free audit found every forward/reverse leave-one-out design rank exactly 9, maximum condition number <6.73, and every resulting prediction error finite/nondegenerate.

For i define `ef = ||Z2023_i - pred2023_i||_2`, `er = ||Z2022_i - pred2022_i||_2`. Append exactly one 24th v31 feature:

`paired_error_i = sqrt((ef^2 + er^2)/2)`.

## Inherited v31 architecture
Exact 23D X, 8D centroid matrix, hard order, five strict whole-shower folds, fold-training z-score, Euclidean k=1 positive/nonpositive margin, diversity lambda=0.8 scale=1.0, tie semantics, equal 1-based rank-sum with immutable P19 hard order, evaluator, universe and memberships remain unchanged. Exact parent hashes and metrics must reproduce before candidate scoring is valid.

## Binding gate
First technically valid outcome is binding. PASS requires @100>66, @25>=23, @50>=41, precision>=0.7229521515453452, MRR>=0.050244164168646674, qualified=95, plus all provenance/firewall checks.

FAIL closes this exact mechanism. No annual-view subset/addition, one-way score, alternate loss, ridge/PLS/CCA/nonlinear/neural map, source-conditioned map, weighting, robust regression, alternate standardization, k/fold/reference/diversity/fusion/budget rescue, or identity-specific correction.

Protected 20-55 remains excluded. SonotaCo 2013/2014, OrbitTrace target information/events, MAARSY and DMS are not accessed. Scientific role: target-excluded GMN 2022/2023 v31 successor development only.