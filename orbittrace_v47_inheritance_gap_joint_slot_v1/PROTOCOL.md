# OrbitTrace v47 inheritance-gap joint-slot permutation v1

## Scientific role

Separately frozen exposed-development successor after binding v44, v45, and v46 failures and the binding post-v46 mechanism diagnostics #1136 and #1139.

The mechanism is now specific and population-level: within the exact #1098 60-family HDB joint-positive set, recoverable families have smaller `inheritance_gap = exact_v31_percentile - component_best_v31_percentile` than nonrecoverable families in both exposed years (#1139), while #1136 showed the concrete boundary failure caused by a large-gap family inheriting very strong component evidence.

v47 makes exactly one scientific change to exact v31:

- Sugar remains exact v31 unchanged;
- the HDB joint-positive population is exactly the same 60 identities frozen by #1098/#1139;
- all 169 non-joint HDB families remain at their exact v31 positions;
- the 60 joint-positive identities are permuted only across the exact v31 positions originally occupied by those same 60 identities;
- inside those fixed slots, priority is exactly `(inheritance_gap, exact_v31_rank, family_id)`, lower first.

This is a parameter-free translation of #1139. No numerical inheritance-gap threshold or boundary identity is used.

SonotaCo 2013/2014 remains `EXPOSED_DEVELOPMENT_ONLY`, not external validation.

## Immutable authorizers and inputs

Before exposed truth is loaded, the workflow must pin:

1. #1098 run `31457923695`, artifact `9088724826`, ZIP SHA-256 `11498b73237304f4175f37910596700ed78284bc6106d0c21dcaab66f97b7978`, signal SHA-256 `a3bcea66b72003a38cc492ea3b182d92cd20f3d1b94a43acbc8a0cbdd465ed07`;
2. #1139 first technically valid run `31488131546`, artifact `9099927842`, ZIP SHA-256 `67960fbd5fd76173da62c6d1823d507c99ee6431862ce56351aa7a194ec81e07`;
3. #1139 diagnostic result SHA-256 `c372b4aac0547198cb6ac4239d604fddc12fdd0f11a930ab39a1e46d01f5e461`, verdict `PASS_V46_JOINT_INHERITANCE_GAP_DIAGNOSTIC`;
4. #1139 60-family vector SHA-256 `145ceb528e66f924c00c152cf2e5a38a2424ffda8f0a39a7eb80680c1bd5dadd`, canonical SHA-256 `0a9eda015ca367697a1dca678a0e8f7d986880fc424a0cbf4573567ab8776672`;
5. immutable #950 pretruth payload artifact `9074742322`, ZIP SHA-256 `d940fa255804866f14bc34b1d72467d17adddcfb7d82c954ed5a8d1668aa307a`;
6. exact #1064/#1072 graph/component identities `2f25aa7d9af1df0a350c034b2280a790c3869a7775bf6d7063d0d1e4cc802b25` and `c1b80484502907ad19e0d51d8d48d364f3bf7a27e17576e073fe86ae44f499cd`;
7. the same immutable #839 ranker source used by the valid v31 lineage.

The #1139 result must assert that no successor, threshold, pairwise dominance rule, boundary rescue, or alternate statistic was evaluated.

## Pre-truth v47 order freeze

Before SonotaCo truth is restored, use only #1098 plus the #1139 frozen vector to construct the complete HDB order:

1. sort all 229 #1098 HDB families by exact `v31_rank` to reproduce exact v31 order;
2. require exactly 60 joint-positive identities and exact identity equality with the #1139 vector;
3. require each vector row's `inheritance_gap` to equal `v31_percentile - component_best_v31_percentile` to numerical tolerance;
4. freeze the sorted list of the 60 joint identities by `(inheritance_gap, v31_rank, family_id)`;
5. replace only the 60 exact v31 joint slots with that sorted list;
6. require every non-joint position to remain byte-for-byte the exact v31 family identity;
7. serialize the full 229-family v47 HDB order, v31 order, exact joint slot set, and their SHA-256 identities before truth.

No SonotaCo outcome truth, annual recoverability, literature budget, #1136 boundary identity, or panel result may enter this order freeze.

## Evaluation

Only after the complete v47 HDB order is frozen may the workflow restore the same immutable exposed SonotaCo truth used by the established evaluator.

Evaluation must reproduce all four exact v31 controls first, then evaluate exactly one v47 order. Sugar must be byte-identical to v31. The HDB order produced by the frozen v31 engine must exactly equal the pre-truth v47 order hash.

PASS requires all four existing SonotaCo literature pair gates to win. The first technically valid result is binding.

## Explicit prohibitions

No inheritance-gap threshold, quantile, clipping, transform, coefficient, bonus, cap, effective component size, component-size rule, second Pareto layer, pairwise dominance rule, top-k, rank window, budget/year exception, route exception, boundary rescue list, hard-coded family identity, alternate joint population, alternate Boolean gate, component representative selection, quality placement, component-best placement, weighted fusion, equal-ranksum, graph/radius/metric/component change, candidate change, feature/model/k/scaling/diversity/fusion/source-quota search, or post-result rescue is authorized.

If v47 fails, this exact inheritance-gap joint-slot rule is permanently closed.

## Firewall

Protected OrbitTrace solar longitude `20°–55°` remains inaccessible. Do not access OrbitTrace target information or target-region events. Do not access MAARSY or DMS scientifically. Every output must assert these conditions and `SonotaCo = EXPOSED_DEVELOPMENT_ONLY`.
