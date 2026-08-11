# OrbitTrace v43 conservative conjunctive rank transfer v1

## Scientific role

Separately frozen exposed-SonotaCo development successor after:

- exact v31 remained the strongest stable base order at 2/4 literature pair wins;
- #1091 showed that recoverable HDB groups missed by v31 are strongly enriched for the exact conjunction `(quality_suppression > 0) AND component_closure_opportunity`;
- #1098 independently extended that exact conjunction to the full fixed 229-family HDB universe and passed its preregistered selectivity gate, while showing the flag is broad (60/229 families) and 2014 family-level enrichment is only marginal;
- binding v42 converted each joint-positive family directly to its immutable quality-rank position and failed 2/4, degrading HDB recovery from 9 to 7 in both years. v42 therefore established a specific placement incompatibility: using only the quality prior for promotion magnitude is too aggressive even when eligibility is jointly corroborated.

v43 tests exactly one canonical conservative placement implied by the conjunction: a joint-positive HDB family may move only as far as **both** independent support signals justify. The promotion key is the worse (larger) normalized percentile of immutable quality support and frozen component support.

SonotaCo 2013/2014 remains `EXPOSED_DEVELOPMENT_ONLY`. A pass is development evidence, not external validation.

## Immutable identities

Use the unchanged fixed candidate universe and exact v31 machinery.

Before any SonotaCo truth is loaded, reproduce the exact frozen #1064/#1072 geometry:

- Sugar candidates: 267;
- HDB candidates: 229;
- radius-1 cross-route edges: 2,334;
- graph SHA-256 `2f25aa7d9af1df0a350c034b2280a790c3869a7775bf6d7063d0d1e4cc802b25`;
- connected components: 196 total, 113 non-singleton, 83 singleton;
- component SHA-256 `c1b80484502907ad19e0d51d8d48d364f3bf7a27e17576e073fe86ae44f499cd`.

Also preserve the immutable HDB `quality_order` from the #950 pretruth manifest. No candidate, membership, graph, component, or quality-order search is authorized.

## Exact v31 parent

After the pretruth geometry is frozen, reproduce exact v31 with unchanged strict whole-shower OOF 71D local-geometry margin, annual `min`, #839 diversity (`lambda=0.8`, `scale=1.0`), and the exact v19 rank fusion.

Required controls:

- Sugar 2013: `0.2719801488280529 / 16`;
- Sugar 2014: `0.31529041952487225 / 17`;
- HDB 2013: `0.14888037368183737 / 9`;
- HDB 2014: `0.15198123772301594 / 9`.

Any mismatch is an engineering/provenance failure and produces no v43 scientific result.

## Sole v43 rule

### Sugar

Sugar remains **exact v31 unchanged**.

### HDB

For HDB family `i`, let:

- `r_v31(i)` = one-indexed exact v31 HDB rank;
- `r_q(i)` = one-indexed immutable pre-SonotaCo quality rank;
- `p_h(i) = (r_v31(i)-1)/228`;
- `p_q(i) = (r_q(i)-1)/228`.

For the already-frozen component `C(i)`, define

`p_C(i) = min((r_route(j)-1)/(N_route-1))`

over every Sugar/HDB member `j` of `C(i)` using the exact v31 route orders.

Retain the exact independently supported Boolean gate:

- `quality_suppressed(i) = [p_q(i) < p_h(i)]`;
- `component_opportunity(i) = [p_C(i) < p_h(i)]`;
- `joint(i) = quality_suppressed(i) AND component_opportunity(i)`.

For a joint-positive family define the **conservative shared-support percentile**

`p_support(i) = max(p_q(i), p_C(i))`.

For a nonjoint family define `p_support(i) = p_h(i)`.

The v43 HDB total order is the deterministic sort by

`(p_support(i), p_h(i), family_id)`.

Because both `p_q` and `p_C` must be strictly better than `p_h` for a joint-positive family, the `max` rule is the furthest promotion simultaneously supported by both independent signals. It cannot promote a family as far as either signal alone when the other signal is weaker. This is the sole scientific change from the failed v42 placement architecture.

No conversion of `p_C` to an integer rank is used; normalized percentiles are compared directly. No interpolation, average, geometric mean, minimum, coefficient, bonus, clipping, threshold, cap, top-k, rank window, or budget/year-specific behavior is allowed.

## Authorizing evidence

Pin the scientific rationale to:

- #1091 first valid run `31456963941`, artifact `9088402091`, result SHA-256 `2edb949dbab2d7cbf6ed5e808e2a049116eb0934b25b356572463b615d730842`;
- #1098 first valid repaired run `31457788803`, artifact `9088683367`, which passed the preregistered full-universe selectivity gate with 60/229 joint-positive HDB families;
- v42 first valid run `31457295276`, artifact `9088524431`, which failed 2/4 and demonstrated that full quality-rank transfer is too aggressive.

These prior results justify the architecture but no truth-aware family/group identity from them may enter v43 ranking.

## Binding development gate

Exactly one v43 Sugar order (exact v31) and one v43 HDB order are evaluated. The first technically valid result is binding.

For each of the four frozen SonotaCo literature panels, a win requires both:

- candidate macro-F1 strictly greater than the frozen literature comparator; and
- recovered `F1 > 0.5` shower count at least the literature comparator.

Development PASS requires **4/4** panel wins.

If v43 fails, this exact conservative `max(p_q,p_C)` shared-support transfer is permanently rejected. No in-place mean/minimum/interpolation, coefficient, cap, threshold, top-k, rank window, component-size term, route/year/budget exception, or alternate Boolean rule is authorized.

If v43 passes 4/4, freeze only the exact exposed-development reference material needed to reproduce it. A pass does not authorize protected validation or an external-superiority claim.

## Explicit non-search commitments

No:

- quality-suppression threshold/magnitude search;
- component-opportunity threshold/magnitude search;
- AND/OR/XOR/weighted Boolean search;
- `min`, mean, geometric-mean, weighted-average, coefficient, interpolation, bonus, or cap search for the support key;
- top-k or oracle correction count;
- rank window;
- budget/year-specific rule;
- Sugar modification;
- alternate quality order;
- global quality fusion;
- component-score global ordering;
- radius/metric/graph/component search;
- candidate-generation or membership change;
- feature/model/k/scaling/annual-combiner/diversity/fusion/source-quota search;
- truth-aware identity rule;
- post-result second search.

## Firewall

- SonotaCo 2013/2014 is `EXPOSED_DEVELOPMENT_ONLY`.
- Protected OrbitTrace solar longitude `20°–55°` remains inaccessible.
- No OrbitTrace target information or target-region events may be accessed.
- No MAARSY or DMS scientific access is authorized.
- Oracle identities from #1050/#1053/#1071 and truth-aware group identities from #1091/#1098 may not enter the v43 candidate rule.
