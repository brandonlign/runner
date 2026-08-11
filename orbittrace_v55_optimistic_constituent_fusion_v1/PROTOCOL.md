# OrbitTrace v55 optimistic-constituent fusion v1

## Scientific role

This is a separately frozen **exposed-development successor** after binding v52 failure and the independent mechanism PASSes #1157 and v54.

The binding state is:

- exact v31 remains the parent and wins both Sugar panels but loses both HDB literature pair gates;
- v52 lexicographic minimax/worst-constituent fusion is permanently rejected at 2/4;
- #1157 `PASS_V31_INTERNAL_V19_SUPPRESSION_DIAGNOSTIC` showed that recoverable-but-missed HDB groups tend to have their best fixed candidate ranked materially better by immutable v19 than by the local/diversity constituent in both exposed years;
- v54 `PASS_V54_V19_ADVANTAGE_FULL_UNIVERSE_DIAGNOSTIC` then confirmed across the complete fixed 229-family HDB universe that the natural condition `v19_rank < local_rank` has a strictly higher annual recoverability fraction than the complementary class in both 2013 and 2014.

v55 tests exactly one parameter-free consequence of those two independently frozen mechanisms: the **optimistic constituent** order. It does not tune v31, v19, or v52 and does not search fusion weights.

SonotaCo 2013/2014 remains `EXPOSED_DEVELOPMENT_ONLY`, not external validation.

## Immutable inputs

The successor may use only:

1. binding v51 rank-vector run `31493423814`, artifact `9101972590`, artifact digest `sha256:56258a0be52d83c0d6dbfcffdb9fd9a2c6b73587ba8d92d7bdccdef9729868c9`;
2. v51 vector SHA-256 `5f20a8bedb6e7b8d6c06d66e45d5037057a9853ded35a2b360333d6ea5e2c4cc`, canonical SHA-256 `0e13b3f9e6b791a13a3e90d853f8704573b1264dffcb67236e6423491ad70020`, and v51 result SHA-256 `fef1d2c5bb83748de5c5511615915e76ce6fcd0801afbddb0e01bab09b9ab76d`;
3. binding v54 run `31497952186`, artifact `9103776799`, artifact digest `sha256:db9bd25f8d8cea942f5db5dac655227ddb2e5c413a5f6ce7893e28abc03b795e`, split SHA-256 `3a065240c07e2abd0e0a6b9d0b712fd21009096c06a714237390de22ea483667`, split canonical SHA-256 `b55b86574c45a509c1da3f34b7c00957a4e1926fe11e3c3fa9badff772b3d5f2`, and result SHA-256 `4cea3be96bd643585da4754c6ef039f454d3f83fcbdf7329ec4b1b39ff7d9159`;
4. exact v31 parent source blob `917e3cd6f9310ca1282e0efa58ed0924d03ed4da`;
5. immutable #839 ranker source SHA-256 `dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990`;
6. immutable #950 pretruth payload artifact `9074742322`, ZIP SHA-256 `d940fa255804866f14bc34b1d72467d17adddcfb7d82c954ed5a8d1668aa307a`;
7. immutable exposed SonotaCo truth artifact `9069505548`, ZIP SHA-256 `cdea3297c234b0b3a8f09c2208649c8607bb3e9a9004d299f6dcc18536ebb797`.

v54 is an **authorization mechanism only**. Its annual recoverability fractions, annual outcome labels, and any outcome-bearing family identity must not enter the v55 order.

## Sole scientific change

Sugar remains **exact v31 unchanged**.

For HDB, take only the two complete exact-v31 constituent permutations already captured outcome-free by v51:

- `local_rank`: exact strict-OOF local-geometry order after the inherited #839 diversity pass;
- `v19_rank`: immutable exact-v19 order.

Replace v31's final equal rank-sum with one symmetric lexicographic optimistic-constituent order:

`(min(local_rank, v19_rank), max(local_rank, v19_rank), family_id)` ascending.

