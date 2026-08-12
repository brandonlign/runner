# OrbitTrace GMN local-background trajectory contrast v1

## Scientific role

This is a new target-excluded GMN mechanism diagnostic after the predictive-consistency transfer family was closed in PR #1220. It is **not** another predictive rank-fusion rescue.

The previous experiments established that candidate self-predictability can be informative in a restricted hard-family ranking problem but does not transport to the active 4,504-candidate objective. The unresolved scientific distinction is whether a candidate's coherent trajectory is actually unusual relative to the surrounding meteor background. That local-background contrast is the mechanism tested here.

SonotaCo 2013/2014 is inaccessible during this diagnostic. No OrbitTrace target information, protected target-region events, MAARSY, or DMS access is authorized. The first technically valid result is binding.

## Immutable candidate universe and baseline

Use exact frozen GMN 2022/2023 artifacts:

- hard = 226 families
- P19 = 1075 families
- P20 = 3203 families
- union = 4504 families

Candidate generation and memberships are immutable.

The baseline is the exact active #839 34-feature grouped five-fold OOF quality/diversity order with diversity lambda `0.8`, scale `1.0`, and the exact existing tie rule. It must reproduce:

- recovered@25 = 22
- recovered@50 = 40
- recovered@100 = 75
- recovered@500 = 159
- qualified matches = 256
- top-100 dominant precision = 0.7645689180574315
- MRR = 0.019037817654898162

## Physical candidate trajectory

For every candidate and each year separately, use only accessible observables: solar longitude, solar-centered radiant longitude, ecliptic latitude, and positive geocentric speed.

The candidate's internal tube radius is the exact already-frozen leave-one-out predictive q90 rule from source blob `25d91e92c41f83416ad87766c2d96884c30b714c`:

- if annual membership >=4, leave one member out, fit ordinary least squares on the remaining members with design `[1, signed_delta_solar_longitude / 10 deg]` and response `[radiant unit-vector x,y,z, log(vg)]`, normalize the predicted radiant, and score the held-out event as `hypot(radiant_angle / 3 deg, abs(delta_log_vg) / log(1.08))`;
- if annual membership <4, use the static annual centroid residual as the predictive residual;
- annual tube radius = q90 of those member predictive residuals.

This internal q90 is **not itself the ranking signal** in this experiment. It only defines each candidate's own empirical trajectory tube.

## Local nonmember background

For each candidate-year:

1. Partition accessible GMN events by exact 2-degree solar-longitude stratum `floor((sol mod 360) / 2)`.
2. The local background pool is the union of strata containing that candidate's annual members.
3. Exclude every event belonging to that candidate family from its own background pool.
4. Fit one deterministic full-member annual affine trajectory model using the same design and response as above. If annual membership has fewer than two events, use the static annual unit-radiant/log-speed centroid model.
5. Evaluate every local-background event against that full-member candidate model with the exact same physical residual.
6. Define annual **background intrusion fraction** as the fraction of local nonmember events whose residual is less than or equal to that candidate-year's internally determined predictive q90 tube radius.

This fraction requires no tuned background-distance cutoff: the candidate's own held-out residual distribution defines the tube. The 2-degree stratum is frozen before outcome and no alternate stratum width is evaluated.

## Candidate background-contrast order

For every candidate compute:

- worst-year intrusion fraction = max of annual intrusion fractions;
- mean annual intrusion fraction;
- worst-year internal predictive q90.

The sole background-contrast order is:

`(lower worst-year intrusion fraction, lower mean intrusion fraction, lower worst-year predictive q90, family_id)`.

No source-class exception, threshold, candidate deletion, orbital element, fitted weight, density-tree quantity, HDBSCAN cluster score, or alternate background statistic is permitted.

## Frozen fusion

Convert the exact active #839 baseline order and the complete background-contrast order to 1-based ranks over the same 4,504-family universe. The sole successor is equal rank-sum:

`(baseline_rank + background_contrast_rank, baseline_rank, family_id)`.

No coefficient or alternate fusion is evaluated.

## Binding PASS gate

PASS requires all five:

- fused recovered@100 strictly greater than 75;
- fused recovered@50 >= 40;
- fused recovered@25 >= 22;
- fused top-100 dominant precision >= 0.7645689180574315;
- fused MRR >= 0.019037817654898162.

Otherwise verdict is FAIL and this exact local-background contrast rule is permanently closed. No post-result rescue by changing bin width, background pool definition, q90 tube radius, fit degree, residual scale, fusion weight, source class, rank window, or budget is authorized.

## Claim boundary

A PASS is target-excluded GMN development evidence only. It does not establish HDBSCAN literature superiority. Only after a PASS could a separately frozen SonotaCo/v31 transfer be considered, before any new SonotaCo benchmark view.

## Firewall

- protected solar longitude 20°–55° remains excluded before all event indexing and scoring;
- SonotaCo 2013/2014 access = false;
- OrbitTrace target information access = false;
- target-region events accessed = false;
- MAARSY scientific access = false;
- DMS scientific access = false.
