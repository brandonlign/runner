# OrbitTrace v48 self-supported quality-component transfer v1

## Scientific role

Separately frozen exposed-development successor after binding v44, v45, and v46 failures and the binding post-v46 mechanism diagnostics #1136 and #1139.

The completed evidence is specific:

- #1098 fixes the exact 60-family HDB joint-positive population defined by positive immutable quality suppression AND frozen component opportunity;
- #1113 shows lower absolute `component_best_v31_percentile` is associated with recoverability within that fixed population;
- #1136 shows that component evidence can be harmful when a weak family inherits much stronger evidence from another component member;
- #1139 shows population-wide that recoverable joint families have smaller `inheritance_gap = v31_percentile - component_best_v31_percentile` than nonrecoverable families in both exposed years;
- v42 failed because every joint-positive family was allowed to use its quality rank, while v44-v46 failed by translating component evidence into placement without requiring enough own-family support.

A separately frozen v47 gap-only joint-slot branch exists but is **not scientifically executed**. A truth-blind structural audit showed that minimizing inheritance gap alone can prefer a family whose own and component evidence are both poor merely because they are similarly poor. No SonotaCo outcome was used for that no-go decision.

v48 makes exactly one scientific change to exact v31:

- Sugar remains exact v31 unchanged;
- HDB uses the exact existing 60-family #1098 joint gate;
- for each joint-positive family define on the common 229-family percentile scale:
  - `quality_suppression = v31_percentile - quality_percentile`;
  - `inheritance_gap = v31_percentile - component_best_v31_percentile`;
- a joint-positive family is **self-supported** iff `quality_suppression >= inheritance_gap`;
- algebraically, on the same percentile scale, this is exactly `quality_percentile <= component_best_v31_percentile`: the family's own frozen quality evidence must be at least as strong as the component evidence it would borrow;
- only self-supported joint-positive families use immutable `quality_rank` as their promotion key;
- every other HDB family keeps exact `v31_rank` as its key;
- the sole HDB total order is `(promotion_key, exact_v31_rank, family_id)`.

There is no fitted coefficient, numerical cutoff, quantile, rank window, budget rule, or identity list. Equality of the two evidence gains is the parameter-free scientific boundary.

SonotaCo 2013/2014 remains `EXPOSED_DEVELOPMENT_ONLY`, never external validation.

## Immutable inputs and authorizers

Before exposed truth is loaded, pin all of the following:

1. immutable #950 pretruth family payload artifact `9074742322`, ZIP SHA-256 `d940fa255804866f14bc34b1d72467d17adddcfb7d82c954ed5a8d1668aa307a`;
2. immutable #839 ranker source from run `31344632499`, source SHA-256 `dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990`;
3. exact #1064/#1072 graph/component identities `2f25aa7d9af1df0a350c034b2280a790c3869a7775bf6d7063d0d1e4cc802b25` and `c1b80484502907ad19e0d51d8d48d364f3bf7a27e17576e073fe86ae44f499cd`;
4. #1091 run `31456963941`, artifact `9088402091`, ZIP SHA-256 `d1943f629964633f44e154252a225f7171c380674ae6e60e5fcbbd3f8b890dd7`, result SHA-256 `2edb949dbab2d7cbf6ed5e808e2a049116eb0934b25b356572463b615d730842`;
5. #1098 run `31457923695`, artifact `9088724826`, ZIP SHA-256 `11498b73237304f4175f37910596700ed78284bc6106d0c21dcaab66f97b7978`, signal SHA-256 `a3bcea66b72003a38cc492ea3b182d92cd20f3d1b94a43acbc8a0cbdd465ed07`;
6. #1139 first technically valid run `31488131546`, artifact `9099927842`, ZIP SHA-256 `67960fbd5fd76173da62c6d1823d507c99ee6431862ce56351aa7a194ec81e07`;
7. #1139 result SHA-256 `c372b4aac0547198cb6ac4239d604fddc12fdd0f11a930ab39a1e46d01f5e461`, verdict `PASS_V46_JOINT_INHERITANCE_GAP_DIAGNOSTIC`;
8. #1139 frozen 60-family vector SHA-256 `145ceb528e66f924c00c152cf2e5a38a2424ffda8f0a39a7eb80680c1bd5dadd`, canonical SHA-256 `0a9eda015ca367697a1dca678a0e8f7d986880fc424a0cbf4573567ab8776672`.

#1091 and #1139 are authorizers only. They do not supply SonotaCo family identities for ranking.

## Pre-truth v48 order freeze

Before outcome truth is restored:

1. reproduce exact v31 HDB order from #1098 and require order SHA-256 `85ac3f29a443c35b3812cf28c99ef13474fc3e0455458e20b41cec64d942073d`;
2. require exactly 60 joint-positive HDB families and exact identity agreement between #1098 and the #1139 frozen vector;
3. verify every #1139 vector `inheritance_gap` against the #1098 percentiles;
4. compute the self-supported condition exactly as `joint_signal AND quality_percentile <= component_best_v31_percentile`;
5. require the truth-blind self-supported count to be exactly **35**;
6. assign `promotion_key = quality_rank` only to those 35 families, else `promotion_key = v31_rank`;
7. sort all 229 HDB families by `(promotion_key, v31_rank, family_id)`;
8. require the complete frozen v48 HDB order SHA-256 `62041ea9f6e094471a7decf02c71491fc553e93af86a655e21bf1035d0904db6`.

These count/order identities are consequences of the frozen truth-blind vectors, not tuned parameters. No literature budget or SonotaCo recoverability label is used to define or verify the order.

## Evaluation and binding gate

Only after the complete v48 order, exact graph/components, #1091 authorization, and #1139 authorization are pinned may immutable exposed SonotaCo truth be restored.

Evaluation must reproduce the exact v31 parent controls and then evaluate exactly one v48 order. Sugar must remain byte-identical to v31. HDB evaluation order must exactly match the pre-truth v48 order hash above.

The first technically valid v48 result is binding.

PASS requires all four existing SonotaCo literature pair gates to win. Any result below 4/4 permanently rejects this exact v48 rule.

## Explicit prohibitions

No alternate evidence-balance inequality, epsilon/tolerance relaxation, numerical inheritance-gap threshold, quality-suppression threshold, component threshold, quantile, top-k, rank window, budget/year rule, identity exception, v47 gap-only rescue, alternate Boolean gate, OR rule, coefficient, interpolation, bonus, cap, weighted fusion, equal-ranksum, Pareto layer, pairwise dominance, component representative selection, component-best placement, alternate quality order, graph/radius/metric/component change, candidate change, feature/model/k/scaling/diversity/fusion/source-quota search, or post-result second search.

If v48 fails, do not weaken `quality_percentile <= component_best_v31_percentile`, change placement strength, alter the 35-family set, or rescue boundary identities in place.

## Firewall

Protected OrbitTrace solar longitude `20°–55°` remains inaccessible. Do not access OrbitTrace target information or target-region events. Do not access MAARSY or DMS scientifically. Every output must assert these conditions and `SonotaCo = EXPOSED_DEVELOPMENT_ONLY`.