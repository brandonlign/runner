# OrbitTrace density-synchronous global FOSC exclusion-margin v1 — repaired frozen protocol

## Status and repair provenance

This protocol supersedes only the pre-GMN mathematical definition in original protocol blob `e80458fcb6e12e40f0f78c3d03a09780f0709054`.

The original zero-data synthetic audit failed before any scientific data access because the local parent-vs-descendant gap was incorrectly described as the global objective loss when a selected node is forbidden. That failure is preserved in `THEORY_REPAIR_FREEZE.md`:

- run `31862832013`;
- artifact `9241107440`;
- digest `sha256:67e071548652890c3dc7d6e239809f5dbafa23f3ba3c7c3d36ff050e5ae6f3c0`;
- exact counterexample: selected node 15 had local gap `6` but true global forced-exclusion loss `1` because rejected ancestor 12 could switch on.

No GMN catalogue, GMN scientific labels, SonotaCo, AMOS, ASFN, EFN, MAARSY, DMS, OrbitTrace target information, or protected-region event was accessed by that audit. Therefore this is a pre-science mathematical correction, not an outcome-informed rescue.

This repaired protocol is frozen before the first technically valid scientific outcome.

## Scientific role

Direct ranking-only successor to the binding density-synchronous recurrent-EOM HDBSCAN v1 champion from PR #1263.

The following remain **exactly #1263**:

- pooled target-excluded GMN 2022+2023 corpus;
- GEO6 representation;
- HDBSCAN hierarchy and parameters;
- density-synchronous node objective `S_sync`;
- FOSC/EOM selected-node set;
- event memberships and candidate universe;
- candidate family IDs;
- evaluator and truth timing.

The sole scientific change is candidate ranking by the exact global FOSC objective loss caused by forbidding each already-selected node.

A full-GMN PASS is insufficient for promotion by itself. This version must also pass the already-frozen deterministic 10-fold GMN train-robustness criterion before it can reach a separately frozen SonotaCo 2013/2014 validation.

## Scientific firewall

- protected solar longitude `[20°,55°]` is removed inclusively before scientific use;
- no OrbitTrace target information/events;
- no SonotaCo 2013/2014 access during method development;
- no AMOS access;
- no ASFN or EFN access;
- no MAARSY or DMS scientific access;
- no external-survey shopping;
- first technically valid endpoint for each frozen gate is binding;
- no post-result score blend, normalization, threshold, exponent, alternate margin, tie rule, parameter or rescue variant.

## Exact direct parent

Binding #1263 execution head:

`182f07ade6bb5d4be2c80b88df9216bb2d6eee2d`

Pinned parent scientific sources:

- density-synchronous kernel blob `587a304f451e41b9503272f1783a6c6ebb295000`;
- recurrent-EOM kernel blob `30ac3fa3bc47910370df528fcf3ae8ecb6277b47`;
- #1263 GMN runner blob `157813ca331165180a6d20aa71bfc78d5984396f`.

Binding #1263 full-GMN result:

- run `31852836840`;
- artifact `9238142199`;
- digest `sha256:918992863d019baf3bbb5eadd83ecaa32cabea3d9bd7d9d43735b26474e8ed60`;
- exact candidate count `2,094`;
- exact condensed-tree SHA-256 `f708b61d925f7b14f999a88b3ce2ff106a6417624a9d02b48174a8d64ad0ec25`;
- exact #1263 ordered-membership SHA-256 `e8f374ad03e7072463118ee6440a54d96d11e3aab17202cfe336f866530224f2`;
- 2022 @50/@100 `45/89`, precision `0.7873334042799703`, MRR `0.022505373166085363`, fragmentation `1.0`;
- 2023 @50/@100 `46/90`, precision `0.7898245986099988`, MRR `0.02203028490649908`, fragmentation `1.0`.

PR #1265 separately showed that #1263's strict full-data @100 gain did not survive the frozen aggregate 10-fold perturbation criterion. That does not rewrite #1263's PASS, but it motivates requiring robustness from any ranking-only challenger.

