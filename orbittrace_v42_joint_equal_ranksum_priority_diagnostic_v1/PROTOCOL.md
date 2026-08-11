# OrbitTrace v42 joint-positive equal-rank-sum priority diagnostic v1

## Scientific role

Post-result exposed-SonotaCo diagnostic only after:

- #1091 found the exact binary joint signal `(quality_suppression > 0) AND component_closure_opportunity` enriched among recoverable-but-missed HDB groups;
- #1098 froze that exact signal over all 229 HDB families and passed its full-universe selectivity gate, but found 60/229 candidates joint-positive and only marginal family-level 2014 enrichment;
- binding v42 failed because using raw immutable `quality_rank` alone as the promotion position chose harmful sparse prefix replacements.

The unresolved question is therefore not whether the joint gate has any information, but whether the **two already-frozen evidence ranks inside that gate can provide a defensible priority ordering** without another fitted magnitude, threshold, rank window, or top-k rule.

This diagnostic evaluates one canonical parameter-free priority statistic only. It evaluates no new total order, selector, replacement rule, literature panel, or successor.

## Frozen source signal

Use the authoritative first technically valid #1098 run:

- run `31457788803`;
- artifact `9088683367`;
- artifact digest `sha256:1ad3513e021136b402e8aa121faa37675e2982d57aa2a14f1bc5e28d81b61b11`;
- frozen signal-vector canonical SHA-256 `47966ec3e5b29f56c5bb536ed19f24a99ff41f11bc2d20778240b16c5e44fd47`.

Consume only `V31_QUALITY_COMPONENT_JOINT_UNIVERSE_SIGNAL.json` from that artifact before outcome truth is loaded. Require:

- 229 fixed HDB families;
- exactly 60 `joint_signal=true` families;
- exact joint definition `(v31_percentile > quality_percentile) AND (component_best_v31_percentile < v31_percentile)`;
- graph SHA `2f25aa7d9af1df0a350c034b2280a790c3869a7775bf6d7063d0d1e4cc802b25`;
- component SHA `c1b80484502907ad19e0d51d8d48d364f3bf7a27e17576e073fe86ae44f499cd`;
- no threshold/top-k/rank-window/alternate-Boolean/oracle rule in the frozen signal.

## Sole priority statistic

For every joint-positive HDB family `i`, #1098 already freezes two normalized better-is-smaller evidence ranks:

- `p_q(i) = quality_percentile` from the immutable pre-SonotaCo #950 quality order;
- `p_c(i) = component_best_v31_percentile` from the exact frozen #1072 physical component using exact v31 route ranks.

Define exactly one equal-weight rank-sum priority statistic

`e(i) = (p_q(i) + p_c(i)) / 2`.

Lower `e` means stronger concordant priority evidence.

The equal weight is not fitted here: equal rank-sum is the already-established OrbitTrace fusion convention used by v19/v31, now applied only to the two frozen rescue evidences that define the #1091/#1098 joint direction. No raw-v31 percentile is added to `e`, and no minimum, maximum, geometric mean, harmonic mean, product, learned weight, coefficient, calibration, clipping, or transform is evaluated.

Before outcome truth is loaded, freeze for all 60 joint-positive families:

- family ID;
- `p_q`;
- `p_c`;
- `e`;
- deterministic priority rank by `(e, v31_rank, family_id)`.

## Truth-aware priority diagnostic

Only after the complete 60-family priority vector is frozen, use the immutable exposed SonotaCo 2013/2014 truth and unchanged #950 HDB memberships to compute each fixed family's annual F1 for its unchanged recurrent best label exactly as in v24. Annual recoverability remains `F1_y > 0.5`.

Evaluate the ability of **lower e** to prioritize recoverability within the frozen joint-positive set using pairwise concordance / ROC AUC, with no threshold selection.

### Family level

For each year separately:

- positives = joint-positive families with annual `F1 > 0.5`;
- negatives = the remaining joint-positive families;
- compute `AUC_family` for score `-e` predicting annual recoverability;
- report median `e` in positive and negative families descriptively.

### Strict diagnostic-group level

Use the unchanged v22 diagnostic group convention after truth is loaded: `SHOWER/<best_label>` for positive recurrent families, otherwise unique `NEG/<family_id>`.

For each diagnostic group containing at least one joint-positive family, define the group priority

`e_group = min e(i)`

over its joint-positive member families, because a deployable candidate order needs only one sufficiently high-priority family to surface that physical group. Define group recoverability as `any(annual_F1_y > 0.5)` among its fixed families.

For each year compute `AUC_group` for score `-e_group` predicting group recoverability. Report group counts and median `e_group` in recoverable/nonrecoverable groups descriptively.

No group identity or group-level score may enter a later deployable candidate rule; this level is diagnostic only.

## Predeclared interpretation gate

The equal-rank-sum priority direction is supported only if, in **both 2013 and 2014**:

1. `AUC_family > 0.5`; and
2. `AUC_group > 0.5`.

No p-value, minimum AUC margin, effect-size cutoff, rank-window, top-k, or selected operating threshold is used.

A PASS authorizes at most one separately frozen successor using this exact `e` only inside the already-frozen #1098 joint gate. It does not choose a budget, top-k, rank window, number of corrections, or any alternative priority statistic.

A FAIL closes this exact equal-rank-sum priority mechanism. Do not rescue it by using min/max/geometric/product fusion, fitted weights, adding v31 to the average, clipping, thresholds, rank windows, top-k, or year/budget-specific exceptions within this direction.

## Explicit non-search commitments

No:

- new candidate total order;
- literature panel evaluation;
- selector/replacement rule;
- alternative rank aggregation;
- coefficient/weight search;
- threshold/top-k/rank-window search;
- AND/OR/XOR rule change;
- component size/calibration rule;
- graph/component redefinition;
- feature/model/k/scaling/diversity/fusion/source-quota change;
- oracle identity hard-coding;
- post-result second statistic.

## Firewall

- SonotaCo 2013/2014 is `EXPOSED_DEVELOPMENT_ONLY`.
- Protected OrbitTrace solar longitude `20°–55°` remains inaccessible.
- No OrbitTrace target information or target-region events may be accessed.
- No MAARSY or DMS scientific access is authorized.
- Oracle identities from #1050/#1053/#1071 cannot enter the statistic or interpretation gate.
