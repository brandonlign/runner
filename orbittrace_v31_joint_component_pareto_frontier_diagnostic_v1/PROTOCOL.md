# OrbitTrace v31 joint-component Pareto-frontier diagnostic v1

## Scientific role

Post-result exposed-SonotaCo diagnostic only after:

- #1098 froze the exact truth-blind quality-suppression × component-opportunity gate over all 229 HDB families, with exactly 60 joint-positive families;
- v42 showed that sending all 60 to their full immutable quality-rank positions is too aggressive and harms both HDB panels;
- v43 showed that conservative shared-support placement leaves the top-9/top-11 memberships unchanged;
- #1113 independently showed that, **within the same fixed 60-family gate**, lower frozen `component_best_v31_percentile` is strongly associated with annual recoverability in both years at family and strict-group level;
- #1121 closed the direct-crossroute Boolean refinement because it removes only 2/60 families and zero strict groups.

The remaining supported question is whether component-best evidence defines a **threshold-free sparse priority structure** when combined with the existing exact-v31 order, without averaging/interpolating scores or choosing a top-k/rank window.

This diagnostic evaluates no new candidate total order, promotion position, replacement rule, literature panel, threshold, top-k, rank window, or successor.

SonotaCo 2013/2014 remains `EXPOSED_DEVELOPMENT_ONLY`.

## Immutable source

Use the authoritative #1098 truth-free full-universe joint-signal file from run `31457923695`, artifact `9088724826`, file SHA-256 `a3bcea66b72003a38cc492ea3b182d92cd20f3d1b94a43acbc8a0cbdd465ed07`.

Require exactly:

- 229 HDB families;
- 60 `joint_signal=true` families;
- exact v31 HDB rank/percentile for every family;
- exact `component_best_v31_percentile` for every family;
- graph SHA-256 `2f25aa7d9af1df0a350c034b2280a790c3869a7775bf6d7063d0d1e4cc802b25`;
- component SHA-256 `c1b80484502907ad19e0d51d8d48d364f3bf7a27e17576e073fe86ae44f499cd`;
- all threshold/top-k/rank-window/alternate-Boolean/oracle/protected-access flags false.

The 60-family frontier vector must be frozen **before** any outcome truth or truth-aware #1113 result is loaded.

#1113 is authorization/provenance only after the vector freeze: valid repaired run `31458734952`, artifact `9088994714`, result SHA-256 `939f4288a5f0d2de84ef566bb93713da664230deb65777c422795c93fba10c6d`, verdict `PASS_V42_JOINT_COMPONENT_PLACEMENT_DIAGNOSTIC`. No #1113 truth-aware family/group identity may enter the frontier definition.

## Exact truth-blind frontier definition

Restrict to the fixed 60 #1098 joint-positive HDB families.

For family `i`, define the two already-frozen coordinates:

- `x(i) = v31_percentile(i)` — smaller is better / earlier in exact v31;
- `y(i) = component_best_v31_percentile(i)` — smaller is better cross-route component evidence.

A family is on the **joint-component Pareto frontier** iff there is no other joint-positive family `j` such that

- `x(j) <= x(i)`, and
- `y(j) <= y(i)`,

with at least one inequality strict.

Because exact-v31 HDB ranks are unique, this is equivalently the deterministic record rule:

> sort the 60 joint-positive families by exact v31 rank ascending; mark a family as a frontier record iff its `component_best_v31_percentile` is strictly smaller than every earlier joint-positive family's component-best percentile.

The first joint-positive family is necessarily a record. Equal component-best values after the first occurrence are not new records.

This definition introduces no weight, coefficient, distance, threshold, quantile, rank window, budget, year, top-k, or outcome information.

Freeze the complete 60-family record/nonrecord vector and canonical SHA-256 before exposed truth is restored.

## Truth-aware diagnostic audit

After the frontier vector is frozen, restore immutable SonotaCo exposed-development truth and attach unchanged annual recoverability using the exact v22/v24 fixed-label semantics:

`recoverable_y = annual_F1_y > 0.5`.

### Family level

Within the fixed 60 joint-positive families, compare:

- `frontier`: Pareto-frontier record families;
- `dominated`: all remaining joint-positive families.

Report counts, recoverable counts/fractions, and threshold-free pairwise recoverability direction.

Family-level direction passes in a year iff:

`P(recoverable | frontier) > P(recoverable | dominated)`.

### Strict diagnostic-group level

For diagnosis only, use the unchanged strict fixed-label identity (`SHOWER/<best_label>` for positive recurrent families; unique `NEG/<family_id>` otherwise).

A `frontier_group` is any joint-positive strict group containing at least one frontier family. Its recoverability is evaluated using only its frontier families.

A `dominated_only_group` is a joint-positive strict group containing no frontier family. Its recoverability is evaluated using its dominated families.

Report counts and recoverable fractions.

Group-level direction passes in a year iff both group strata are nonempty and

`P(recoverable | frontier_group) > P(recoverable | dominated_only_group)`.

Truth-aware group identity is diagnostic only and may not enter any later ranking rule.

## Predeclared interpretation gate

The Pareto-frontier priority direction passes only if **all** of the following hold:

1. frontier count is at least 1 and strictly less than 60;
2. family-level direction passes in both 2013 and 2014;
3. strict-group-level direction passes in both 2013 and 2014.

Any required empty comparison stratum is a fail-closed non-pass; no smoothing or pseudocount is allowed.

No minimum effect size, significance threshold, maximum frontier size, required recovered-family count, oracle correction count, literature budget, or panel score is selected.

A PASS means only that the threshold-free Pareto/record structure is a defensible priority scaffold inside the fixed #1098 gate. It does not authorize a deployable total order or specify how a frontier family should move relative to non-gated exact-v31 families.

A FAIL closes this exact frontier/record mechanism. Do not rescue it with second/third Pareto layers, relaxed dominance, epsilon dominance, quantiles, top-k, rank windows, budget boundaries, component thresholds, fitted weights, or alternate tie handling.

## Explicit non-search commitments

No:

- candidate total order or literature panel evaluation;
- promotion/replacement rule;
- threshold/quantile/effect-size search;
- top-k or rank-window selection;
- budget/year-specific behavior;
- second Pareto layer or relaxed/epsilon dominance;
- weighted sum, mean, min, max, geometric mean, interpolation, coefficient, or bonus;
- alternate component statistic;
- component-size/q calibration;
- graph/component redefinition;
- feature/model/k/scaling/diversity/fusion/source-quota search;
- oracle identity rule;
- truth-aware group identity used for ranking;
- post-result second statistic.

## Firewall

- SonotaCo 2013/2014 is `EXPOSED_DEVELOPMENT_ONLY`.
- Protected OrbitTrace solar longitude `20°–55°` remains inaccessible.
- No OrbitTrace target information or target-region events may be accessed.
- No MAARSY or DMS scientific access is authorized.
