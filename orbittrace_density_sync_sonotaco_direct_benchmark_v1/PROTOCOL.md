# OrbitTrace #1263 density-sync direct SonotaCo benchmark v1

## Status

**FROZEN BEFORE THE FIRST #1263 SONOTACO OUTCOME UNDER THIS DIRECT BENCHMARK.**

This benchmark is an explicit owner-authorized use of already-exposed SonotaCo 2013/2014 development data to decide whether density-synchronous recurrent-EOM (#1263) earns selection over its recurrent-EOM predecessor. SonotaCo is **EXPOSED DEVELOPMENT / VALIDATION BENCHMARK ONLY**, not pristine external validation.

No AMOS data are used or requested. Protected OrbitTrace solar longitude `[20°,55°]` remains excluded inclusively. OrbitTrace target information/events, MAARSY and DMS remain inaccessible.

## Fixed methods

### Recurrent-EOM predecessor

Exact implementation blob:

`30ac3fa3bc47910370df528fcf3ae8ecb6277b47`

Its established SonotaCo benchmark is binding historical evidence: run `31829200215`, result SHA-256 `c2395a86be5ba8a8b801210ac6e64b97c446e724991207aef85062ee00b89f12`.

### Density-synchronous recurrent-EOM #1263

Exact implementation blob:

`587a304f451e41b9503272f1783a6c6ebb295000`

Binding #1263 GMN execution head:

`182f07ade6bb5d4be2c80b88df9216bb2d6eee2d`

No method byte, HDBSCAN parameter, geometry, normalization, score, ranking rule, evaluator, candidate budget, or row eligibility may change for this benchmark.

## Same-data head-to-head construction

For each established SonotaCo route (`sugar`, `hdbscan`):

1. use the exact label-free SonotaCo 2013/2014 rows from the recurrent-EOM benchmark;
2. fit exactly one pooled two-year HDBSCAN hierarchy with the existing GEO6 representation and exact `min_cluster_size=10`, `min_samples=10`, Euclidean, EOM, epsilon 0, no single cluster;
3. on that same hierarchy compute ordinary stability, recurrent-EOM stability, and exact #1263 density-synchronous stability;
4. extract recurrent-EOM and density-sync candidates independently with the unchanged HDBSCAN/FOSC extraction;
5. freeze complete memberships and ranks for both methods before SonotaCo shower truth, v31 results, or literature-comparator results are opened;
6. after the freeze, evaluate both methods with the exact established Hungarian macro-F1 evaluator and exact established panel budgets.

The benchmark must reproduce the established recurrent-EOM SonotaCo metrics before interpreting #1263.

## Established comparison panels and budgets

- Sugar 2013: budget 34
- Sugar 2014: budget 46
- HDBSCAN 2013: budget 11
- HDBSCAN 2014: budget 9

Exact v31 controls remain:

- Sugar 2013: macro-F1 `0.2719801488280529`, recovered `16`
- Sugar 2014: macro-F1 `0.31529041952487225`, recovered `17`
- HDBSCAN 2013: macro-F1 `0.14888037368183737`, recovered `9`
- HDBSCAN 2014: macro-F1 `0.15198123772301594`, recovered `9`

## Frozen decision rule

### POSITIVE / select #1263

`PASS_DENSITY_SYNC_SONOTACO_DIRECT_BENCHMARK_V1` requires all of the following:

1. #1263 satisfies the established v31 pair gate on **all four panels**: macro-F1 strictly greater than v31 and recovered F1>0.5 at least equal to v31;
2. versus recurrent-EOM, #1263 macro-F1 is **non-lower on all four panels**;
3. versus recurrent-EOM, #1263 recovered F1>0.5 count is **non-lower on all four panels**;
4. #1263 is **strictly better than recurrent-EOM on at least one panel** in either macro-F1 or recovered count;
5. the density-synchronous mechanism is active on at least one route through a changed selected-node set and/or changed complete candidate order.

### NEUTRAL / added criterion not earned

`NEUTRAL_DENSITY_SYNC_SONOTACO_DIRECT_BENCHMARK_V1` requires #1263 to retain 4/4 v31 superiority and be non-lower than recurrent-EOM on all four panels, but show **no strict improvement over recurrent-EOM on any panel**. In that case the benchmark provides no evidence that density-sync earns its added criterion over recurrent-EOM.

### NEGATIVE / recurrent-EOM preferred

Any regression against recurrent-EOM in macro-F1 or recovered count on any panel, or loss of the established 4/4 v31 superiority pattern, yields:

`FAIL_DENSITY_SYNC_SONOTACO_DIRECT_BENCHMARK_V1`.

No aggregate-average rescue, route exception, precision/recall threshold change, candidate-budget change, rerank, blend, new HDBSCAN parameter, or post-result variant is allowed.

## Interpretation

This benchmark is allowed to choose between the two already-fixed methods for the paper/development methodology. It does **not** become pristine external validation merely because it is decisive. Seeing the result does not invalidate the result for the method that was frozen before execution; it only means any later method designed in response would not receive independent validation claims on these same SonotaCo outcomes.

## Firewall

The result must record:

- `sonotaco_role = EXPOSED_DEVELOPMENT_VALIDATION_BENCHMARK`;
- `blind_exclusion = [20.0,55.0]`;
- `target_information_access = false`;
- `target_region_events_accessed = false`;
- `amos_access = false`;
- `maarsy_scientific_access = false`;
- `dms_scientific_access = false`;
- `post_result_parameter_search = false`.
