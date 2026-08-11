# OrbitTrace v45 joint-gated component-representative placement v1

## Scientific role

Separately frozen exposed-SonotaCo successor after exact v31, failed v42/v43, #1113 component-placement PASS, and #1121 full-universe three-way refinement FAIL.

The surviving evidence is narrow:

- #1091/#1098 support the exact 60-family HDB joint condition `(quality_suppressed AND component_opportunity)` but the candidate-level gate is broad.
- v42 proved immutable quality rank is a harmful placement coordinate inside that gate.
- v43 proved the conservative shared-support placement is too weak to move the relevant prefixes.
- #1113 independently found lower frozen `component_best_v31_percentile` is associated with recoverability inside the fixed joint gate at both family and strict-group levels in both years.
- #1121 closed the categorical direct-crossroute third sign: it removes only 2/60 families and zero strict groups.
- Earlier v39/v40 work showed that copying component evidence onto multiple fragments can flood a small budget. v40 already froze the deterministic own-route component representative as the member with the best exact-v31 rank.

v45 therefore tests one structural architecture: **only the best-v31 HDB representative of a frozen physical component can receive joint-gated component-best placement.** Every other HDB family remains on exact-v31 placement, including all nonrepresentative fragments. Sugar remains exact v31.

This is not interpolation between v42/v43, not a threshold, and not an oracle-cardinality rule.

SonotaCo 2013/2014 remains `EXPOSED_DEVELOPMENT_ONLY`.

## Immutable source identity

Use the authoritative #1098 full-universe signal artifact:

- run `31457788803`;
- artifact `9088683367`;
- artifact digest `sha256:1ad3513e021136b402e8aa121faa37675e2982d57aa2a14f1bc5e28d81b61b11`;
- `V31_QUALITY_COMPONENT_JOINT_UNIVERSE_SIGNAL.json` SHA-256 `a3bcea66b72003a38cc492ea3b182d92cd20f3d1b94a43acbc8a0cbdd465ed07`;
- frozen signal canonical SHA-256 `47966ec3e5b29f56c5bb536ed19f24a99ff41f11bc2d20778240b16c5e44fd47`.

Require exactly:

- 229 HDB family rows;
- 60 `joint_signal=true` rows;
- joint definition `(v31_percentile > quality_percentile) AND (component_best_v31_percentile < v31_percentile)`;
- exact #1064 graph SHA `2f25aa7d9af1df0a350c034b2280a790c3869a7775bf6d7063d0d1e4cc802b25`;
- exact #1072 component SHA `c1b80484502907ad19e0d51d8d48d364f3bf7a27e17576e073fe86ae44f499cd`;
- no selected threshold/top-k/rank-window/alternate Boolean/oracle rule;
- all protected-access flags false.

Use immutable #950 HDB memberships and exposed truth/comparator artifact only after the complete v45 order is frozen.

## Authorizing placement diagnostic

Pin #1113:

- run `31458734952`;
- artifact `9088994714`;
- digest `sha256:5bddfbe4abda60006757561d4c6477102317e02f5fb9555330e0b62eaf3353df`;
- result SHA-256 `939f4288a5f0d2de84ef566bb93713da664230deb65777c422795c93fba10c6d`;
- verdict `PASS_V42_JOINT_COMPONENT_PLACEMENT_DIAGNOSTIC`.

Require the exact 60-family population and the predeclared statistic `component_best_v31_percentile` with lower-is-better direction supported at family and diagnostic-group levels in both years. No truth-aware identity from #1113 may enter v45.

## Frozen component representative rule

For each exact #1072 connected component containing one or more HDB families, define its HDB representative exactly as already used by v40:

`R_HDB(C) = HDB member of C with smallest exact-v31 rank`,

with `family_id` as deterministic tie-break only if needed.

This is a structural de-fragmentation rule. It is not selected from SonotaCo outcome truth.

