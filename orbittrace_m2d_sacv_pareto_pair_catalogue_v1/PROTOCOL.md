# OrbitTrace M2D + SACV Pareto-pair catalogue v1 — frozen protocol

## Status

**FROZEN BEFORE IMPLEMENTATION, BEFORE ZERO-LABEL STRUCTURAL OUTCOME, AND BEFORE ANY SHOWER-TRUTH OUTCOME FOR THIS SUCCESSOR.**

This is a scientifically distinct successor to the closed single-output recurrence/component/core family. It does not choose one validated SACV pair, merge a recurrence component, threshold a recurrence graph, or alter SACV-v1 primary membership. Instead, every already-valid cross-year SACV hypothesis pair is retained intact as an independently reportable child candidate, and the complete child catalogue is ordered by a parameter-free Pareto construction.

The construction is justified by two target-free facts already frozen in the repository:

1. SACV v1 (#1405) defines an intrinsic annual hypothesis order by maximizing `(excess, parent_support, -contamination, -radius)` with smaller center ID as the final tie break; and
2. pre-reveal recurrent–TopoModal Pareto-prominence v1 (#1294) passed all ten frozen GMN gates by retaining independently corroborated children intact and combining inherited parent priority with child-intrinsic evidence through ordinary non-dominated layers rather than a fitted weighted score.

No OrbitTrace target information is used to define objectives, tie rules, candidate budgets, memberships, or gates.

## 1. Firewall

Development uses only the established target-excluded GMN 2022+2023 sparse panels. Inclusive solar longitude `[20.0,55.0]` remains excluded before construction and truth evaluation.

Forbidden throughout this experiment:

- OrbitTrace canonical IDs, coordinates, target-region events, target size, target pair/component scores, or target membership;
- SonotaCo scientific access before a binding GMN PASS;
- ASFN/EFN event-level access, AMOS, MAARSY, or DMS scientific access;
- shower-truth-informed objectives, budgets, ranks, membership edits, duplicate handling, or tie rules;
- post-result threshold, radius, support, score, Pareto-objective, or ordering rescue.

## 2. Immutable construction machinery

Use the exact target-excluded M2D panel parents/ranks from the frozen GMN fair pretruth and exact SACV-v1 geometry/constants: years 2022 and 2023; solar scale 5 degrees; radiant scale 4 degrees; speed fraction 10%; maximum normalized radius 1.0; minimum support 4; maximum modeled contamination 0.10; seasonal analog offsets 60..300 degrees by 10; for each event center the widest radius satisfying the frozen SACV-v1 support/contamination/positive-excess rule; and exact reciprocal cross-year validation in which each endpoint has opposite-year support >=4 and center distance lies within both endpoint radii.

The neutral all-hypothesis enumeration and reciprocal validation are inherited from the frozen SACV recurrence lineage. The failed recurrence-pair-v2 *single-pair selector* is not used.

## 3. Exact annual SACV hypothesis ranks

For each M2D parent and each year independently, enumerate every SACV-admissible annual hypothesis. Define its one-indexed intrinsic annual rank by the exact original pre-target SACV-v1 selector order:

1. descending `excess`;
2. descending `parent_support`;
3. ascending `contamination`;
4. descending radius;
5. ascending center event ID.

This is exactly equivalent to maximizing frozen SACV-v1 key `(excess, parent_support, -contamination, -radius)` with event-ID tie break. Ranks must form a permutation `1..N_y` for that parent's annual hypotheses.

## 4. Intact validated-pair child catalogue

For every exact validated 2022×2023 hypothesis pair, create one child candidate. Child membership is exactly the sorted union of the two endpoint SACV balls, restricted to the immutable M2D parent. No intersection, consensus frequency, component union, halo, pruning, trimming, threshold, target-size cap, or membership modification is allowed.

Every validated pair is retained as a distinct candidate identity, including pairs whose event memberships happen to be identical. There is no post-hoc deduplication or one-child-per-parent quota. Such duplicates consume reporting capacity and therefore cannot create a free advantage.

For child `s`, define three minimized ordinal objectives:

- `P(s)`: immutable M2D parent rank;
- `A(s)`: exact frozen annual SACV hypothesis rank of the 2022 endpoint;
- `B(s)`: exact frozen annual SACV hypothesis rank of the 2023 endpoint.

No pair score, averaging, weighting, normalization, bottleneck-support objective, center-distance objective, target-aware preference, or learned reranker is used.

## 5. Pareto depth and total order

For distinct children `x,y`, `x` dominates `y` iff `P(x)<=P(y)`, `A(x)<=A(y)`, and `B(x)<=B(y)`, with at least one strict inequality. Assign ordinary non-dominated layers: layer 1 is the current non-dominated set; remove it; repeat until every child has one positive integer layer.

Final total order is:

1. ascending Pareto layer;
2. ascending deterministic `pair_hash`, defined solely from `(parent family hash, 2022 center ID, 2023 center ID)`.

The hash is a tie order only and is not a scientific score. It deliberately adds no post-reveal preference among incomparable points on the same Pareto layer.

## 6. Equal-budget rule

For each panel, let `K` be the exact number of immutable M2D/SACV parent candidates in that panel. The successor reporting catalogue is the first `K` Pareto-pair children. The SACV-v1 comparator is its exact `K` original candidate rows at immutable parent ranks.

The complete pair catalogue must contain at least `K` candidates in every panel. If any panel has fewer than `K`, the method is structurally `POWER_INCONCLUSIVE` / non-authorized before shower truth; no parent fallback candidates may be injected to fill capacity. Thus producing many pair children cannot manufacture an advantage by increasing reporting budget.

## 7. Zero-label structural authorization

Before any shower truth opens, persist the complete pair catalogue and require all of:

1. frozen fair-pretruth and geometry identities reproduce exactly;
2. target/firewall flags remain false;
3. every child maps to exactly one immutable M2D parent and exact validated cross-year pair;
4. every child membership equals byte-for-byte the union of its endpoint SACV balls;
5. every annual hypothesis rank is a permutation under the exact frozen SACV-v1 selector order;
6. every Pareto layer assignment satisfies the frozen three-objective dominance rule;
7. final ranks are a deterministic permutation `1..N` of the complete pair set;
8. every child has at least four member events from 2022 and at least four from 2023;
9. candidate capacity `N >= K` in all eight panels;
10. no target information, shower truth, or SonotaCo scientific data was accessed.

Only `PASS_M2D_SACV_PARETO_PAIR_CATALOGUE_V1_PRETRUTH` authorizes hidden GMN truth.

## 8. Binding target-excluded GMN contract

Use the same frozen sparse-GMN hidden-truth runtime and catalogue metrics as pre-reveal recurrent–TopoModal Pareto-prominence v1, but compare the equal-budget top-`K` Pareto-pair catalogue against exact SACV-v1 equal-budget catalogue in every annual panel.

Report qualified matches, recovered@25/@50/@100/@500, top-100 dominant precision, zero-filled eligible-query MRR, and median top-500 fragmentation. Historical conditional MRR is diagnostic only.

At each sparse scale (`d=1024` and `d=128`), all five gates must pass against SACV v1:

1. qualified-total is not lower;
2. qualified matches are nonlower in at least 6/8 annual panels;
3. mean zero-filled eligible-query MRR is not lower;
4. mean top-100 dominant precision is not lower;
5. mean median top-500 fragmentation is not higher.

In addition, across the two scales combined, at least one of qualified-total, zero-filled MRR, or top-100 dominant precision must be a strict improvement on at least one scale. Exact equality everywhere is not promotion evidence.

Binding verdict is exactly one of:

- `PASS_M2D_SACV_PARETO_PAIR_CATALOGUE_V1_GMN_DEVELOPMENT`;
- `FAIL_M2D_SACV_PARETO_PAIR_CATALOGUE_V1_GMN_DEVELOPMENT`;
- `POWER_INCONCLUSIVE_M2D_SACV_PARETO_PAIR_CATALOGUE_V1_GMN_DEVELOPMENT` only when the frozen pretruth capacity condition prevents truth-authorized comparison.

The first technically valid execution is binding.

## 9. Continuation / closure

A binding GMN PASS authorizes exactly one unchanged SonotaCo transfer under the same pair construction, annual-rank semantics, Pareto objectives, tie order, equal-budget rule, and already-established SACV-v1 transfer benchmark. No OrbitTrace target application occurs before that transfer passes.

A valid GMN FAIL permanently closes this exact intact-pair three-view Pareto catalogue. Do not rescue it by weighted ranks, pair-v2 support/distance/excess scores, alternate Pareto objectives, frontier-only selection, crowding distance, quotas, membership unions, target-size filters, deduplication, or post-result tie changes.
