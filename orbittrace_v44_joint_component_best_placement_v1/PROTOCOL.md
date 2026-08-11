# OrbitTrace v44 joint-gated component-best placement v1

## Scientific role

Separately frozen exposed-SonotaCo successor after exact v31, failed v42/v43, diagnostic #1113, and full-universe refinement no-go #1121.

The fixed 229-family HDB universe already has sufficient tiny-budget headroom (#1050/#1071). Exact v31 remains the strongest genuine all-route method at 2/4. The recent sequence localizes the remaining failure more narrowly:

- #1091/#1098 support the exact truth-free HDB gate `(quality_rank < v31_rank) AND component_opportunity`, but the gate is broad at 60/229 candidates.
- v42 used immutable quality rank as the placement coordinate inside that gate and failed badly on HDB (`9 -> 7` recoveries in both years).
- v43 used a conservative conjunctive support key and produced no top-budget replacements, returning exactly to v31.
- #1113 then tested placement directly, without evaluating any total order, and found that **lower frozen `component_best_v31_percentile` is strongly associated with recoverability inside the unchanged 60-family joint gate** at both family and diagnostic-group levels in both years.
- #1121 showed that adding the categorical direct-crossroute sign does not meaningfully refine the full-universe gate: it removes only 2/60 families and zero strict groups, so exact three-way categorical refinement is closed.

v44 therefore tests exactly one successor implied by #1113: preserve the original #1098/#1091 joint gate, but replace v42's failed quality-rank placement coordinate with the independently supported frozen component-best exact-v31 percentile. This is **not** an interpolation between v42 and v43 and does not tune promotion strength.

SonotaCo 2013/2014 remains **EXPOSED DEVELOPMENT ONLY**.

## Immutable scientific parents

v44 reuses without scientific alteration:

- immutable #950 71D pretruth features and fixed family memberships;
- exact v31 strict whole-shower OOF local-geometry margin ranking;
- exact #839 diversity `(lambda=0.8, scale=1.0)`;
- exact equal rank-sum with v19 already inside v31;
- exact #1064 radius-1 Sugar↔HDB graph and #1072 connected components;
- immutable pre-SonotaCo #839/#853 HDB quality order **only to define the already-frozen binary joint gate**;
- exact fixed candidate generation/memberships;
- exact #854/v22-v24 equal-budget one-to-one literature evaluation;
- exact literature budgets and pair-gate definition.

The pretruth graph must reproduce SHA-256 `2f25aa7d9af1df0a350c034b2280a790c3869a7775bf6d7063d0d1e4cc802b25` and component identity SHA-256 `c1b80484502907ad19e0d51d8d48d364f3bf7a27e17576e073fe86ae44f499cd` before evaluation truth.

## Frozen authorizing diagnostics

### Gate authorization

Require exact #1091 result:

- run `31456963941`;
- artifact `9088402091`;
- artifact digest `sha256:d1943f629964633f44e154252a225f7171c380674ae6e60e5fcbbd3f8b890dd7`;
- result SHA-256 `2edb949dbab2d7cbf6ed5e808e2a049116eb0934b25b356572463b615d730842`;
- verdict `PASS_V31_QUALITY_COMPONENT_JOINT_SIGNAL_DIAGNOSTIC`.

This fixes the gate as:

`joint = (quality_rank < exact_v31_rank) AND (component_best_v31_percentile < own_hdb_v31_percentile)`.

### Placement authorization

Require exact #1113 binding result:

- run `31458734952`;
- artifact `9088994714`;
- artifact digest `sha256:5bddfbe4abda60006757561d4c6477102317e02f5fb9555330e0b62eaf3353df`;
- result SHA-256 `939f4288a5f0d2de84ef566bb93713da664230deb65777c422795c93fba10c6d`;
- verdict `PASS_V42_JOINT_COMPONENT_PLACEMENT_DIAGNOSTIC`;
- fixed joint population `60`;
- placement statistic `component_best_v31_percentile from frozen #1098 signal; lower is better`;
- placement direction supported at family and diagnostic-group levels in both 2013 and 2014;
- no rank/order/selector/replacement/successor evaluated in #1113.

#1113's result is diagnostic authorization only. Its truth-aware rows or identities may not be used by v44.

## Exact v31 controls

Before accepting a v44 outcome, reproduce exact v31:

- Sugar 2013: `0.2719801488280529 / 16`;
- Sugar 2014: `0.31529041952487225 / 17`;
- HDBSCAN 2013: `0.14888037368183737 / 9`;
- HDBSCAN 2014: `0.15198123772301594 / 9`.

Any mismatch is an engineering/provenance failure, not a scientific v44 outcome.

## Sole v44 scientific change

Let each route's exact v31 fused total order be fixed. For HDB with `N=229`, define

`p_v31(i) = (rank_v31(i)-1)/(N-1)`.

For every exact frozen #1072 connected component `C`, define the same component-best statistic already frozen in #1098/#1113:

`p_component(C) = min(normalized exact-v31 percentile of every Sugar/HDB member of C)`.

For HDB family `i` in component `C(i)`, define the exact pre-existing gate:

`quality_suppressed(i) = quality_rank(i) < rank_v31(i)`

`component_opportunity(i) = p_component(C(i)) < p_v31(i)`

`joint(i) = quality_suppressed(i) AND component_opportunity(i)`.

The sole v44 placement key is:

`key_v44(i) = p_component(C(i))` if `joint(i)` else `p_v31(i)`.

Construct the HDB total order once by ascending:

`(key_v44, p_v31, family_id)`.

Sugar is **exact v31 unchanged**.

This is the entire scientific successor. No quality percentile/rank enters placement after the binary joint gate is formed. No direct-crossroute third sign is used.

## Why this is distinct from failed v42/v43

- v42's joint-positive placement coordinate was **quality rank**; v44 uses **component-best exact-v31 percentile**, independently supported by #1113.
- v43's conservative conjunctive key was designed to require both signals to be simultaneously strong and produced zero budget replacements; v44 does not interpolate with or tune that key.
- v44 uses no coefficient, blend, bonus, cap, threshold, top-k, rank window, or chosen number of corrections.
- #1121's three-way categorical sign is excluded because its full-universe selector-refinement gate failed.

## Binding development gate

Exactly one v44 total order per route is evaluated. The first technically valid v44 result is binding.

For each frozen SonotaCo panel, a win requires both:

- candidate macro-F1 strictly greater than literature; and
- recovered `F1 > 0.5` shower count at least literature.

Development PASS requires **4/4** wins.

If v44 fails, exact joint-gated component-best placement is permanently rejected. Do not rescue it with:

- a component-best threshold;
- top-k/rank-window gating;
- a promotion cap/bonus/coefficient;
- interpolation with own v31 or quality rank;
- component-size or q-calibration terms;
- direct-crossroute sign/magnitude;
- route/year/budget-specific exceptions;
- alternate tie-breaking;
- post-result local search.

If v44 passes 4/4, freeze the exact exposed-development reference only. A PASS is **not external validation** and requires separately protected cross-survey validation before any general superiority claim.

## Explicit non-search commitments

No:

- gate threshold search;
- component-best threshold/search/transformation;
- quality/component blend or fitted weight;
- promotion coefficient/bonus/cap/interpolation;
- top-k, rank-window, or oracle correction count;
- three-way/OR/XOR Boolean alternatives;
- graph/radius/metric/component changes;
- representative search;
- candidate generation/membership changes;
- feature/model/k/scaling/annual-combiner/diversity/fusion/source-quota search;
- truth-aware group identity in ranking;
- post-result second search.

## Firewall

- SonotaCo 2013/2014 is `EXPOSED_DEVELOPMENT_ONLY`.
- Protected OrbitTrace solar longitude `20°–55°` remains inaccessible.
- No OrbitTrace target information or target-region events may be accessed.
- No MAARSY or DMS scientific access is authorized.
- Oracle identities from #1050/#1053/#1071 and truth-aware identities from diagnostics may not enter the v44 score/order.
