# OrbitTrace station-support-weighted topomodal recovery v1

## Status

**FROZEN BEFORE ANY PROJECT `Num (stat)` AVAILABILITY OUTCOME, BEFORE ANY STATION-WEIGHTED TOPOMODAL STRUCTURAL OUTCOME, AND BEFORE ANY STATION-WEIGHTED SHOWER-TRUTH ACCESS.**

Execute only if both prerequisites hold exactly:

1. `PASS_TOPOMODAL_NUMSTAT_AVAILABILITY_V1`;
2. `SUPPORTS_STATION_WEIGHTED_TOPOMODAL_CROSS_SCALE_COHERENCE`.

If either prerequisite fails or the structural stage is blocked by incomplete event weights, this truth-bearing successor is permanently blocked.

## 1. Exact scientific method

Use the exact pre-frozen station-weighted structural method without modification:

- target-excluded GMN 2022+2023 only;
- #1284 physical embedding, 5° solar / 4° radiant / 10% log-speed;
- exact symmetric Euclidean radius-1 physical neighborhoods including self;
- exact event weight `w_j = Num(stat)_j`, integer >=2, with no transform/cap/imputation;
- manual density `rho_station(i) = sum_{j in N1(i)} w_j / sum_{k in subset} w_k`;
- GUDHI 3.12.0 manual-graph/manual-density ToMATo;
- complete leaf/internal/root hierarchy;
- exact membership deduplication;
- support >=4.

Station identity, participating-station strings, station geography, and any other GMN quality variable remain absent.

## 2. Candidate ordering is frozen independently of station-count outcome

Use the exact intrinsic #1284 sparse-recovery hierarchy-ordering semantics already frozen before its first truth result, pinned to:

- commit `312b1b718ae105813de242355142a74e7d377d65`;
- source `orbittrace_topomodal_sparse_recovery_v1/run_development.py`;
- Git blob `752df8212ce601227f6e9170b0fe994ba06b515d`.

The station-weighted hierarchy substitutes only for the #1284 hierarchy input. The intrinsic ranking equations, root handling, finite-node handling, tie rules, and family-hash tie break are unchanged.

No station-count statistic may enter ranking separately from its already-frozen role in the upstream density field. No ordinary-density blend, year recurrence term, station-count rank, station-count sum per candidate, exposure correction, or learned coefficient is authorized.

## 3. Frozen sparse panels

Use exactly the same deterministic panels:

- denominator 128, buckets 0,1,2,3;
- denominator 1024, buckets 0,1,2,3;
- identity salt `ORBITTRACE_SCALE_STRESS_V1|`.

No other thinning level, bucket, salt, or replicate.

## 4. Pretruth immutable seal

Before shower truth is loaded, serialize and SHA-256 seal for all eight subsets:

- exact event-ID universe/order;
- exact `event_id -> num_stat` mapping hash from the binding availability artifact;
- exact physical-coordinate hash;
- radius-neighborhood hash;
- station-weighted density-vector hash;
- complete support>=4 ToMATo hierarchy memberships;
- every intrinsic ranking field and final successor order;
- exact recurrent-EOM comparator memberships/order;
- equal candidate budget K;
- source/input/runtime hashes;
- complete firewall fields.

The post-seal evaluator may not regenerate, alter, rerank, merge, split, or otherwise modify candidates.

## 5. Exact recurrent-EOM comparator

Unchanged:

- GEO6;
- HDBSCAN `min_cluster_size=10`, `min_samples=10`;
- Euclidean;
- exact annual-normalized recurrent-EOM node quality;
- exact FOSC/EOM extraction.

## 6. Equal-budget evaluation

For each panel:

`K = min(successor candidate count, recurrent-EOM candidate count)`.

Evaluate top K from each immutable order using the exact #1284 sparse-recovery evaluator.

Report:

- qualified known-shower matches;
- recovered showers @25/@50/@100/@500, capped by K;
- mean reciprocal rank of first qualifying candidate per eligible shower;
- top-100 dominant-candidate precision;
- median fragmentation among top-500 qualifying matches.

Aggregate separately across the four d1024 and four d128 panels.

## 7. Frozen ten promotion gates

`PASS_STATION_WEIGHTED_TOPOMODAL_RECOVERY_V1` requires **all ten**:

### Fine sparse scale, d1024

1. successor qualified total strictly greater than recurrent-EOM;
2. successor qualified count nonlower in at least 6 of 8 annual panel evaluations;
3. successor mean MRR not lower;
4. successor mean top-100 dominant precision not lower;
5. successor mean median-fragmentation not higher.

### Coarse sparse scale, d128

6. successor qualified total not lower than recurrent-EOM;
7. successor qualified count nonlower in at least 6 of 8 annual panel evaluations;
8. successor mean MRR not lower;
9. successor mean top-100 dominant precision not lower;
10. successor mean median-fragmentation not higher.

Any failed gate returns `FAIL_STATION_WEIGHTED_TOPOMODAL_RECOVERY_V1` and permanently closes the exact architecture.

## 8. No rescue

After the first technically valid truth outcome, do not change:

- event station-weight definition;
- any station-count transform/cap/threshold/imputation;
- physical graph, radius, or physical scales;
- density formula;
- support floor;
- ToMATo hierarchy;
- intrinsic ranking semantics or tie rule;
- equal-budget rule;
- metric;
- subset/salt;
- gate.

No result-informed rerank, density blend, recurrence blend, station-quality feature, or alternative observational-support statistic is authorized.

## 9. Firewall

Protected solar longitude `[20.0,55.0]` remains excluded inclusively before station weight enters any method statistic. OrbitTrace target information/events, SonotaCo, ASFN/EFN event rows, AMOS, MAARSY, and DMS remain inaccessible during this GMN development test.