# OrbitTrace v44 component-prioritized joint-slot permutation v1

## Scientific role

Separately frozen exposed-SonotaCo development successor after the following binding evidence:

- exact v31 remains the stable parent;
- #1091 and #1098 support the exact 60-family HDB joint condition `(quality_suppressed AND component_opportunity)`;
- binding v42 failed 2/4 because full quality-rank promotion caused broad total-order spillover and degraded HDB recovery from 9 to 7 in both years;
- binding v43 failed 2/4 because its conservative shared-support key preserved the exact v31 top-9 and top-11 HDB memberships, giving the method no boundary leverage;
- #1116 rejected equal quality/component rank-sum priority because the 2014 strict-group direction reversed;
- #1113 passed the separately frozen component-placement diagnostic: within the exact 60 joint-positive HDB candidates, lower frozen `component_best_v31_percentile` is associated with recoverability at both family and diagnostic-group levels in both 2013 and 2014;
- #1121's full-universe three-way refinement is rejected: the third sign reduces 60 joint-positive families only to 58 and leaves no joint-only diagnostic-group comparison stratum.

v44 tests one minimal response to the surviving component-placement evidence. It permits component evidence to choose **which joint-positive identity occupies an already-existing joint-positive v31 slot**, while prohibiting any displacement of a non-joint candidate from its exact v31 position.

SonotaCo 2013/2014 remains `EXPOSED_DEVELOPMENT_ONLY`. A pass is not external validation.

## Immutable identities

Use the unchanged fixed candidate universe and exact v31 machinery.

Before exposed truth evaluation, reproduce the exact #1064/#1072 geometry:

- Sugar candidates: 267;
- HDB candidates: 229;
- radius-1 cross-route edges: 2,334;
- graph SHA-256 `2f25aa7d9af1df0a350c034b2280a790c3869a7775bf6d7063d0d1e4cc802b25`;
- connected components: 196 total, 113 non-singleton, 83 singleton;
- component SHA-256 `c1b80484502907ad19e0d51d8d48d364f3bf7a27e17576e073fe86ae44f499cd`.

Preserve the immutable HDB quality order from the #950 pretruth manifest. No candidate, membership, graph, component, quality-order, feature, model, or distance search is authorized.

## Exact v31 parent

Reproduce exact v31 with the unchanged strict-whole-shower OOF 71D local-geometry margin, annual `min`, #839 diversity `lambda=0.8, scale=1.0`, and one equal rank-sum with exact v19.

Required parent controls:

- Sugar 2013: `0.2719801488280529 / 16`;
- Sugar 2014: `0.31529041952487225 / 17`;
- HDB 2013: `0.14888037368183737 / 9`;
- HDB 2014: `0.15198123772301594 / 9`.

Any parent mismatch is an engineering/provenance failure and yields no v44 scientific result.

## Authorizing component-placement diagnostic

Pin #1113 technically valid PASS:

- run `31458734952`;
- artifact `9088994714`;
- artifact digest `sha256:5bddfbe4abda60006757561d4c6477102317e02f5fb9555330e0b62eaf3353df`;
- result JSON SHA-256 `939f4288a5f0d2de84ef566bb93713da664230deb65777c422795c93fba10c6d`.

Require `PASS_V42_JOINT_COMPONENT_PLACEMENT_DIAGNOSTIC`, exact 60-family joint population, frozen graph/component identities, and `placement_direction_supported_both_years_both_levels == true`.

Only its already-preregistered direction is authorization. No truth-aware family/group identity from #1113 enters the v44 candidate rule.

## Sole v44 rule

### Sugar

Sugar remains **exact v31 unchanged**.

### HDB joint condition

For each HDB family `i`, let:

- `p_v31(i) = (r_v31(i)-1)/228`;
- `p_q(i) = (r_quality(i)-1)/228` using the immutable #950 quality order;
- `p_C(i)` be the frozen connected-component best normalized exact-v31 percentile across Sugar and HDB members, using the exact #1064/#1072 component identity.

Define exactly:

- `quality_suppressed(i) = [p_q(i) < p_v31(i)]`;
- `component_opportunity(i) = [p_C(i) < p_v31(i)]`;
- `joint(i) = quality_suppressed(i) AND component_opportunity(i)`.

Require exactly 60 joint-positive HDB candidates. No magnitude threshold enters the gate.

### Joint-slot permutation

Let `P` be the sorted list of the exact-v31 HDB ranks currently occupied by the 60 joint-positive candidates.

Let `J` be the same 60 joint-positive candidate identities sorted by the single priority:

`(p_C(i), r_v31(i), family_id)`

with lower frozen component-best percentile better.

Construct the v44 HDB order by assigning the ordered identities in `J` to the ordered positions in `P` one-for-one.

Every HDB position not in `P` must retain **the exact same family identity as v31**. Therefore:

- no non-joint family may move at all;
- no new slot may be created;
- no joint candidate may occupy a position that was non-joint under exact v31;
- component evidence changes only the identity occupying an already-existing joint slot.

This is a stable permutation, not a global score or promotion key.

The rule is independent of deployment budget. Top-9/top-11 membership changes are consequences of the frozen total order, not inputs to it.

## Binding development gate

Exactly one v44 Sugar order and one v44 HDB order are evaluated. The first technically valid result is binding.

For each of the four frozen SonotaCo literature panels, a win requires:

- candidate macro-F1 strictly greater than the frozen literature comparator; and
- recovered `F1 > 0.5` shower count at least the literature comparator.

Development PASS requires 4/4 panel wins.

If v44 fails, this exact component-prioritized joint-slot permutation is permanently rejected. No in-place threshold, top-k, alternative component aggregation, slot expansion, rank window, weight, bonus, year/budget exception, or post-result rescue is authorized.

If v44 passes 4/4, freeze only the exact exposed-development reference material required for reproducible full-training application. A pass does not authorize protected validation or an external-superiority claim.

## Explicit non-search commitments

No:

- component-percentile threshold or magnitude transform;
- quality-suppression magnitude rule;
- third-sign/cross-route-positive filter;
- equal-ranksum, weighted fusion, product, min/max, geometric mean, or learned score;
- top-k or oracle correction count;
- rank window;
- promotion coefficient, interpolation, bonus, cap, or insertion depth;
- expansion beyond the original joint-positive v31 slots;
- movement of any non-joint HDB family;
- budget- or year-specific rule;
- Sugar modification;
- alternate quality order;
- graph/component/radius/metric search;
- candidate-generation or membership change;
- feature/model/k/scaling/annual-combiner/diversity/fusion/source-quota search;
- oracle identity or truth-aware group identity in ranking;
- post-result second search.

## Firewall

- SonotaCo 2013/2014 is `EXPOSED_DEVELOPMENT_ONLY`.
- Protected OrbitTrace solar longitude `20°–55°` remains inaccessible.
- No OrbitTrace target information or target-region events may be accessed.
- No MAARSY or DMS scientific access is authorized.