## Motivation independent of scientific outcomes

FOSC/HDBSCAN flat extraction solves an additive optimization problem on the condensed hierarchy. #1263 ranks its selected nodes by raw density-synchronous node quality `S_sync(C)`. That value measures recurrent persistence accumulated by C, but does not measure whether C is **indispensable to the globally optimal flat clustering**.

A selected node can be nearly replaceable because, when it is removed, descendants or a previously rejected ancestor can recover almost the same total objective. Another selected node can cause a much larger loss when forbidden. The latter has a larger exact optimization margin even if its raw `S_sync` is smaller.

The new statistic is therefore an exact counterfactual of the already-frozen #1263 FOSC optimization. It introduces no fitted parameter and does not modify the clustering itself.

The construction is motivated by the FOSC optimization framework and by recent work on alternative globally optimal/local-cut FOSC solutions (FOSC-X, Simpson & Campello 2026, arXiv:2606.18972). This method does **not** use FOSC-X top-M extraction and introduces no M; it asks one deterministic counterfactual question per already-selected #1263 node.

## Exact statistic: global forced-exclusion FOSC margin

Let `S(C)` be #1263's exact density-synchronous scalar objective for cluster node C.

Let `children(C)` be C's immediate **cluster** children in the condensed tree (`child_size > 1`).

First compute the unrestricted optimal subtree value:

`O(C) = max(S(C), sum_{D in children(C)} O(D))`.

For a cluster leaf the child sum is zero.

HDBSCAN/FOSC tie semantics are inherited exactly: the parent wins when `S(C) >= child_sum`; only a strictly larger child solution rejects C.

Let R be the HDBSCAN root. Because `allow_single_cluster=False`, R itself is never eligible. The unrestricted global objective is therefore

`F* = sum_{D in children(R)} O(D)`.

Point children contribute no cluster-objective term.

For each final #1263-selected node C, define `F*_{-C}` as the exact optimum under the **sole** additional constraint that C itself may not be selected. All descendants and all ancestors other than the excluded root remain eligible under the original #1263 objective and tie semantics.

Compute `F*_{-C}` deterministically:

1. At C, force the subtree value to its unrestricted optimal descendant cut:
   `E_C(C) = sum_{D in children(C)} O(D)`.
2. Follow C's unique cluster-parent path upward.
3. At each non-root ancestor A whose path child is P, recompute
   `E_C(A) = max(S(A), E_C(P) + sum_{D in children(A), D != P} O(D))`.
4. At the excluded root R, do **not** compare against `S(R)`. Instead
   `F*_{-C} = E_C(P_R) + sum_{D in children(R), D != P_R} O(D)`,
   where `P_R` is the affected root-child branch.

Finally define

`G_FOSC(C) = F* - F*_{-C}`.

`G_FOSC(C) >= 0` up to the existing `1e-12` numerical audit tolerance.

Interpretation: this is the exact additive density-synchronous FOSC objective loss caused by forbidding selected cluster C while allowing the **entire remaining hierarchy to re-optimize**, including switching on a previously rejected ancestor.

No division by `S(C)`, member count, lifetime, annual EOM, ordinary stability or any other quantity is allowed. No logarithm, ECDF, percentile, normalization, exponent or clipping is allowed except mapping a numerical value in `[-1e-12,0)` to zero after the theorem audit confirms the tolerance condition.

The original local gap `S(C)-sum O(children(C))` is explicitly **not** an eligible score for this version.

## Required zero-data theorem audit

Before any GMN workflow may be registered or activated, a synthetic-only audit must prove:

1. unrestricted dynamic-programming optimum agrees with exhaustive brute-force flat-cut enumeration on preregistered synthetic trees;
2. `G_FOSC(C)` equals exhaustive brute-force global objective loss for **every selected node** when that node is forbidden;
3. the ancestor-switch counterexample from failed run `31862832013` is repaired exactly (`G=1`, not local gap `6` for node 15);
4. root exclusion matches `allow_single_cluster=False`;
5. FOSC tie semantics remain parent-favoring;
6. positive scaling of the complete objective scales every `G_FOSC` by the same factor and preserves the margin order;
7. ranking by `G_FOSC` changes only order, never identity or membership;
8. no scientific data source is reachable from the audit.

