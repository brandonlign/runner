# OrbitTrace GMN v31 component-year balance v1 — frozen protocol

## Status

**PRE-OUTCOME SCIENTIFIC FREEZE.** This defines exactly one target-excluded GMN 2022/2023 successor to exact v31 before any candidate score/rank/performance outcome is calculated.

Authoritative inputs are the immutable v31 offline-development package (artifact `9167087908`) plus the already-frozen P19 prelabel payload that contains the exact 226 hard-family objects and year-tagged component IDs. No raw catalogue or external scientific data is required.

Exact parent controls: recovered@25 `23`, recovered@50 `41`, recovered@100 `66`, top-100 dominant precision `0.7229521515453452`, MRR `0.050244164168646674`, qualified matches `95`.

## Scientific motivation

Exact v31 includes total component count, annual detector-strength balance, annual member-count balance, cross-year centroid displacement, and member-cloud cohesion. It does **not** encode whether the detector's independent component fragments themselves are recurrently distributed across both development years.

Two families can have the same total component count but different structural recurrence: a balanced family may have comparable component support in 2022 and 2023, while an imbalanced family may obtain nearly all of its component evidence from one year. Annual component-count balance therefore measures recurrence of the detector's structural support, not recurrence of member counts, activity profiles, radial member profiles, covariance shape, or cross-route component topology.

A label-free pre-outcome feasibility audit established only that every one of the 226 hard families has at least one component in both 2022 and 2023, every component ID carries an unambiguous 2022/2023 year prefix, and the two annual counts sum exactly to the stored total `component_count`. No development label or ranking outcome was inspected for this feasibility decision.

## Sole scientific change

For each immutable hard family, count exact `component_ids` beginning with `2022-` and `2023-`:

- `n22 = number of 2022 component_ids`
- `n23 = number of 2023 component_ids`

Append exactly one 24th coordinate:

`component_year_balance = min(n22,n23) / max(n22,n23)`.

Both counts must be strictly positive and their sum must equal the stored total component count; otherwise fail closed before scoring.

No threshold, smoothing, epsilon, logarithm, entropy, component-size weighting, source weighting, total-count normalization, rank transform, or alternative annual-combination formula is permitted.

The exact 23 existing v31 coordinates remain unchanged.

## Exact inherited v31 architecture

Everything except the one appended coordinate remains exact v31:
- immutable 226 hard-family universe and order;
- exact v31 23D feature matrix and centroid matrix from the offline package;
- exact strict whole-shower five-fold OOF split and frozen development labels;
- fold-training mean and population-standard-deviation scaling, zero std -> `1.0`;
- ordinary Euclidean distance;
- k=1 nearest positive and nearest nonpositive reference;
- margin `d_nonpositive - d_positive`;
- exact diversity lambda `0.8`, scale `1.0`, hard-order tie semantics;
- exact equal 1-based rank-sum fusion with immutable P19 hard order;
- exact monotone GMN evaluator.

The evaluator must reproduce the exact parent feature SHA, exact parent margin SHA, hard-order metrics, and fused parent metrics before the candidate outcome is technically valid.

## Binding PASS gate

The first technically valid candidate outcome is binding. PASS requires all:
1. recovered@100 > `66`;
2. recovered@25 >= `23`;
3. recovered@50 >= `41`;
4. top-100 dominant precision >= `0.7229521515453452`;
5. MRR >= `0.050244164168646674`;
6. qualified matches exactly `95`;
7. all provenance and firewall assertions pass.

A FAIL terminates this mechanism without SonotaCo access.

## No-rescue closure

After the first valid result do not retry:
- max/min difference, absolute difference, signed difference, ratio inverse, log ratio, entropy, Gini, harmonic/geometric mean, or another component-year balance formula;
- component-size, quartet-count, anchor-count, strength, or score weighting of annual component counts;
- annual anchor/quartet balance variants motivated by this outcome;
- thresholds, bins, rank/percentile transforms, clipping, smoothing, or epsilons;
- adding/removing other features, feature subsets, metric/k/scaling/fold/reference changes;
- diversity/fusion/weight/source/rank-window/budget changes;
- blending with activity-KS, radial-KS, thinning stability, component-topology, or another failed successor;
- any identity-specific or post-result second search.

Any future successor after a binding FAIL must change mechanism class and be independently motivated/frozen.

## Firewall

Scientific role: `TARGET_EXCLUDED_GMN_2022_2023_V31_OFFLINE_SUCCESSOR_DEVELOPMENT_ONLY`.

Required assertions: raw event rows accessed=false; SonotaCo 2013/2014 access=false; protected target-region events accessed=false; OrbitTrace target information access=false; MAARSY scientific access=false; DMS scientific access=false.