A component representative is **rescue-eligible** iff that representative itself is `joint_signal=true` in the exact #1098 signal. Joint-positive nonrepresentative HDB fragments are not rescue-eligible and remain at exact-v31 placement.

No representative search, alternate member choice, component-size condition, or truth-aware component identity is authorized.

## Sole v45 placement rule

For every HDB family `i`, retain exact #1098 values:

- `p_v31(i) = v31_percentile`;
- `p_C(i) = component_best_v31_percentile`.

Define

`eligible(i) = [i = R_HDB(C(i))] AND joint_signal(i)`.

Then

`key_v45(i) = p_C(i)` if `eligible(i)` else `p_v31(i)`.

Construct exactly one HDB total order by ascending

`(key_v45(i), p_v31(i), family_id)`.

Sugar remains **exact v31 unchanged**.

No quality rank enters placement after the already-frozen Boolean gate. No q calibration, component-size term, direct-crossroute third sign, coefficient, blend, bonus, cap, threshold, top-k, rank window, insertion depth, or budget/year-specific action is allowed.

## Truth-blind structural controls

From the exact #1098 signal alone, before evaluation truth:

- HDB connected-component count represented by the 229 rows must be `138`;
- rescue-eligible component representatives must be exactly `48`;
- exact-v31 HDB order SHA-256 must be `85ac3f29a443c35b3812cf28c99ef13474fc3e0455458e20b41cec64d942073d`;
- frozen v45 HDB order SHA-256 must be `85e604e9aefca88736b6fcd7acc2670c4f7ec89781e74937135422436f13d194`.

For audit only, the resulting total order differs in membership from exact v31 by one family at prefix 9 and two families at prefix 11. These counts are consequences of the frozen rule and are **not** gates, targets, or chosen from #1071. Oracle identities/cardinalities do not enter the ordering formula.

Any mismatch in these pre-evaluation structural controls is an engineering/provenance failure and yields no v45 scientific result.

## Exact v31 controls

The unchanged parent controls remain:

- Sugar 2013 `0.2719801488280529 / 16`;
- Sugar 2014 `0.31529041952487225 / 17`;
- HDB 2013 `0.14888037368183737 / 9`;
- HDB 2014 `0.15198123772301594 / 9`.

The exact #1098 signal already fixes v31 HDB ranks; Sugar is declared unchanged only if these immutable parent controls/provenance remain consistent.

## Binding development gate

Exactly one frozen v45 HDB order and exact-v31 Sugar order are evaluated. The first technically valid result is binding.

For each frozen SonotaCo panel, a win requires both:

- candidate macro-F1 strictly greater than the frozen literature comparator; and
- candidate recovered `F1 > 0.5` shower count at least the literature comparator.

Development PASS requires `4/4` panel wins.

If v45 fails, exact joint-gated best-HDB-component-representative placement is permanently rejected. Do not rescue it with another representative, component threshold, q/size adjustment, promotion cap, rank window, top-k, coefficient, interpolation, direct-crossroute magnitude, year/budget exception, or post-result local search.

If v45 passes, freeze only the exposed-development reference needed for reproducibility. A PASS is not external validation and does not authorize a general superiority claim.

## Explicit non-search commitments

No:

- candidate-generation or membership change;
- graph/radius/metric/component change;
- representative search;
- threshold/top-k/rank-window/cardinality rule;
- quality/component blend or fitted weight;
- q/component-size correction;
- promotion coefficient/bonus/cap/interpolation;
- three-way/direct-crossroute rule;
- route/year/budget exception;
- feature/model/k/scaling/annual-combiner/diversity/fusion/source-quota search;
- truth-aware group identity in ranking;
- oracle identity or #1071 replacement identity in ranking;
- post-result second search.

## Firewall

- SonotaCo 2013/2014 is `EXPOSED_DEVELOPMENT_ONLY`.
- Protected OrbitTrace solar longitude `20°–55°` remains inaccessible.
- No OrbitTrace target information or target-region events may be accessed.
- No MAARSY or DMS scientific access is authorized.