A synthetic failure is an engineering/theory no-result and cannot authorize GMN.

## Candidate universe and memberships

Before scientific truth access, the binding GMN runner must reproduce exact #1263:

- condensed-tree SHA `f708b61d925f7b14f999a88b3ce2ff106a6417624a9d02b48174a8d64ad0ec25`;
- identical density-synchronous quality map and selected-node tuple;
- exactly `2,094` candidate memberships;
- exact #1263 ordered-membership SHA `e8f374ad03e7072463118ee6440a54d96d11e3aab17202cfe336f866530224f2` before reranking;
- identical family IDs and membership multiset.

Any mismatch is a technical/scientific invalidity, not a new method result.

## Sole ranking change

#1263 ranking:

1. descending `S_sync`;
2. descending ordinary HDBSCAN stability;
3. descending member count;
4. ascending deterministic family ID.

Successor ranking:

1. descending `G_FOSC`;
2. descending `S_sync`;
3. descending ordinary HDBSCAN stability;
4. descending member count;
5. ascending deterministic family ID.

Secondary keys only make exact ties deterministic. There is no rank fusion with #1263, recurrent-EOM, v31, DBCV, GLOSH, annual quality or a learned score.

Mechanism activity requires the complete successor order to differ from #1263.

## Gate A — binding full-GMN development superiority

Use the exact #1263 target-excluded GMN 2022+2023 corpus, evaluator and truth timing. Complete #1263 and successor orders plus all `G_FOSC` values must be persisted before the already-exposed GMN training labels are opened.

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

PASS token: `PASS_DENSITY_SYNC_FOSC_MARGIN_V1_GMN_DEVELOPMENT`.

FAIL token: `FAIL_DENSITY_SYNC_FOSC_MARGIN_V1_GMN_DEVELOPMENT`.

Any FAIL permanently closes v1 and blocks Gate B and SonotaCo.

## Gate B — preregistered 10-fold train robustness

Gate B is eligible **only after Gate A PASS**. It uses exactly the deterministic perturbation already frozen in PR #1265:

`fold(event_id) = int.from_bytes(SHA256(UTF8(event_id))[0:8], 'big') mod 10`.

For each fold `f=0..9`, remove that hash bucket from both years, fit the unchanged pooled HDBSCAN hierarchy, reconstruct exact #1263 density-synchronous extraction, then rerank the exact same selected candidates by `G_FOSC`.

Across all 20 year-fold panels, successor robustness passes iff all are true relative to exact #1263 on those same folds:

1. total recovered@50 is not lower;
2. total recovered@100 is **strictly higher**;
3. mean top-100 dominant precision is not lower;
4. mean MRR is not lower;
5. median top-500 fragmentation is not higher;
6. global exclusion-margin ranking is active in at least one fold.

No fold weighting/removal, alternate hash, holdout fraction, salt, seed, bootstrap, threshold or rescue is allowed.

PASS token: `PASS_DENSITY_SYNC_FOSC_MARGIN_V1_GMN_ROBUSTNESS`.

FAIL token: `FAIL_DENSITY_SYNC_FOSC_MARGIN_V1_GMN_ROBUSTNESS`.

Only Gate A PASS + Gate B PASS makes this a genuine challenger to #1263 and authorizes freezing a prospective SonotaCo validation protocol under PR #1264. Neither gate authorizes AMOS.

## Failure interpretation and no-rescue rule

If Gate A fails, global FOSC indispensability does not improve fixed-budget GMN recovery enough to replace #1263.

If Gate A passes but Gate B fails, any full-data gain is considered development-sample-sensitive and this version is rejected rather than promoted.

No global-margin/S_sync blend, local margin, relative margin, logarithm, percentile, ECDF, exponent, annual decomposition, top-k-only use, budget-specific ranking, ancestor-depth weighting, alternative forced constraint or other post-result rescue of this version is permitted.
