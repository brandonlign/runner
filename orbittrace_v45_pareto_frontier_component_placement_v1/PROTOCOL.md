# OrbitTrace v45 Pareto-frontier component placement v1

## Scientific role

Separately frozen exposed-SonotaCo development successor after:

- exact v31 remained the stable 2/4 base;
- #1098 froze a broad 60/229 HDB quality-suppression × component-opportunity gate;
- #1113 showed lower frozen `component_best_v31_percentile` strongly predicts annual recoverability within those 60;
- v44 showed that applying component-best placement to **all 60** is too disruptive and degrades HDB sharply;
- #1126, frozen independently before the v44 outcome, established a threshold-free Pareto/record frontier in `(exact-v31 percentile, component-best percentile)` inside the same fixed 60-family gate. Its vector was frozen before outcome truth and its binding audit passed at family and strict-group level in both years.

v45 tests exactly one sparse architecture implied by those results: **frontier membership decides eligibility for component-best placement; every non-frontier family remains exact v31**.

The observed frontier cardinality is not a parameter and is not used as a chosen correction count. The method applies the same Pareto rule to whatever frontier the frozen truth-blind inputs imply.

SonotaCo 2013/2014 remains `EXPOSED_DEVELOPMENT_ONLY`. A pass is development evidence, not external validation.

## Immutable identities

Use the unchanged fixed candidate universe, exact v31 machinery, immutable #950 quality order, and exact #1064/#1072 graph/components.

Before truth:

- Sugar candidates: 267;
- HDB candidates: 229;
- radius-1 graph edges: 2,334;
- graph SHA-256 `2f25aa7d9af1df0a350c034b2280a790c3869a7775bf6d7063d0d1e4cc802b25`;
- components: 196 total / 113 non-singleton / 83 singleton;
- component SHA-256 `c1b80484502907ad19e0d51d8d48d364f3bf7a27e17576e073fe86ae44f499cd`.

Exact v31 parent controls after truth is loaded:

- Sugar 2013 `0.2719801488280529 /16`;
- Sugar 2014 `0.31529041952487225 /17`;
- HDB 2013 `0.14888037368183737 /9`;
- HDB 2014 `0.15198123772301594 /9`.

Any mismatch is engineering/provenance failure and produces no v45 scientific result.

## Frozen frontier source

Use the authoritative #1126 artifact from first valid run `31459760333`, artifact `9089357860`, digest `sha256:ce055dc38f5f56d82e6330590fa30becaf6896ab4323de7e1d4abf4644e97a9a`.

The pretruth-frozen vector file is

`freeze/V31_JOINT_COMPONENT_PARETO_FRONTIER_VECTOR.json`

with file SHA-256

`5ca5cab6f6a47c05d013237190ad21b247a13e22fa06988ee36dc0832a37fc02`

and canonical vector SHA-256

`8373f4946e7f84c7c3ee0ac51167881722d4f8b78c34383400f1967824df6798`.

Require the vector role

`FIXED_60_JOINT_FAMILY_PARETO_FRONTIER_FROZEN_BEFORE_OUTCOME_TRUTH_OR_1113_AUTHORIZATION`

and exact source #1098 identity. No truth-aware outcome row may be used for v45 placement.

#1126's diagnostic result is authorization/provenance only and must report `PASS_V31_JOINT_COMPONENT_PARETO_FRONTIER_DIAGNOSTIC`. Its frontier count may be audited for identity, but **must not be hard-coded into the v45 algorithm or used as a chosen top-k**.

## Exact v45 rule

### Sugar

Sugar remains exact v31 unchanged.

### HDB

For every HDB family `i`, reconstruct exact v31 and the exact #1098 joint gate using the unchanged immutable quality order and frozen components.

Let:

- `p_h(i)` = own exact-v31 HDB percentile;
- `p_C(i)` = frozen component-best exact-v31 normalized percentile, exactly as #1098/#1113/v44;
- `frontier(i)` = the truth-blind #1126 Pareto-frontier flag.

Require that every frontier family is in the exact reconstructed #1098 joint-positive set and that the complete #1126 60-family joint universe matches the reconstructed gate.

Define the sole v45 placement key:

- if `frontier(i)=true`, `key(i)=p_C(i)`;
- otherwise `key(i)=p_h(i)`.

Then sort all 229 HDB families exactly by

`(key(i), p_h(i), family_id)`.

This means:

- frontier families receive the same component-best placement coordinate tested in v44;
- all dominated joint-positive families revert exactly to their own v31 placement;
- all nonjoint families remain exact v31 placement.

There is no promotion coefficient, threshold, cap, bonus, interpolation, quality-rank placement, frontier cardinality rule, or literature-budget action.

## Why this is a distinct successor rather than a v44 rescue

v44's exact architecture—component-best placement for all 60 joint-positive families—is permanently rejected.

Before the v44 result was known, #1126 separately froze and evaluated a parameter-free Pareto/record priority structure derived only from truth-blind `(v31, component-best)` coordinates. Its PASS therefore supplies an independent selector mechanism; v45 applies the already-frozen selector without choosing a threshold after v44.

v45 is not allowed to change frontier membership, use a second Pareto layer, relax dominance, or use the observed frontier size as a target count.

## Binding development gate

Exactly one v45 Sugar order and one v45 HDB order are evaluated. The first technically valid result is binding.

For each frozen SonotaCo literature panel, a win requires both:

- candidate macro-F1 strictly greater than the literature comparator; and
- candidate recovered `F1 > 0.5` shower count at least the literature comparator.

Development PASS requires **4/4** panel wins.

If v45 fails, exact Pareto-frontier gating + component-best placement is permanently rejected. Do not rescue it with second Pareto layers, relaxed/epsilon dominance, frontier-specific rank caps, alternate frontier placement, top-k, rank windows, budget boundaries, coefficients, or truth-aware frontier selection.

If v45 passes, freeze only the exact exposed-development reference package needed to reproduce it. A pass does not authorize protected validation or an external-superiority claim.

## Explicit non-search commitments

No:

- observed frontier-cardinality/top-k rule;
- threshold, quantile, rank window, budget boundary;
- second Pareto layer, relaxed dominance, epsilon dominance;
- quality-rank placement or quality/component blend;
- mean/min/max/interpolation/weighted-score search;
- promotion coefficient, bonus, cap, or clipping;
- alternate component statistic or component-size/q term;
- route/year/budget-specific behavior;
- Sugar modification;
- graph/component/candidate/membership change;
- feature/model/k/scaling/annual-combiner/diversity/fusion/source-quota search;
- oracle identity rule;
- truth-aware group identity used for ranking;
- post-result second search.

## Firewall

- SonotaCo 2013/2014 is `EXPOSED_DEVELOPMENT_ONLY`.
- Protected OrbitTrace solar longitude `20°–55°` remains inaccessible.
- No OrbitTrace target information or target-region events may be accessed.
- No MAARSY or DMS scientific access is authorized.
