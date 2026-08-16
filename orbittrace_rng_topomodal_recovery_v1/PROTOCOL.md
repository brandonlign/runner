# OrbitTrace RNG-pruned topomodal recovery v1

## Status

**FROZEN BEFORE THE FIRST TECHNICALLY VALID OUTCOME OF THE ZERO-LABEL RNG-TOPOMODAL SCALE DIAGNOSTIC AND BEFORE ANY RNG-TOPOMODAL SHOWER-TRUTH ACCESS.**

Execute only if `orbittrace_rng_topomodal_scale_v1` returns exactly:

`SUPPORTS_RNG_TOPOMODAL_CROSS_SCALE_COHERENCE`.

If that structural gate fails, this truth-bearing successor is permanently blocked and must not run.

## 1. Scientific change from #1284 recovery successor

The successor inherits the exact #1284 topomodal sparse-recovery architecture and its intrinsic candidate ordering, with exactly one scientific substitution:

- replace #1284's full radius-1 manual ToMATo connectivity with the exact radius-capped relative-neighborhood connectivity frozen in `orbittrace_rng_topomodal_scale_v1/PROTOCOL.md`.

Everything else remains unchanged:

- same target-excluded GMN 2022+2023 rows;
- same #1284 physical embedding and physical radius 1;
- same original radius-count density `rho_i=|N_1(i)|/n`, including self and computed **before** RNG pruning;
- same GUDHI 3.12.0 manual-graph/manual-density ToMATo hierarchy;
- same complete leaf/internal/root membership universe with support >=4;
- same exact intrinsic #1284 candidate-ordering semantics;
- same exact recurrent-EOM comparator;
- same deterministic sparse subsets;
- same truth evaluator and promotion gates.

No score blend, recurrence feature, empirical density rank, map equation, lineage round, significance filter, community model, drift feature, local background contrast, or post-result ranking rule is added.

## 2. Frozen implementation anchors

The intrinsic ordering semantics are pinned to the already-existing #1284 truth-bearing implementation at commit:

`312b1b718ae105813de242355142a74e7d377d65`

and source:

`orbittrace_topomodal_sparse_recovery_v1/run_development.py`

Git blob:

`752df8212ce601227f6e9170b0fe994ba06b515d`

The future implementation may refactor that source only as required to inject the already-frozen RNG graph. Before truth opens, a zero-label audit must prove that, when supplied the original full radius graph, the reconstructed candidate memberships/order are exact byte-identical to the pinned #1284 source on all eight frozen subsets.

The exact RNG graph implementation must be byte-pinned to the first technically valid zero-label structural run; no graph repair after a scientific structural outcome is allowed unless the structural run was itself an engineering no-result before any diagnostic metric.

## 3. Frozen subsets

Use exactly:

- denominator `128`, buckets `0,1,2,3` (~5.8k events);
- denominator `1024`, buckets `0,1,2,3` (~0.7k events).

Identity rule:

`uint64_be(SHA256('ORBITTRACE_SCALE_STRESS_V1|' + event_id)[0:8]) % denominator == bucket`.

No other thinning level, bucket, salt, or replicate is authorized.

## 4. Immutable prelabel boundary

For all eight subsets, before shower truth is loaded, serialize and SHA-256 seal:

- exact event-ID universe/order;
- physical coordinates/hash;
- original radius-neighborhood/density hashes;
- RNG graph edge/member hashes and pruning counts;
- complete support>=4 hierarchy memberships;
- every intrinsic ranking field;
- final successor candidate order;
- exact recurrent-EOM comparator memberships/order;
- equal candidate budget `K` for each panel;
- source/input/runtime hashes;
- firewall fields.

The evaluator may not reconstruct, alter, rerank, merge, split, or regenerate candidates after truth opens.

## 5. Equal-budget comparison

For each panel set

`K = min(number of successor candidates, number of recurrent-EOM candidates)`.

Evaluate the top `K` candidates from each frozen order.

Candidate-budget sufficiency is reported. If the successor has fewer candidates than recurrent-EOM on any panel, the equal-budget comparison still uses `K`, but the relevant recovery/nonloss gates remain unchanged and cannot be relaxed.

## 6. Truth metrics

Use the exact already-frozen #1284 sparse-recovery evaluator semantics.

For every method/panel report:

- qualified known-shower matches;
- recovered known showers at budgets 25, 50, 100, and 500 (capped by `K`);
- mean reciprocal rank of first qualifying candidate per eligible shower;
- top-100 dominant-candidate precision;
- median fragmentation among top-500 qualifying matches.

Aggregate separately across the four fine (`d=1024`) and four coarse (`d=128`) panels.

## 7. Frozen ten promotion gates

`PASS_RNG_TOPOMODAL_RECOVERY_V1` requires **all ten**:

### Fine sparse scale (`d=1024`)

1. successor qualified total strictly greater than recurrent-EOM;
2. successor qualified count nonlower in at least 6 of the 8 annual panel evaluations;
3. successor mean MRR not lower;
4. successor mean top-100 dominant precision not lower;
5. successor mean median-fragmentation not higher.

### Coarse sparse scale (`d=128`)

6. successor qualified total not lower than recurrent-EOM;
7. successor qualified count nonlower in at least 6 of the 8 annual panel evaluations;
8. successor mean MRR not lower;
9. successor mean top-100 dominant precision not lower;
10. successor mean median-fragmentation not higher.

The structural zero-label PASS is a prerequisite but is not substituted for any truth gate.

Any failed gate returns `FAIL_RNG_TOPOMODAL_RECOVERY_V1` and permanently closes the exact architecture.

## 8. No rescue

After the first technically valid truth outcome, do not change:

- RNG inequality/tie semantics;
- graph radius or physical scales;
- density field;
- support floor;
- ToMATo hierarchy;
- root/finite ordering semantics;
- any intrinsic ordering field or tie rule;
- equal-budget rule;
- metric;
- subset/salt;
- gate.

No result-informed rerank, blend, pruning, alternative proximity graph, or threshold is authorized.

## 9. Firewall

Protected solar longitude `[20.0,55.0]` remains excluded inclusively before geometry. OrbitTrace target information/events, SonotaCo, ASFN/EFN event rows, AMOS, MAARSY, and DMS remain inaccessible during this GMN development test.