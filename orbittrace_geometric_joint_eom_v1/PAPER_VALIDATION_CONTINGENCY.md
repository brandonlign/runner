# Geometric joint EOM v1 — dormant current-paper validation contingency

## Status

**FROZEN BEFORE THE FIRST TECHNICALLY VALID GMN OUTCOME. DORMANT UNLESS GMN PASSES.**

This contingency cannot execute unless the exact frozen GMN successor on PR #1366 returns `PASS_GEOMETRIC_JOINT_EOM_V1_GMN_DEVELOPMENT` under its pre-outcome density-synchronous-champion gate.

A GMN FAIL permanently closes this contingency without SonotaCo scientific execution.

## Method identity

Validation must use the exact geometric joint EOM v1 scientific definition frozen before GMN:

- protocol blob `f0e3acfafb1373371f081702526430423abc1df2`;
- kernel blob `0371bbc8f5e1a0234c499295c487d4d188dcaf2d`;
- development runner blob `acb685d98ceb273c1c70d6cd8e9f4d3168546e3d`;
- recurrent-EOM kernel blob `30ac3fa3bc47910370df528fcf3ae8ecb6277b47`;
- one pooled GEO6 HDBSCAN hierarchy with `min_cluster_size=10`, `min_samples=10`, Euclidean metric, EOM, epsilon 0, no single root;
- node quality `sqrt(ordinary_eom_stability * recurrent_eom_stability)`;
- one standard EOM cut on that quality;
- final order: joint stability, recurrent stability, ordinary stability, member count, deterministic family ID.

No validation-specific method change is authorized.

## Exact current-paper primary validation

The primary validation is exactly the benchmark currently used in the OrbitTrace paper, not the later symmetric tuned-HDBSCAN benchmark.

Frozen current paper result Git blob: `1ac067658d7a1d99b1a276099ca6d3fee83a6c0b` with verdict `PASS_TEMPORAL_FAIR_LITERATURE_4_OF_4`.

Panels:

1. Sugar 2013 — comparator-complete budget `B=40`;
2. Sugar 2014 — `B=43`;
3. published-configuration HDBSCAN 2013 — `B=14`;
4. published-configuration HDBSCAN 2014 — `B=14`.

For every panel:

- method construction receives pooled 2013+2014 label-free observations before truth;
- use the exact same route-specific row universe as the current paper benchmark;
- freeze the complete geometric-joint candidate catalogue before truth;
- evaluate the indicated year only afterward;
- use the exact current-paper eligible-shower definition;
- use one-to-one Hungarian assignment maximizing F1;
- compare at exactly the current paper comparator-complete candidate budget.

## Validation promotion gate

Geometric joint EOM can replace current recurrent-EOM in the paper only if all conditions hold:

1. strict macro-F1 superiority over the corresponding literature comparator on all 4/4 panels;
2. recovered `F1>0.5` shower count at least equal to the literature comparator on all 4/4 panels;
3. macro-F1 no lower than current paper recurrent-EOM on all 4/4 panels;
4. recovered-shower count no lower than current recurrent-EOM on all 4/4 panels;
5. strict macro-F1 improvement over current recurrent-EOM on at least one panel;
6. mean macro-F1 across all four panels strictly higher than current recurrent-EOM.

A valid SonotaCo FAIL is binding. No exponent/weight change, ordinary/recurrent rescaling, route exception, budget exception, ranking change, HDBSCAN setting change, union catalogue, threshold, or second validation attempt is authorized.

## Secondary benchmark

Only after the exact current-paper validation PASS may the already-completed symmetric tuned-HDBSCAN benchmark be used as harder secondary characterization. It cannot redefine, replace, or rescue the current-paper validation.
