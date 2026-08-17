# OrbitTrace v40 component-minimum multiplicity calibration diagnostic v1

## Scientific role

Post-result exposed-SonotaCo diagnostic only after binding v40 (#1079) failed 2/4.

v40 used the minimum normalized exact-v31 rank percentile among all Sugar/HDB members of each frozen #1072 connected component as component evidence. It substantially improved HDB 2013 but remained broad (105/229 HDB candidates moved upward) and damaged HDB 2014. A structural concern is inherent in the v40 statistic: taking a minimum over more component members creates a best-of-many advantage even when the member percentiles contain no stronger underlying evidence.

This diagnostic tests that multiplicity-bias mechanism and one canonical parameter-free calibration. It evaluates **no new candidate order, selector, replacement, literature panel, or successor**.

## Frozen inputs

Before truth, reproduce exactly:

- immutable #950 Sugar/HDB payload;
- #1064 cross-route radius-1 graph: 267 Sugar, 229 HDB, 2,334 edges, serialized SHA-256 `2f25aa7d9af1df0a350c034b2280a790c3869a7775bf6d7063d0d1e4cc802b25`;
- #1072 connected-component identity: 196 components, 113 non-singletons, 83 singletons, serialized SHA-256 `c1b80484502907ad19e0d51d8d48d364f3bf7a27e17576e073fe86ae44f499cd`.

After truth is loaded, reproduce the four exact v31 parent controls and the exact v40 total-order SHA-256 values:

- Sugar v40 order: `1dc01938a8cb83622ce023b516162be524e0812aa4b0a886c23267c0881aee2c`;
- HDB v40 order: `c6d29171c410f731a30f6eacba5bfe8de05c8cddf17d7bcbfd4dabb867fd7899`.

Any mismatch is an engineering/provenance failure and yields no diagnostic result.

## Frozen component statistics

Let `rank_r(i)` be the one-indexed exact-v31 fused rank of candidate `i` on route `r`, and `N_r` the route candidate count. Define

`p_r(i) = (rank_r(i)-1)/(N_r-1)`.

For frozen component `C`, define the exact v40 raw evidence

`p_min(C) = min p_r(i)`

over all Sugar/HDB members of `C`, and let

`m(C) = number of members of C`.

The diagnostic additionally defines exactly one canonical minimum-order-statistic calibration

`q(C) = 1 - (1 - p_min(C)) ** m(C)`.

This is the probability-integral transform for the minimum of `m` independent Uniform(0,1) draws. It has no learned coefficient, threshold, exponent, route weighting, or component-size cutoff. The independence model is not asserted to be physically exact; the diagnostic asks only whether this canonical transform materially reduces the empirical component-size dependence created by the raw minimum statistic.

For every component report `m`, `p_min`, `q`, best Sugar percentile/rank if present, best HDB percentile/rank if present, and whether the component has each route.

## Predeclared diagnostic test

Use ordinary Spearman rank correlation between `m(C)` and the evidence statistic across three fixed component universes:

1. all 196 components;
2. all components containing at least one Sugar candidate;
3. all components containing at least one HDB candidate.

For each universe record

- `rho_raw = Spearman(m, p_min)`;
- `rho_calibrated = Spearman(m, q)`.

Because smaller evidence is better, multiplicity bias predicts `rho_raw < 0`: larger components look artificially better under a minimum. The canonical calibration direction is considered supported only if, in **all three fixed universes**:

1. `rho_raw < 0`; and
2. `abs(rho_calibrated) < abs(rho_raw)`.

No significance cutoff or effect-size threshold is selected.

## Descriptive v40 post-result localization only

Without changing the predeclared gate, also report for each HDB literature budget/year:

- exact v31 prefix families;
- exact v40 prefix families;
- entrants newly promoted by v40;
- each entrant's component size, `p_min`, and `q`;
- after truth, whether each entrant is individually annual-recoverable (`F1_y > 0.5`).

These rows are descriptive only. They cannot change the correlation gate and no entrant identity may enter a future deployable rule.

## Interpretation boundary

If the predeclared correlation gate passes, it justifies separately freezing at most one successor that replaces v40's raw component-minimum evidence with the exact canonical `q(C)` calibration while otherwise requiring a separately stated total-order rule. This diagnostic itself does not select or evaluate that successor.

If the gate fails, minimum-order-statistic multiplicity calibration is not justified from this diagnostic and must not be rescued by tuned exponents, pseudocounts, effective component sizes, route-specific member counts, clipping, thresholds, or component-size bins.

## Explicit non-search commitments

No new candidate order, component order, panel evaluation, component-size threshold, effective-size fit, exponent/coefficient/pseudocount, route-specific calibration, feature/model/k/scaling/annual-combiner/diversity/fusion/source-quota change, oracle identity rule, or post-result second search is evaluated.

## Firewall

- SonotaCo 2013/2014 is `EXPOSED_DEVELOPMENT_ONLY`.
- Protected OrbitTrace solar longitude `20°–55°` remains inaccessible.
- No OrbitTrace target information or target-region events may be accessed.
- No MAARSY or DMS scientific access is authorized.
- Candidate generation and memberships remain unchanged.
