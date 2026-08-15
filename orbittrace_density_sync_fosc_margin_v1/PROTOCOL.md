# OrbitTrace density-synchronous FOSC decision-margin v1 — frozen protocol

## Status and role

Frozen before implementation and before the first technically valid scientific outcome.

This is a direct successor to the binding density-synchronous recurrent-EOM HDBSCAN v1 champion from PR #1263. It changes **candidate ranking only**. The pooled HDBSCAN hierarchy, density-synchronous node quality, FOSC/EOM selected-node set, event memberships, HDBSCAN parameters, representation, target exclusion, evaluator and candidate universe remain exactly #1263.

Scientific role: permanent target-excluded GMN 2022+2023 TRAIN / DEVELOPMENT only. A passing train result must also pass the already-frozen deterministic 10-fold robustness criterion before this version may proceed to a separately frozen SonotaCo 2013/2014 validation.

## Scientific firewall

- protected solar longitude `[20°,55°]` is removed inclusively before scientific use;
- no OrbitTrace target information/events;
- no SonotaCo 2013/2014 access during method development;
- no AMOS access;
- no ASFN or EFN access;
- no MAARSY or DMS scientific access;
- no external-survey shopping;
- the first technically valid endpoint for each frozen gate is binding;
- no post-result score blend, normalization, threshold, exponent, alternative margin, tie rule, parameter or rescue variant.

## Exact direct parent

Binding #1263 execution head:

`182f07ade6bb5d4be2c80b88df9216bb2d6eee2d`

Pinned scientific sources:

- density-synchronous kernel blob `587a304f451e41b9503272f1783a6c6ebb295000`;
- recurrent-EOM kernel blob `30ac3fa3bc47910370df528fcf3ae8ecb6277b47`;
- #1263 GMN runner blob `157813ca331165180a6d20aa71bfc78d5984396f`.

Binding #1263 full-GMN result:

- run `31852836840`;
- artifact `9238142199`;
- digest `sha256:918992863d019baf3bbb5eadd83ecaa32cabea3d9bd7d9d43735b26474e8ed60`;
- candidate count `2,094`;
- 2022 @50/@100 `45/89`, precision `0.7873334042799703`, MRR `0.022505373166085363`, fragmentation `1.0`;
- 2023 @50/@100 `46/90`, precision `0.7898245986099988`, MRR `0.02203028490649908`, fragmentation `1.0`.

The separate #1265 robustness diagnostic is also binding context: exact #1263 did not achieve a strict aggregate @100 improvement under the deterministic 10-fold 10% event holdouts. This successor therefore must pass a robustness gate as part of promotion.

## Motivation independent of outcome identities

FOSC/HDBSCAN flat extraction is an additive dynamic program over a condensed hierarchy. #1263 ranks its selected clusters by their raw density-synchronous node quality `S_sync(C)`. Raw node quality measures accumulated recurrent persistence, but it does not measure how strongly the FOSC optimization prefers that selected node over the best alternative cut available inside the same subtree.

A selected cluster can therefore have high `S_sync(C)` while being nearly exchangeable, in objective value, with a descendant solution. Conversely, another selected cluster can have a smaller raw quality but be structurally decisive: forbidding that node would incur a large loss in the exact density-synchronous FOSC objective.

The proposed ranking uses this already-defined optimization contrast directly. It introduces no fitted hyperparameter and does not change the hierarchy or selected clustering.

The construction is motivated by the FOSC optimization framework and by recent work extending FOSC to alternative globally optimal/local-cut solutions (FOSC-X, Simpson & Campello 2026, arXiv:2606.18972). The method does not copy FOSC-X top-M extraction and introduces no value of M; it uses the exact local counterfactual already implied by the single optimum dynamic program.

## Sole new statistic: selected-node FOSC decision margin

Let `S(C)` be #1263's exact density-synchronous node quality for cluster node `C`.

Let `children(C)` be the immediate **cluster** children in the HDBSCAN condensed tree (`child_size > 1`). Define the optimal descendant-subtree objective recursively:

`O(C) = max(S(C), sum_{D in children(C)} O(D))`.

For a cluster leaf, the empty child sum is `0`.

The tie semantics are inherited exactly from HDBSCAN/FOSC EOM: `S(C) >= child_sum` selects the parent, matching #1263's current extraction.

For every node `C` selected by #1263's exact density-synchronous FOSC/EOM solution, define

