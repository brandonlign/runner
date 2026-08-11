# OrbitTrace v45 component-prioritized joint-slot permutation v1

## Provenance and scientific role

This is a **version-only transplant** of the already-frozen pre-result joint-slot protocol at blob `83c6b82259cb184e312aac51f74b525582eabc69` (`orbittrace_v44_component_prioritized_joint_slot_v1/PROTOCOL.md`). That protocol was frozen before the binding result of the concurrently created, scientifically different v44 branch `agent/orbittrace-v44-joint-component-best-placement-v1` was inspected. The version is changed to v45 solely to avoid two incompatible methods sharing the v44 label. **The candidate rule is unchanged.**

The frozen basis remains:

- exact v31 as parent;
- #1091/#1098 exact 60-family HDB joint condition `quality_suppressed AND component_opportunity`;
- v42 rejected because full quality-rank placement caused broad spillover;
- v43 rejected because it preserved exact v31 top-9/top-11 HDB membership and therefore had no boundary leverage;
- #1116 rejected equal quality/component rank-sum priority;
- #1113 passed component-placement direction within the exact 60-family joint set;
- #1121 rejected direct-crossroute third-sign pruning.

The subsequently observed #1126 Pareto-frontier PASS and the other v44 failure are **corroborating context only**. Their truth-aware recoverability results and family identities do not enter v45 ranking or define any parameter.

SonotaCo 2013/2014 remains `EXPOSED_DEVELOPMENT_ONLY`. A pass is not external validation.

## Immutable identities

Use the unchanged fixed candidate universe and exact v31 machinery. Before exposed truth evaluation reproduce:

- Sugar candidates: 267;
- HDB candidates: 229;
- radius-1 cross-route edges: 2,334;
- graph SHA-256 `2f25aa7d9af1df0a350c034b2280a790c3869a7775bf6d7063d0d1e4cc802b25`;
- connected components: 196 total, 113 non-singleton, 83 singleton;
- component SHA-256 `c1b80484502907ad19e0d51d8d48d364f3bf7a27e17576e073fe86ae44f499cd`.

Preserve the immutable HDB quality order from the #950 pretruth manifest. No candidate, membership, graph, component, quality-order, feature, model, or distance search is authorized.

## Exact v31 parent controls

- Sugar 2013: `0.2719801488280529 / 16`;
- Sugar 2014: `0.31529041952487225 / 17`;
- HDB 2013: `0.14888037368183737 / 9`;
- HDB 2014: `0.15198123772301594 / 9`.

Any mismatch is an engineering/provenance failure and yields no v45 scientific result.

## Authorizing component-placement diagnostic

Pin #1113 technically valid PASS:

- run `31458734952`;
- artifact `9088994714`;
- artifact digest `sha256:5bddfbe4abda60006757561d4c6477102317e02f5fb9555330e0b62eaf3353df`;
- result JSON SHA-256 `939f4288a5f0d2de84ef566bb93713da664230deb65777c422795c93fba10c6d`.

Require `PASS_V42_JOINT_COMPONENT_PLACEMENT_DIAGNOSTIC`, exact 60-family joint population, frozen graph/component identities, and `placement_direction_supported_both_years_both_levels == true`. No truth-aware family/group identity from #1113 enters the rule.

## Sole v45 rule

Sugar remains **exact v31 unchanged**.

For each HDB family `i` define:

- `p_v31(i) = (r_v31(i)-1)/228`;
- `p_q(i) = (r_quality(i)-1)/228` from immutable #950 quality order;
- `p_C(i)` = frozen connected-component best normalized exact-v31 percentile across Sugar/HDB members.

Then exactly:

- `quality_suppressed(i) = [p_q(i) < p_v31(i)]`;
- `component_opportunity(i) = [p_C(i) < p_v31(i)]`;
- `joint(i) = quality_suppressed(i) AND component_opportunity(i)`.

Require exactly 60 joint-positive HDB candidates.

Let `P` be the sorted exact-v31 HDB rank positions occupied by those 60 candidates. Let `J` be those same 60 identities sorted by `(p_C(i), r_v31(i), family_id)`, lower `p_C` first. Construct v45 by assigning `J` one-for-one to positions `P`.

Every position not in `P` retains the **exact same family identity as v31**. No joint candidate may occupy a position that was non-joint under v31. Thus component evidence only permutes identities within the pre-existing joint slots; it is not a global score or promotion key. The rule does not use deployment budgets. Any top-9/top-11 membership change is a consequence, not an input.

## Binding development gate

Evaluate exactly one v45 Sugar order and one v45 HDB order. The first technically valid result is binding.

For each of the four frozen SonotaCo literature panels, a win requires both candidate macro-F1 strictly above literature and recovered `F1 > 0.5` shower count at least literature. PASS requires 4/4.

If v45 fails, this exact joint-slot permutation is permanently rejected. No threshold, top-k, alternate component aggregation, slot expansion, rank window, weight, bonus, year/budget exception, or post-result rescue is authorized.

If v45 passes, freeze only the exact exposed-development reference required for reproduction; no protected validation or external-superiority claim is thereby authorized.

## Explicit non-search commitments and firewall

No component threshold/magnitude transform, quality-suppression magnitude rule, third-sign filter, rank-sum/weighted/product/min/max score, top-k/oracle count, rank window, coefficient/interpolation/bonus/cap, slot expansion, non-joint movement, year/budget rule, Sugar change, alternate quality order, graph/radius/metric/component search, candidate change, feature/model/k/scaling/combiner/diversity/fusion/source-quota search, oracle identity, truth-aware group identity, or post-result second search.

Protected OrbitTrace solar longitude `20°–55°` remains inaccessible. No OrbitTrace target information or target-region events, MAARSY, or DMS scientific access is authorized.
