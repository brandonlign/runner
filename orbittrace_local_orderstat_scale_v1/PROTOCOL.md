# OrbitTrace local order-statistic scale calibration diagnostic v1

## Status

**FROZEN BEFORE IMPLEMENTATION AND BEFORE ANY DIAGNOSTIC OUTCOME.**

This is a zero-label statistical-feasibility diagnostic only. It is not a shower-recovery successor, does not rank candidates, and cannot promote a final method.

It follows PRs #1272–#1276:

- fixed HDBSCAN support becomes statistically coarse and recurrent-EOM becomes inert as catalogue size shrinks;
- both core smoothing and branch condensation contribute to that failure;
- dimensionless local/tree scale ratios are much more sample-size-stable than absolute radii;
- deterministic tree topology/pruning (ordinary single link, log-mass FOSC, theory-scaled RSL) does not identify which branches are scientifically real.

The present diagnostic therefore tests a different object: **local statistical surprise relative to an event's own broader neighborhood**, without a global density scale or shower labels.

## 1. Local-null derivation

GEO6 is a six-coordinate embedding of a locally four-dimensional physical state:

1. solar-longitude circle: one local degree of freedom;
2. Sun-centered radiant sphere: two local degrees of freedom;
3. geocentric speed: one local degree of freedom.

Freeze intrinsic dimension `D=4`.

For a center event, let `r_j` denote Euclidean GEO6 distance to the `j`-th nearest *other* event. Under a locally homogeneous 4-D point process, conditional on the outer `k`-th-neighbor radius, the normalized enclosed-volume ratio

`U = (r_j / r_k)^D`

is the `j`-th order statistic of `k-1` independent Uniform(0,1) enclosed-volume fractions, hence

`U ~ Beta(j, k-j)`.

Small `U` means the inner neighborhood is unusually compact relative to its own broader local background.

Define lower-tail local-surprise p-value

`p = BetaCDF(U; j, k-j)`

and score only for reporting

`S = -log10(max(p, machine_tiny))`.

No p-value threshold is used to select events or clusters in this diagnostic.

## 2. Frozen support scales

Use four dyadic total-support anchors separately:

`s in {4, 8, 16, 32}`.

For total support `s` including the center:

- inner neighbor index `j = s - 1`;
- outer neighborhood total support `2s`, so outer neighbor index `k = 2s - 1`;
- null law `Beta(s-1, s)`.

Thus exact pairs are:

- s=4: `(j,k)=(3,7)`;
- s=8: `(7,15)`;
- s=16: `(15,31)`;
- s=32: `(31,63)`.

Each scale is evaluated independently. No maximum, minimum, fusion, winner selection, multiplicity-combined score, or post-result support choice is authorized.

The dyadic family is frozen because it begins at the project's established minimum evaluable support of four and doubles resolution without introducing a fitted scale.

## 3. Synthetic calibration screen

Before GMN geometry is interpreted, verify the probability transform on independent homogeneous 4-D periodic-torus experiments.

For each synthetic catalogue size `n in {768, 6144}`:

- run exactly `4096` independent trials;
- deterministic NumPy seed base `2026081601`;
- for trial `t`, derive a fresh RNG from `SeedSequence([2026081601, n, t])`;
- generate `n` iid points Uniform([0,1)^4);
- use point 0 as the query center;
- compute exact periodic coordinate differences `min(|dx|,1-|dx|)` to all other points;
- obtain the first 63 Euclidean neighbor distances by exact partition/sort;
- compute `p` separately for each frozen support scale.

For each of the 8 `(n,s)` p-value samples, test Uniform(0,1) with a two-sided one-sample Kolmogorov-Smirnov test.

Frozen synthetic calibration gate:

- every one of the 8 KS p-values must be >= `0.00625` (`0.05/8` Bonferroni familywise level).

This is an implementation/theory calibration screen, not a power test.

## 4. GMN firewall and subsets

Use only target-excluded GMN 2022+2023 geometry under exact GEO6. Remove inclusive solar longitude `[20.0,55.0]` before geometry.

Forbidden:

- OrbitTrace target information or target-region events;
- all shower labels/truth;
- SonotaCo scientific access;
- ASFN or EFN event-level access;
- AMOS scientific access;
- MAARSY or DMS scientific access.

Reuse exact PR #1272 nested hash subsets:

`H(eid) = uint64_be(SHA256('ORBITTRACE_SCALE_STRESS_V1|' + eid)[0:8])`.

Use exactly:

- denominator `128`, buckets `0,1,2,3` (~5.8k events);
- denominator `1024`, same buckets (~0.7k events).

For each bucket, the denominator-1024 universe is a strict subset of denominator-128.

No other denominator, bucket, salt, sample, or external survey is authorized.

## 5. GMN scale diagnostics

For every subset, compute exact Euclidean kNN distances through `scipy.spatial.cKDTree` with maximum requested neighbor index 63. The query event itself is excluded.

For each frozen support scale independently record:

- raw inner radius `r_j`;
- dimensionless local ratio `U=(r_j/r_k)^4`;
- Beta lower-tail `p`;
- surprise `S=-log10(p)`.

### 5.1 Distributional scale drift

Pool all four denominator-128 buckets and all four denominator-1024 buckets separately at each support scale.

For each support scale compute two-sample KS statistics across catalogue scales for:

- raw inner radius `r_j` (negative control);
- `U`.

Because BetaCDF is monotone, its KS statistic is mathematically identical to `U` and is not counted as another win.

A support-scale distributional win requires

`KS(U_128,U_1024) < KS(rj_128,rj_1024)`.

### 5.2 Same-event cross-scale rank stability

For each bucket, evaluate only events in the fine denominator-1024 universe, which are also present in the paired coarse denominator-128 universe.

For each support separately compute Spearman rank correlation between coarse and fine values for:

- raw compactness `-log(r_j)`;
- local surprise `S=-log10(p)`.

For each support, take the median correlation across the four buckets.

A support-scale rank-stability win requires

`median_rho(S) > median_rho(-log r_j)`.

No absolute rho threshold is used.

## 6. Frozen interpretation gate

Return

`SUPPORTS_LOCAL_ORDERSTAT_SCALE_CALIBRATION`

iff all of the following hold:

1. all 8 synthetic KS calibration tests pass the frozen Bonferroni threshold;
2. all four support scales are strict GMN distributional wins;
3. at least three of four support scales are strict same-event rank-stability wins; and
4. the median across the four support-specific median Spearman correlations is strictly greater for local surprise than for raw compactness.

Otherwise return

`REFUTES_LOCAL_ORDERSTAT_SCALE_CALIBRATION`.

There is no mixed verdict and no rescue.

## 7. Consequences

A positive result establishes only that the local order-statistic probability coordinate is well calibrated under its exact synthetic null and transfers across sample size better than absolute local radius on target-excluded GMN. It would authorize one separately frozen follow-up to construct a statistically multiplicity-controlled event/core or branch significance rule without shower truth first.

A negative result closes this exact `D=4`, `{4,8,16,32}` dyadic local-order-statistic architecture for OrbitTrace. It may not be rescued by changing intrinsic dimension, support scales, outer-neighborhood ratio, Beta tail, combination rule, salt, subset, or gate after seeing the result.

No scientific claim about known showers or external generalization can be made from this diagnostic alone.
