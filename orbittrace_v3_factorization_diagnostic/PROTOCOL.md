# OrbitTrace v3 factorization diagnostic

## Purpose

Determine whether the frozen multi-anchor wavelet-energy v3 contains useful catalogue-ranking information that is genuinely distinct from the Brown single-peak comparator on the already-exposed sparse-support v4 proposal scaffold.

This is an artifact-only development diagnostic. It does not open a meteor catalogue, later year, excluded interval, or OrbitTrace target information.

## Exact factorization

For every already-scored family/year episode:

- Brown amplitude `B` is the maximum positive wavelet coefficient.
- v3 energy `E` is the L2 norm of the four strongest positive coefficients.
- The only information in `E` not reducible to the scale `B` is the dimensionless top-four multiplicity

`M = (E / B)^2 = sum(top4_coefficients^2) / B^2`,

with `1 <= M <= 4` whenever `B > 0`.

No parameter is fitted and no threshold is searched.

## Frozen rankings

1. **multiplicity recurrence**: sort families by the smaller of `M_2022` and `M_2023` descending, then geometric mean multiplicity descending, then family ID;
2. **fixed4 + multiplicity RRF**: equal-weight reciprocal-rank fusion of the unchanged fixed4 persistence order and multiplicity recurrence order with the already-used fixed constant `k=60`.

These are diagnostic rankings, not a promoted detector.

## Evaluation

Using the unchanged fixed4 development label evaluation already present in the frozen artifact, report:

- recovered known-shower labels at top 100;
- MRR and median rank over the same 90 qualified labels;
- family-rank Spearman correlations;
- top-100 family overlap with Brown, v3, and fixed4;
- equal-weight fixed4+multiplicity RRF recovery.

## Interpretation rule

The non-Brown term is considered **not supported as a useful independent ranking signal** if both:

- multiplicity recurrence recovers no more top-100 known showers than Brown; and
- fixed4+multiplicity RRF recovers fewer top-100 known showers than unchanged fixed4 persistence.

Otherwise the result is exploratory evidence that the normalized multi-anchor term deserves a separately preregistered successor test.

This rule is frozen before the Actions run. It is not an authorization to tune a fusion weight or cutoff.
