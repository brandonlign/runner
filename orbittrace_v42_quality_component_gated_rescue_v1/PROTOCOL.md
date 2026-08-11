# OrbitTrace v42 quality-component gated rescue v1

## Scientific role

Separately frozen exposed-SonotaCo development successor after:

- exact v31 remained the best stable base order;
- v39/v40/v41 showed that global cross-route/component reordering is too broad;
- #1071 proved the fixed HDB universe admits a single nested top-9/top-11 solution very close to v31;
- #1086 found recoverable-but-missed HDB group representatives are selectively suppressed by v31 relative to the immutable pre-SonotaCo #839/#853 quality order;
- #1072 found recoverable-but-missed HDB group representatives frequently have a frozen cross-route component-closure opportunity;
- #1091 preregistered the exact logical AND of those two binary directions and passed strongly: 0/9 surfaced versus 5/9 missed in 2013 and 0/9 versus 4/9 in 2014.

v42 tests one candidate-level response to that joint mechanism while preserving exact v31 everywhere the joint signal is absent.

SonotaCo 2013/2014 remains `EXPOSED_DEVELOPMENT_ONLY`. A pass is not external validation.

## Immutable identities

Use the unchanged fixed candidate universe and exact v31 machinery.

Before any SonotaCo truth is loaded, reproduce the exact #1064/#1072 pretruth geometry:

- Sugar candidates: 267;
- HDB candidates: 229;
- radius-1 cross-route edges: 2,334;
- graph SHA-256 `2f25aa7d9af1df0a350c034b2280a790c3869a7775bf6d7063d0d1e4cc802b25`;
- connected components: 196 total, 113 non-singleton, 83 singleton;
- component SHA-256 `c1b80484502907ad19e0d51d8d48d364f3bf7a27e17576e073fe86ae44f499cd`.

Also preserve the immutable HDB `quality_order` from the #950 pretruth manifest. This is the already-frozen pre-SonotaCo #839/#853 quality-diversity order used by #1086; it is not recomputed or tuned.

No candidate, membership, graph, component, or quality-order search is authorized.

## Exact v31 parent

After pretruth identity is frozen, reproduce exact v31 with the unchanged strict-whole-shower OOF 71D local-geometry margin, annual `min`, #839 diversity `lambda=0.8, scale=1.0`, and one equal rank-sum with exact v19.

Required parent controls:

- Sugar 2013: `0.2719801488280529 / 16`;
- Sugar 2014: `0.31529041952487225 / 17`;
- HDB 2013: `0.14888037368183737 / 9`;
- HDB 2014: `0.15198123772301594 / 9`.

Any mismatch is an engineering/provenance failure and yields no v42 scientific result.

## Sole v42 candidate-level rule

### Sugar

Sugar remains **exact v31 unchanged**. No Sugar candidate is rescored or reordered.

### HDB

Let `r_v31(i)` be HDB candidate `i`'s one-indexed exact v31 fused rank and let `r_q(i)` be its one-indexed immutable pre-SonotaCo quality rank from #950.

Define normalized own HDB v31 percentile:

`p_h(i) = (r_v31(i)-1)/228`.

For candidate `i`'s already-frozen connected component `C(i)`, define the same uncalibrated component-best normalized v31 evidence used only as a Boolean opportunity in #1072:

`p_C(i) = min((rank_route(j)-1)/(N_route-1))`

over every Sugar or HDB member `j` of `C(i)` using the exact v31 fused orders.

Define the two exact binary conditions:

1. `quality_suppressed(i) = [r_q(i) < r_v31(i)]`;
2. `component_opportunity(i) = [p_C(i) < p_h(i)]`.

Define the exact joint gate:

`joint(i) = quality_suppressed(i) AND component_opportunity(i)`.

No suppression magnitude or component-evidence magnitude enters the gate.

Define one HDB promotion key:

- if `joint(i)` is true: `key(i) = r_q(i)`;
- otherwise: `key(i) = r_v31(i)`.

The v42 HDB total order is the deterministic sort by

`(key(i), r_v31(i), family_id)`.

Thus a joint-positive candidate may receive only the position implied by the already-frozen quality rank; no coefficient, interpolation, additive bonus, threshold, top-k limit, rank window, budget, year, or oracle cardinality is used.

This is deliberately different from v34 global quality fusion and v39-v41 global cross-route/component reorderings: the quality prior can act only when the independently preregistered #1091 component-and-quality gate is simultaneously true.

## Authorizing diagnostic

Pin #1091 first technically valid run `31456963941`, artifact `9088402091`, digest `sha256:d1943f629964633f44e154252a225f7171c380674ae6e60e5fcbbd3f8b890dd7`, result JSON SHA-256 `2edb949dbab2d7cbf6ed5e808e2a049116eb0934b25b356572463b615d730842`.

Require its PASS verdict and diagnostic-only/firewall state. The truth-aware group identities in #1091 are not loaded into or matched against candidate IDs during v42 ranking; only the frozen formula above is implemented.

## Binding development gate

Exactly one v42 Sugar order (identical to v31) and one v42 HDB order are evaluated. The first technically valid result is binding.

For each of the four frozen SonotaCo literature panels, a win requires:

- candidate macro-F1 strictly greater than the frozen literature comparator; and
- recovered `F1 > 0.5` shower count at least the literature comparator.

Development PASS requires 4/4 panel wins.

If v42 fails, this exact candidate-level AND gate plus quality-rank promotion key is permanently rejected. No in-place threshold, magnitude, weight, cardinality, route/year/budget exception, alternate Boolean rule, or promotion key rescue is authorized.

If v42 passes 4/4, freeze only the exact exposed-development reference material needed to reproduce its full-training application. A pass does not authorize protected validation or an external-superiority claim.

## Explicit non-search commitments

No:

- quality-suppression threshold or magnitude transform;
- component-opportunity threshold or magnitude transform;
- AND/OR/XOR/weighted Boolean search;
- top-k or oracle correction count;
- rank window;
- promotion coefficient, interpolation, bonus, or cap;
- budget- or year-specific rule;
- Sugar modification;
- alternate quality order;
- global quality fusion;
- raw/calibrated component-score ordering;
- representative or secondary-fragment rule;
- radius/metric/graph/component search;
- candidate-generation or membership change;
- feature/model/k/scaling/annual-combiner/diversity/fusion/source-quota search;
- post-result second search.

## Firewall

- SonotaCo 2013/2014 is `EXPOSED_DEVELOPMENT_ONLY`.
- Protected OrbitTrace solar longitude `20°–55°` remains inaccessible.
- No OrbitTrace target information or target-region events may be accessed.
- No MAARSY or DMS scientific access is authorized.
- Oracle identities from #1050/#1053/#1071 and truth-aware group identities from #1091 may not enter the v42 candidate rule.
