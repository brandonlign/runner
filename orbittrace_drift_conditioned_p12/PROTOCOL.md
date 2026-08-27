# OrbitTrace P12 cross-year drift-conditioned two-view membership

Status: sole primary successor after authoritative P11 scientific no-go. This branch is source/protocol-only until its complete source/firewall audit passes. No target-containing search, comparator outcome, external scientific endpoint, or OrbitTrace target information is authorized.

## Pretruth provenance

The complete P12 architecture was preregistered in PR #667 comment `5230390070` while P11 workflow `31301133527` was still inside target-excluded scientific execution and before any P11 result was inspected. Its primary-literature physical justification was also recorded pretruth in comment `5230391784`.

P11 subsequently failed cleanly: qualified 90<95 and recovery@100 57<58 while precision remained strong. P12 therefore addresses the already-preregistered representation limitation rather than adding another post-result filter.

Solar longitude 20°–55° remains inaccessible throughout P12 development.

## Immutable lineage retained

P12 retains exact promoted-v8 families, immutable seed IDs, family order and multiplicity ranking; exact D_SH as the second feature; deterministic five-fold family exclusion; P3 seed-floor and local-negative reliability with exact `P3_NEGATIVE_TAIL_MAX=0.10`; P4 coordinate envelope; P8 finite-sample membership floor; P9 bidirectional reliability rule; P10 floor-consistent retained-seed joint frontier; P11 local density-contrast order-statistic veto; responsibility >0.5; no recursive growth/refit/recentering/reranking; and every existing substantive development gate.

Historical *counts* such as 218 bidirectionally reliable families, 50 changed P10 directions, and 436 P11 density directions belonged to the static P11 feature representation. P12 must recompute these counts from the unchanged rules in the new representation and may not require the old counts as scientific gates.

## Sole scientific change: observation representation

Canonical P11 uses a static source-year pooled center and a four-dimensional covariance in scaled `[solar-longitude residual, radiant-longitude residual, radiant-latitude residual, speed residual]`. P12 replaces only that observation-distance feature.

For each family-direction source year:

1. Use only that source year's immutable v8 seed events. Compute the exact inherited pooled source center.
2. Run the exact inherited residual transform, yielding `[t,y_lon,y_lat,y_vg]`, where `t` is the inherited wrapped/scaled solar-longitude residual, `y_lon` is the inherited cosine-corrected/scaled Sun-centered radiant-longitude residual, `y_lat` is the inherited scaled radiant-latitude residual, and `y_vg` is the inherited scaled speed residual.
3. Fit three deterministic unweighted linear regressions jointly by one `np.linalg.lstsq(design,response,rcond=None)`, where `design=[1,t]` and `response=[y_lon,y_lat,y_vg]`.
4. If the two-column design rank is <2, the sole fallback is slope exactly zero for all three responses and intercept equal to each response's arithmetic mean. No tolerance/regularization/robust loss is introduced.
5. Define each event's three-dimensional drift residual as `response - (intercept + slope*t)`.
6. Fit `sklearn.covariance.OAS(assume_centered=False)` to the source-seed three-dimensional drift residuals. Use ordinary matrix inverse when full-rank and Moore-Penrose pseudoinverse otherwise, exactly matching inherited inversion semantics.
7. Define `d_drift` as the square-root Mahalanobis distance of a source/target event's three-dimensional drift residual under that source-year covariance.
8. Do not add solar longitude as a fourth Mahalanobis coordinate: the inherited exact ±5° target-year local candidate window remains the activity-phase bound.
9. Replace the first feature everywhere by `d_drift`; the exact two-view vector is `[d_drift,D_SH]`. Static `d_obs` is not retained as a third feature or combined with `d_drift`.

All classifiers, scalers, seed floors, reliability booleans, P4/P8/P10 geometry, P11 density scores, proposals, conflicts and memberships are then recomputed deterministically in this new two-feature representation using their exact inherited algorithms/constants. No numeric threshold changes.

## Frozen pretruth provenance

Before any known-shower label value is indexed, P12 must freeze/hash:
- exact source seed identities per direction;
- source pooled center;
- OLS design rank and exact fit rule;
- all three intercepts/slopes;
- source drift-residual float64 arrays;
- OAS covariance/rank/inverse method;
- all target positive/local-unlabeled `[d_drift,D_SH]` arrays through inherited cross-fit hashes;
- all P3/P8/P9/P10/P11 reliability, density, proposal, conflict, assignment and final-membership payloads;
- the dedicated P12 drift payload SHA plus inherited model/density/membership/decision hashes.

Required integrity includes:
- every drift fit uses only source-year immutable seeds;
- source and target years differ for every direction;
- exact OLS or sole rank-deficient fallback only;
- 3-D covariance exactly;
- all drift distances finite;
- at least one nonzero fitted slope (nonvacuity only, never selection);
- exact D_SH identity unchanged;
- all inherited rule semantics preserved but historical static-representation counts recomputed rather than forced;
- target exclusion and full label-value firewall pass.

## No analytical degrees of freedom

There is no alternate polynomial degree, smoother, robust regression, weighting, slope significance test, clipping, covariance estimator, window size, solar-longitude feature, static/drift combination, feature rescaling, threshold, rescue, family exception, model selection or parameter sweep.

The linear form is physically motivated by established meteor-stream characterization practice, but P12 deliberately excludes truth-dependent member clipping/significance selection used in characterization studies. The source-year immutable seeds alone define the drift.

## Development gates — unchanged

P12 passes only if every integrity/nonvacuity/firewall gate passes and:
- qualified known-shower matches >=95;
- recovery@100 >=58;
- top-100 dominant precision >=0.65;
- macro-F1 >= exact v8 +0.08;
- large-shower mean recall >=1.5x exact v8;
- large-shower mean precision >=0.85.

No gate may be weakened after this freeze.

A development pass does **not** authorize OrbitTrace target access. The next mandatory stage is matched SonotaCo 2023/2025 comparison requiring sparse-stream superiority separately against both Sugar and catalogue HDBSCAN in both years. Only after that may no-retuning external validation occur; only after both pass may the final target-containing blind search be opened.