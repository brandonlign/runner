# OrbitTrace GMN cross-generator consensus spacing v1

## Status

**PRE-OUTCOME FREEZE.** This protocol defines one target-excluded GMN 2022/2023 successor before its implementation or first result is evaluated.

This experiment is motivated only by target-excluded GMN evidence:

1. PR #1194 established the current representative-share parent on the frozen 4,504-family GMN union at `80/43/22/171` recovered @100/@50/@25/@500 with top-100 dominant precision `0.8075287489258385`, MRR `0.02016666446026534`, and 256 qualified labels.
2. The separately frozen cross-generator diagnostic v1, binding run `31613021560`, established that one exact label-free P19↔P20 relation is a high-purity indicator of duplicate shower fragments: 315/321 truth-qualified edges were same-label (`0.9813084112149533` precision), capturing 85/126 cross-generator duplicate labels (`0.6746031746031746`) and 85/194 all duplicate labels (`0.4381443298969072`).
3. The earlier target-excluded GMN consolidation no-go #843 showed that permanently suppressing families sacrifices too much catalogue recovery. Therefore this successor changes only ordering and **backfills every deferred family**; it does not delete or merge candidates.

No SonotaCo 2013/2014 outcome, identity, rank, budget, comparator, missed family, or post-v60 SonotaCo diagnostic is used to define or select this successor.

## Immutable universe and parent

Use exactly the existing target-excluded GMN 2022/2023 union:

- hard: 226 families;
- P19: 1,075 families;
- P20: 3,203 families;
- total: 4,504 unique families;
- qualified known-shower labels: 256.

The ranking parent is exactly PR #1194 representative-share OOF ranking, including:

- exact #839 34-dimensional feature matrix;
- exact deterministic whole-shower OOF folds;
- exact #839 grouped weights;
- exact #839 ExtraTrees model/hyperparameters;
- exact representative-share target `q_i / sum_G q` for positive shower group `G`, zero otherwise;
- exact #839 diversity `lambda = 0.8`, `scale = 1.0`;
- exact family memberships and tie semantics.

Frozen #1194 scientific source blob: `340f9d54b42ba2500652d7f0a74f22bbd3354f2e`.
Frozen #1194 full-model SHA-256: `acae7fa4b4702e8d3f823defb5f2b3a3e2922b12c3bb07269b6e354316a558cb`.

The exact parent OOF metrics must reproduce before the successor order is interpreted:

- recovered@25 = 22;
- recovered@50 = 43;
- recovered@100 = 80;
- recovered@500 = 171;
- top-100 dominant precision = `0.8075287489258385`;
- MRR = `0.02016666446026534`;
- qualified matches = 256.

If any parent control differs, execution is a technical no-result and stops before successor interpretation.

## Immutable cross-generator graph

Use exactly the pretruth graph frozen by binding diagnostic run `31613021560`:

- graph edge count = 698;
- graph file SHA-256 = `1d7ccb41800b222df053e1f8240ceb2c21020ae160e0c6e6b33eda0b546b03ac`;
- canonical edge SHA-256 = `319d1a868d68148221caba82e28ca17b9a7f55b0f1f7b0f1c02a8fc9e5c28bb0`.

An edge exists only between one P19 family and one P20 family when the two families:

1. share at least one exact GMN event ID; and
2. have inherited #839 two-year maximum annual normalized centroid distance `<= 1.0`.

The graph is an immutable input. No distance threshold, event-overlap cutoff, source-specific threshold, P19-P19/P20-P20 edge, Jaccard rule, component closure, graph learned score, or alternate graph may be evaluated in this lane.

## Sole successor: direct-edge first-pass spacing with complete backfill

Let `P` be the exact #1194 representative-share OOF order over all 4,504 families. Let `E` be the exact 698-edge frozen graph.

Construct exactly one successor order as follows:

1. Initialize `accepted = []`, `deferred = []`, and an empty set of accepted family IDs.
2. Scan families once in exact parent order `P`.
3. For family `f`:
   - if **no** already-accepted family `g` satisfies `(f,g) in E`, append `f` to `accepted`;
   - otherwise append `f` to `deferred`.
4. The final successor order is `accepted + deferred`, with `deferred` retaining exact parent relative order.

Consequences fixed in advance:

- every one of the 4,504 families appears exactly once;
- no membership is changed or merged;
- no family is deleted;
- no transitive connected-component closure is formed;
- no representative is scored separately—the earlier #1194 family wins a direct conflict solely because it appeared earlier in the frozen parent order;
- no graph degree, component size, shared-event count, source identity, target label, or confidence value changes the order;
- no top-k budget enters the algorithm;
- complete backfill is mandatory.

This is a conservative test of whether the newly validated high-purity pairwise redundancy relation can improve early catalogue efficiency without repeating the recall loss caused by permanent suppression.

## Evaluation and promotion gate

Evaluate the sole successor on the same target-excluded GMN truth/evaluator used for the exact #1194 OOF control.

PASS requires **all** of the following relative to the reproduced #1194 parent:

- recovered@100 **> 80**;
- recovered@50 **>= 43**;
- recovered@25 **>= 22**;
- recovered@500 **>= 171**;
- top-100 dominant precision **>= 0.8075287489258385**;
- MRR **>= 0.02016666446026534**;
- qualified matches **== 256**.

The first technically valid execution is binding.

A PASS freezes exactly this deterministic graph-spacing rule on top of the already-frozen #1194 model/ranking architecture. It does not authorize a graph search or a different ranking parent.

A FAIL permanently closes **direct-edge first-pass spacing/backfill on this exact graph and #1194 parent**. Do not rescue it with:

- graph radius/overlap changes;
- connected-component closure;
- graph degree/component-size scoring;
- alternate representatives;
- top-k-only suppression;
- source quotas or source-specific rules;
- score bonuses/penalties;
- fusion weights;
- membership merging;
- candidate deletion;
- alternate backfill positions;
- alternate parent rankers;
- post-result threshold or parameter searches.

Any later successor must be separately motivated by new non-SonotaCo evidence and frozen independently.

## Required provenance guards

Before scientific interpretation, execution must verify:

- exact #1194 source and parent control metrics;
- exact P19/P20 prelabel SHA-256 inputs;
- exact frozen graph file SHA-256 and canonical edge SHA-256;
- exact 4,504-family identity set;
- each graph edge joins P19 to P20 only;
- final order is a permutation of all 4,504 parent IDs with no deletion or duplication;
- all protected-data firewall assertions below.

## Protected-data firewall

Throughout this development run:

- protected solar longitude `[20.0, 55.0]` remains excluded before labels, features, folds, scores, graph evaluation, ranking, and endpoints;
- `sonotaco_2013_2014_access = false`;
- `sonotaco_feature_access = false`;
- `target_information_access = false`;
- `target_region_events_accessed = false`;
- `maarsy_scientific_access = false`;
- `dms_scientific_access = false`.

This protocol does not authorize SonotaCo, GMN held-out target access, MAARSY, DMS, or OrbitTrace target-region work.
