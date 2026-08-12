# OrbitTrace GMN representative-share oracle diagnostic v1

## Status

**PRE-OUTCOME DIAGNOSTIC FREEZE.** This protocol is frozen before implementation or first evaluation.

This is a target-excluded GMN 2022/2023 diagnostic only. It does not define a new ranking method, detector, threshold, feature, model, or SonotaCo successor.

## Scientific question

The exact #1194 representative-share OOF parent recovers 80 distinct qualified shower labels in the first 100 candidates, while the exact 4,504-family union is known from the earlier target-excluded GMN #838 ceiling diagnostic to contain 256 qualified labels and to admit a truth-aware one-representative-per-label recovery@100 ceiling of 100.

The unresolved question is whether the remaining 80→100 gap is primarily:

1. **target/ordering-objective limitation** — even perfect knowledge of the frozen representative-share target cannot produce substantially better top-budget recovery under the exact fixed diversity operator; or
2. **prediction/separability limitation** — the frozen representative-share target itself supports substantially better ordering, but the exact #1194 OOF estimator/features do not predict it well enough.

The diagnostic answers this by evaluating the already-frozen true targets as oracle scores. It does not search or fit anything.

## Immutable inputs and parent

Use exactly the #1194 target-excluded GMN universe and machinery:

- hard: 226 families;
- P19: 1,075 families;
- P20: 3,203 families;
- union: 4,504 unique families;
- eligible recurrent labels: 355;
- qualified matches: 256;
- exact #839 34D features and family truth semantics;
- exact deterministic whole-shower OOF folds;
- exact #839 grouped weights;
- exact #839 ExtraTrees model;
- exact diversity operator with `lambda = 0.8`, `scale = 1.0` and unchanged tie semantics.

Exact frozen #1194 source Git blob: `340f9d54b42ba2500652d7f0a74f22bbd3354f2e`.

The exact #1194 OOF parent must reproduce before any oracle output is interpreted:

- recovered@25 = 22;
- recovered@50 = 43;
- recovered@100 = 80;
- recovered@500 = 171;
- top-100 dominant precision = `0.8075287489258385`;
- MRR = `0.02016666446026534`;
- qualified matches = 256;
- parent order SHA-256 = `a2f365e0a35fc3e8eef39022128c0444448671ab4c4d4b45c89f718de4505592`.

A mismatch is a technical no-result.

## Frozen oracle scores

Evaluate exactly two truth-aware diagnostic score vectors that already exist inside #1194. Neither is a deployable method.

### A. Representative-share oracle

Use the exact #1194 target vector `y_share` as the score vector:

- for each recoverable shower group `G`, each family receives `q_i / sum_G q`, where `q_i` is exact family target F1;
- each recoverable shower group therefore has total target mass exactly 1;
- negatives/nonrecoverable families receive 0.

Pass `y_share` directly through the exact unchanged #839/#1194 diversity operator and tie semantics. Do not transform, clip, calibrate, temperature-scale, normalize, weight, threshold, source-condition, or perturb it.

### B. Absolute-quality oracle control

Use the exact pre-existing #839 absolute family-quality target `q_abs` as the score vector and pass it through the exact same unchanged diversity operator and ties.

This control asks whether the representative-share target itself improves oracle catalogue efficiency relative to the older absolute-quality target when both are known perfectly.

## Required outputs

For exact #1194 OOF parent, representative-share oracle, and absolute-quality oracle, report:

- recovered@25;
- recovered@50;
- recovered@100;
- recovered@500;
- top-100 dominant precision;
- MRR;
- qualified matches;
- order SHA-256.

Also report, without shower names:

- count of distinct qualified labels in the first 100 for each order;
- count of first-100 family IDs shared between #1194 OOF and representative-share oracle;
- count of qualified labels recovered by both first-100 orders;
- count recovered by representative-share oracle but not #1194 OOF;
- count recovered by #1194 OOF but not representative-share oracle.

No missed-label names or protected target information are required or authorized.

## Interpretation frozen in advance

This diagnostic selects no method and has no tunable gate.

The following statements are purely descriptive and fixed before outcome:

- If representative-share oracle recovered@100 is **greater than 80**, then at least part of the #1194 gap is prediction/separability error rather than an unavoidable consequence of the frozen target/diversity objective.
- If representative-share oracle recovered@100 is **100**, the frozen target/diversity objective itself attains the known #838 top-100 recovery ceiling when perfectly predicted.
- If representative-share oracle recovered@100 is **not greater than 80**, the current representative-share target/diversity objective does not contain demonstrated top-100 headroom over #1194 and should not motivate further estimator-only rescue.
- The absolute-quality oracle is a control only; whichever oracle is better does not by itself authorize a new target or blend.

Any later successor must be independently motivated from this target-excluded GMN diagnostic, separately frozen before evaluation, and checked against already-closed mechanism lanes. No post-result oracle score may be used directly as a deployable ranking signal because it contains GMN truth.

## Prohibited rescue/search

This diagnostic may not evaluate:

- alternate representative-share formulas;
- group exponents or temperatures;
- target clipping/floors;
- alternate diversity lambda/scale;
- alternate tie rules;
- source-specific targets;
- target blends;
- learned calibration;
- feature subsets/interactions;
- model changes;
- oracle-guided top-k rules;
- label-conditioned deployment logic;
- SonotaCo data or outcomes.

## Protected-data firewall

Throughout execution:

- protected solar longitude `[20.0, 55.0]` remains excluded before labels, features, folds, scores, ranking and endpoints;
- `sonotaco_2013_2014_access = false`;
- `sonotaco_feature_access = false`;
- `target_information_access = false`;
- `target_region_events_accessed = false`;
- `maarsy_scientific_access = false`;
- `dms_scientific_access = false`.

This protocol authorizes only target-excluded GMN 2022/2023 development diagnostics.