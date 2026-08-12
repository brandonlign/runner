# OrbitTrace v36 density-normalized local-geometry contrast OOF ranker

## Scientific role

Separately frozen exposed-SonotaCo development successor after v31 and diagnostics #1046/#1049/#1050/#1053. v31 remains a binding 2/4 failure and is not modified or rescued in place.

The fixed 229-family HDBSCAN candidate universe can beat the literature comparator at both exact budgets (#1050), while #1053 shows the residual v31 set error is small: one shower-group substitution can clear 2014 and two can clear 2013. At the same time, required recoverable groups can be globally low-ranked and locally isolated, so absolute nearest-class margin can penalize candidates simply because both positive and nonpositive training support are far away. The successor therefore tests one canonical, parameter-free change: normalize the signed nearest-class distance margin by total nearest-class distance.

SonotaCo 2013/2014 is exposed development only. This result is not external validation.

## Immutable inputs and anti-leakage structure

Keep exactly:

- immutable #950 71-dimensional pretruth feature matrices and fixed family memberships;
- exact shared strict whole-shower five-fold assignment across Sugar and HDBSCAN;
- exact v31 annual positive definition `annual F1 > 0.5` for the fixed best shower label;
- fold-training mean / population-standard-deviation z-scoring across all 71 dimensions, zero standard deviation replaced by 1.0;
- ordinary Euclidean distance and `k=1` nearest annual-positive and annual-nonpositive references;
- annual conservative `min` combiner;
- exact #839 diversity ordering (`lambda=0.8`, `scale=1.0`);
- exactly one equal rank-sum with frozen v19;
- exact fixed memberships, budgets, evaluator, and literature comparators.

Every strict shower group remains wholly absent from the model/reference training fold used to score that group. No candidate generation or membership change is allowed.

## Sole scientific change

For held-out family `i` and year `y`, using the exact v31 fold-local standardized Euclidean distances

- `d_pos(i,y)` = distance to the single nearest annual-positive fold-training family;
- `d_nonpos(i,y)` = distance to the single nearest annual-nonpositive fold-training family;

define the annual density-normalized contrast

`c(i,y) = (d_nonpos(i,y) - d_pos(i,y)) / (d_nonpos(i,y) + d_pos(i,y))`.

The denominator must be finite and strictly positive; otherwise the run fails closed. No epsilon, clipping, exponent, transform, temperature, or alternate normalization exists.

The final geometry score is exactly `min(c(i,2013), c(i,2014))`. Higher is better. This bounded contrast preserves the direction of v31's nearest-class evidence while removing the absolute local-distance scale that can vary for sparse or out-of-distribution candidate groups.

## Parent control

The same computed `d_pos` and `d_nonpos` values must also reconstruct exact v31's absolute margin `d_nonpos-d_pos`, exact diversity, and exact v19 fusion before the successor result is accepted. Required exact v31 controls:

- Sugar 2013: macro-F1 `0.2719801488280529`, recovery `16`;
- Sugar 2014: macro-F1 `0.31529041952487225`, recovery `17`;
- HDBSCAN 2013: macro-F1 `0.14888037368183737`, recovery `9`;
- HDBSCAN 2014: macro-F1 `0.15198123772301594`, recovery `9`.

Failure to reproduce any parent control is an engineering/provenance failure, not a scientific v36 result.

## Binding evaluation

Exactly one successor order is evaluated. A panel is a win only when:

- candidate macro-F1 is strictly greater than the frozen literature comparator; and
- recovered `F1 > 0.5` shower count is at least the literature comparator.

v36 passes development only with 4/4 wins. The first technically valid result is binding.

If v36 fails, this exact normalized contrast is permanently rejected. No denominator variant, epsilon, clipping, nonlinear transform, k, metric, covariance, scaling, feature subset/block weight, threshold, annual combiner, diversity setting, fusion weight/algebra, source quota, route-specific rule, budget-specific rule, or post-result second search is authorized within v36.

If v36 passes 4/4, freeze only the exact full exposed-development reference package needed to reproduce this score. A pass remains exposed-development evidence only and does not authorize protected target access or an external-superiority claim.

## Firewall

- `20°–55°` protected OrbitTrace target-region content remains inaccessible.
- No OrbitTrace target information or target-region events may be accessed.
- No MAARSY or DMS scientific access is authorized.
- No oracle family/group identity from #1050/#1053 may enter the score, rank, code path, or protected use.
- Candidate memberships are fixed and unchanged.