`M_FOSC(C) = S(C) - sum_{D in children(C)} O(D)`.

Because `C` is selected, `M_FOSC(C) >= 0` up to the existing `1e-12` numerical audit tolerance.

Interpretation: `M_FOSC(C)` is the exact additive density-synchronous objective loss incurred by forbidding selected node `C` and substituting the optimal descendant cut within its subtree, while leaving all disjoint selected subtrees unchanged.

No division by `S(C)`, member count, lifetime, annual EOM, ordinary stability or any other quantity is allowed. No clipping except numerical `-1e-12 <= margin < 0` audit normalization to `0` is allowed. No alternate definition is allowed after outcome.

## Candidate universe and memberships

The successor must reproduce #1263 exactly before any truth access:

- identical condensed-tree SHA;
- identical density-synchronous quality map;
- identical selected-node tuple;
- identical `2,094` candidate memberships;
- identical family IDs and candidate membership multiset.

If any membership or selected node changes, the run is an engineering/scientific invalidity, not a new result.

## Sole ranking change

#1263 ranking:

1. descending `S_sync`;
2. descending ordinary HDBSCAN stability;
3. descending member count;
4. ascending deterministic family ID.

Successor ranking:

1. descending `M_FOSC`;
2. descending `S_sync`;
3. descending ordinary HDBSCAN stability;
4. descending member count;
5. ascending deterministic family ID.

The secondary keys are inherited only to make ties deterministic. There is no rank fusion with #1263, recurrent-EOM, v31, DBCV, GLOSH, annual quality or any learned score.

Mechanism activity requires the complete successor order to differ from #1263.

## Gate A — binding full-GMN development superiority

Use the exact #1263 target-excluded GMN 2022+2023 corpus, evaluator and truth timing. Candidate order and all margin values must be persisted before the already-exposed GMN training labels are opened.

For each year separately, successor must not regress #1263 on:

- recovered@50;
- recovered@100;
- top-100 dominant precision;
- MRR;
- median top-500 fragmentation.

In addition:

- recovered@100 must be strictly higher than #1263 in at least one year;
- mechanism must be active;
- candidate membership universe must be exactly identical to #1263.

Recovered@25, @500 and full-catalogue qualified matches are reporting-only.

PASS token:

`PASS_DENSITY_SYNC_FOSC_MARGIN_V1_GMN_DEVELOPMENT`

FAIL token:

`FAIL_DENSITY_SYNC_FOSC_MARGIN_V1_GMN_DEVELOPMENT`

Any FAIL permanently closes v1 and blocks Gate B/SonotaCo.

## Gate B — preregistered 10-fold train robustness

Gate B is eligible **only after Gate A PASS**. It uses exactly the deterministic perturbation already frozen in PR #1265:

`fold(event_id) = int.from_bytes(SHA256(UTF8(event_id))[0:8], 'big') mod 10`.

For fold `f=0..9`, remove that hash bucket from both years, fit the unchanged pooled HDBSCAN hierarchy, reconstruct exact #1263 density-synchronous extraction, then rank the exact same selected candidates by `M_FOSC`.

Across all 20 year-fold panels, successor robustness passes iff all are true relative to exact #1263 on those same folds:

1. total recovered@50 is not lower;
2. total recovered@100 is **strictly higher**;
3. mean top-100 dominant precision is not lower;
4. mean MRR is not lower;
5. median top-500 fragmentation is not higher;
6. margin ranking is active in at least one fold.

No fold weighting/removal, alternate hash, holdout fraction, salt, seed, bootstrap, threshold or rescue is allowed.

PASS token:

`PASS_DENSITY_SYNC_FOSC_MARGIN_V1_GMN_ROBUSTNESS`

FAIL token:

`FAIL_DENSITY_SYNC_FOSC_MARGIN_V1_GMN_ROBUSTNESS`

Only Gate A PASS + Gate B PASS makes this a genuine challenger to #1263 and authorizes freezing a prospective SonotaCo validation protocol under PR #1264. Neither gate authorizes AMOS.

## Failure interpretation

If Gate A fails, raw selected-node FOSC decisiveness does not improve fixed-budget GMN recovery enough to replace #1263.

If Gate A passes but Gate B fails, any full-data gain is considered development-sample-sensitive and this version is rejected rather than promoted.

No margin/S_sync blend, relative margin, logarithm, percentile, ECDF, exponent, annual decomposition, top-k-only use, budget-specific ranking, or other post-result rescue of this version is permitted.