Interpretation: a candidate is prioritized first by the stronger of the two already-frozen independent constituent ranks; the weaker constituent is used only as the deterministic second key; family ID is the final stable tie-break.

There is no coefficient, interpolation, threshold, rank gap, quantile, top-k, budget, rank window, year-specific rule, route-specific coefficient, or identity correction.

This rule is the canonical symmetric opposite of the already-rejected v52 minimax rule, but v55 is **not a rescue of v52**. It is separately motivated by #1157 and v54, both of which were obtained after v52 and showed that the v19-favored side of constituent disagreement contains recoverability signal that minimax suppresses.

## Complete truth-blind order freeze

Before current v55 panel truth is loaded, reconstruct exact v31 HDB equal-rank-sum order from the v51 constituent ranks and require SHA-256:

`85ac3f29a443c35b3812cf28c99ef13474fc3e0455458e20b41cec64d942073d`.

Then construct the sole v55 HDB order above and require full order SHA-256:

`9cb7cf0597394f7c253452ed5788eb0dce6bcc6ad6442647ecb54dc31d438132`.

Truth-blind structural consequences fixed before outcome:

- family universe: `229`;
- moved global positions versus exact v31: `221`;
- moved up: `104`;
- moved down: `117`;
- top-9 membership substitutions versus exact v31: `4`;
- top-11 membership substitutions versus exact v31: `4`.

These prefix counts are descriptive structural consequences of the complete order only. They do not define or alter the rule. The workflow must fail closed if any count or order hash changes.

The complete order freeze must explicitly assert:

- current v55 panel outcome not accessed;
- annual own-family F1 not used for the order;
- recoverability labels not used for the order;
- v54 annual fractions/identities not used for the order;
- literature budgets not used for the order;
- no boundary identity, component, quality, topology, cross-route, or oracle signal used;
- no threshold, weight, alternative tie rule, top-k, or rank window selected.

## Parent reproduction and evaluation

Only after the complete v55 HDB order is frozen may immutable #950 and exposed SonotaCo truth be restored.

The evaluator must first reproduce exact v31 controls:

- Sugar 2013 `0.2719801488280529 / 16`;
- Sugar 2014 `0.31529041952487225 / 17`;
- HDB 2013 `0.14888037368183737 / 9`;
- HDB 2014 `0.15198123772301594 / 9`.

Require exact parent properties: strict whole-shower OOF, 71D fold-training z-score, Euclidean k=1, annual margin `d_nonpositive-d_positive`, annual `min`, #839 diversity `lambda=0.8`/`scale=1.0`, immutable v19, and one equal rank-sum.

Then:

- Sugar panel results remain exact v31;
- HDB fixed #950 memberships are reordered by the single frozen v55 HDB permutation;
- evaluate once with the existing exact SonotaCo literature evaluator and already-fixed comparator budgets.

PASS requires **all four** literature pair gates:

`candidate_macro_f1 > literature_macro_f1` AND `candidate_recovered_f1_gt_0_5 >= literature_recovered_f1_gt_0_5`

for Sugar 2013, Sugar 2014, HDB 2013, and HDB 2014.

The first technically valid result is binding.

## No rescue

If v55 fails, permanently close this exact optimistic-constituent architecture. Do not retry with:

- v19-only ranking;
- asymmetric positive-v19-advantage promotion;
- mean/sum/product with minimum rank;
- weighted or soft minimum;
- reciprocal-rank fusion;
- alternate second key;
- rank-gap thresholds;
- quantiles;
- top-k/rank-window/budget/year rules;
- identity corrections;
- mixing component/quality/topology/cross-route signals;
- post-result second searches.

Any future successor would need an independently motivated mechanism and separate pre-result freeze.

## Firewall

Protected OrbitTrace solar longitude `20°–55°` remains inaccessible. Do not access OrbitTrace target information or target-region events. Do not access MAARSY or DMS scientifically. Every output must assert these conditions and `SonotaCo = EXPOSED_DEVELOPMENT_ONLY`.