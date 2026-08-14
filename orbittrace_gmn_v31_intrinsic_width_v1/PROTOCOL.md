# OrbitTrace GMN v31 intrinsic-width successor v1 — frozen protocol

Status: **FROZEN BEFORE FIRST SCIENTIFIC OUTCOME**.

This is a target-excluded GMN 2022/2023 development successor to exact v31. It does not access SonotaCo 2013/2014, OrbitTrace target information/events, the protected solar-longitude interval 20°–55°, MAARSY, or DMS. A valid result is development evidence only.

## Scientific motivation

Exact v31 already encodes candidate geometry/cohesion but does not contain event-level measurement uncertainty. GMN publishes Monte-Carlo radiant and velocity uncertainty estimates. Moorhead, Clements & Vida, *Meteor shower radiant dispersions in Global Meteor Network data* (MNRAS 2021/2022 publication lineage) explicitly treats formal radiant errors as a systematic broadening of measured shower dispersion and estimates the physical dispersion after accounting for that broadening. Vida et al., *Global Meteor Network — Methodology and first results*, documents the trajectory uncertainty estimates and their relevance to measuring physical shower dispersion.

The hypothesis is therefore not that low-uncertainty observations are intrinsically better candidates. The hypothesis is that, after removing annual radiant/velocity drift and subtracting the expected contribution of the reported measurement noise, a real recurrent stream should have a smaller **intrinsic physical width** than a spurious/fragmentary family with the same apparent observed compactness.

This mechanism is distinct from:

- PR #57/#61 uncertainty-inflated quartet detection/calibration: those altered event-pair distances during sparse-subset discovery; this successor leaves every v31 candidate and membership byte unchanged and uses uncertainty only to estimate the intrinsic width of the already-fixed family;
- PR #1236 directional morphology recurrence: this uses total residual variance after measurement-noise subtraction, not a trace-normalized tensor shape discrepancy;
- PR #1237 phase–geometry drift recurrence: drift is fitted only as a nuisance trend and discarded; its cross-year slope agreement is never scored;
- the closed radial/activity-profile, energy-distance, graph/topology, local-background, and fusion/rescue lanes.

No threshold, feature grid, uncertainty multiplier, covariance fit, clipping constant, alternate annual combiner, metric, k, diversity setting, or fusion weight will be searched.

## Authorizing zero-endpoint uncertainty audit

The only new data channel is the already-completed fixed-member uncertainty enrichment audit:

- workflow run: `31812584375`;
- artifact: `9223741916`;
- artifact digest: `sha256:ee56911a802d7acacfde6241954154b957919d60334a4bfe3959fff3459effcb`;
- enriched fixed-member gzip SHA-256: `01de5502aab911fa251656cd7a71ab4b6ef6158abf3a675495c4ba4d1c349622`;
- exact fixed v31 member rows: 8,794 = 4,726 (2022) + 4,068 (2023);
- exact source months: 24;
- mandatory fields on every fixed member: RA, Dec, Vg and nonnegative finite RA/Dec/Vg formal uncertainties;
- optional quality metadata (`Qc`, `fiterr`, `num_stat`) is not used by this successor;
- zero scientific endpoint, candidate ranking, truth metric, SonotaCo, target, MAARSY or DMS access occurred in the audit.

The fixed 226-family universe has at least four members in each annual recurrence (observed feasibility minimum: 4 in 2022 and 5 in 2023), so no applicability threshold, family deletion, or imputation rule is needed.

## Immutable parent

Reproduce exact target-excluded GMN v31 first. Preserve without change:

- 226 hard families and every event membership from immutable P19 prelabel SHA-256 `276129ef8f9f31a1f8e7b1570c15f5e67ed1a7274f293f5da65bab60f86e32b8`;
- exact parent 23-dimensional v31 representation;
- exact strict five-fold whole-shower OOF assignment and annual truth construction;
- fold-training z-score;
- ordinary Euclidean distance;
- k = 1 nearest annual-positive and annual-nonpositive reference families;
- annual margin `d_nonpositive - d_positive` and exact v31 annual `min` combiner;
- exact #839 diversity `lambda=0.8`, scale `1.0`;
- exact hard-order equal-rank fusion and deterministic tie rules;
- identical fixed development metrics/gates.

Parent controls must reproduce exactly before the successor is evaluated:

- recovery@25 = 23;
- recovery@50 = 41;
- recovery@100 = 66;
- top-100 dominant precision = `0.7229521515453452`;
- MRR = `0.050244164168646674`;
- qualified matches = 95.

## Sole new coordinate

For each fixed family `f` and year `y in {2022, 2023}`, use the exact annual v31 centroid `c_y` and its fixed member IDs. For member `i`, define the same physical residual coordinates used in the recent v31 physical diagnostics:

- `r1_i = signed_delta(sun_lon_i, c_y.sun_lon) / 4 degrees`;
- `r2_i = (ecl_lat_i - c_y.ecl_lat) / 4 degrees`;
- `r3_i = log(Vg_i / c_y.Vg) / log(1.10)`.

Define activity phase only as a nuisance regressor:

`p_i = signed_delta(sol_i, c_y.sol)`.

Fit ordinary unweighted least squares independently to all three columns of `r_i` using the fixed design matrix `[1, p_i]`. Let `H` be that design matrix's ordinary hat matrix, `h_i = H_ii`, `R` the `n x 3` residual matrix, and `df = n - 2`.

The observed drift-adjusted residual variance trace is:

`V_obs = ||R||_F^2 / df`.

For the same event, define the dimensionless formal measurement-noise trace

`q_i = ((sigma_RA,i * cos(dec_i)) / 4 degrees)^2 + (sigma_Dec,i / 4 degrees)^2 + ((sigma_Vg,i / Vg_i) / log(1.10))^2`.

The first two terms are the local orthonormal radiant-tangent-plane variance trace expressed in the inherited 4-degree scale. The covariance trace is rotation invariant, so no unreported RA/Dec covariance is invented when comparing the equatorial formal uncertainties with the locally rotated radiant residual coordinates. The speed term uses first-order propagation through the fixed log-speed coordinate.

The expected contribution of measurement noise to the OLS residual variance trace is

`V_noise = sum_i ((1 - h_i) * q_i) / df`.

The annual intrinsic variance and width are fixed as

`V_int,y = max(0, V_obs - V_noise)`

and

`W_y = sqrt(V_int,y)`.

The **only new v31 coordinate** is

`W = max(W_2022, W_2023)`.

The `max` is fixed prospectively because a recurrent family must remain intrinsically narrow in both years; it is the width analogue of v31's conservative worst-year logic. No mean/min/geometric mean, annual weighting, radiant-only, speed-only, eigenvalue, determinant, robust/MAD, quantile, uncertainty multiplier, alternative drift order, or uncorrected-width alternative may be tried after the result.

Append exactly this scalar to the exact 23D parent representation, producing exactly 24 dimensions. It then enters the unchanged fold-training z-score and exact v31 k=1 geometry. No direct reward for small `W`, threshold on `W`, or separate reranker is allowed.

## Fixed quality-only ablation

For interpretation only, compute one preregistered non-promotion ablation using the same annual OLS leverages but **measurement noise alone**:

`Q_y = sqrt(sum_i ((1 - h_i) * q_i) / df)` and `Q = max(Q_2022, Q_2023)`.

Append `Q` alone to the exact 23D parent and report its otherwise-identical OOF metrics. This ablation cannot be selected, fused, or promoted regardless of its result. It exists only to distinguish an intrinsic-width effect from a generic low-measurement-error preference. The candidate scientific verdict is determined solely by the intrinsic-width gates below; the ablation does not alter those gates.

## Binding continuation gates

The first technically valid outcome is binding. `PASS_GMN_V31_INTRINSIC_WIDTH_V1` requires **all** of:

1. recovery@100 strictly greater than parent: `> 66`;
2. recovery@50 not below parent: `>= 41`;
3. recovery@25 not below parent: `>= 23`;
4. top-100 dominant precision not below `0.7229521515453452`;
5. MRR not below `0.050244164168646674`;
6. qualified matches exactly 95;
7. all 226 families have finite annual widths from their exact fixed members;
8. all 8,794 enriched member IDs are used only through their already-fixed family memberships and no nonmember uncertainty row enters the calculation;
9. protected-data/firewall checks remain clean.

Any failed gate yields `FAIL_GMN_V31_INTRINSIC_WIDTH_V1` and permanently closes this exact formulation. A failure does not authorize radiant-only/speed-only widths, alternate drift models, alternate variance estimators, different uncertainty propagation, alternate annual combiners, feature weighting, transforms, thresholds, metric/k/scaling changes, diversity/fusion changes, or result-conditioned family handling.

A complete PASS would authorize only a separately frozen compatibility/transfer stage. It would not by itself establish literature superiority or authorize target-region, MAARSY, or DMS access.

## Firewall

At all stages:

- solar longitude 20°–55° remains inaccessible;
- OrbitTrace target information/events remain inaccessible;
- SonotaCo 2013/2014 is not accessed by this GMN development run;
- MAARSY and DMS are not accessed scientifically;
- no outcome may be used to alter this protocol.
