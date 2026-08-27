# OrbitTrace post-v46 joint inheritance-gap diagnostic v1

## Scientific role

This is a **post-v46 exposed-development mechanism diagnostic only**. It does not define, evaluate, select, or authorize a successor ranking.

The completed evidence is intentionally kept separate:

- #1098 shows that the exact 60-family HDB joint-positive set is recoverability-enriched relative to the remaining HDB universe;
- #1113 shows that, within those same 60 families, lower frozen `component_best_v31_percentile` is associated with recoverability;
- v44, v45, and v46 nevertheless all fail when component-level evidence is converted into candidate placement;
- the binding post-v46 boundary diagnostic #1136 shows the concrete failure mechanism at both fixed HDB literature boundaries: the same weak own-family candidate at exact-v31 rank 195 inherited `component_best_v31_percentile = 0.0` from its 16-member component and displaced materially stronger own-family candidates in both years.

#1136 is only one truth-blind entrant repeated at two budgets, so it cannot by itself justify a new ranking rule. This diagnostic therefore asks one population-level question before any successor is considered:

> **Within the exact fixed 60-family #1098 joint-positive HDB population, is a larger gap between a family's own exact-v31 percentile and its component-best percentile associated with failure to recover that family?**

Define the sole truth-blind statistic

`inheritance_gap = v31_percentile - component_best_v31_percentile`.

Because all 60 families already satisfy component opportunity, the gap is strictly positive and directly measures how much better the inherited component evidence is than the family's own v31 placement. Larger values mean more strongly borrowed component evidence.

This quantity is distinct from #1113's absolute component-best placement statistic. No component-best placement, quality placement, new order, Pareto frontier, selector, threshold, or replacement is evaluated here.

SonotaCo 2013/2014 remains `EXPOSED_DEVELOPMENT_ONLY`, never external validation.

## Immutable inputs and population

Use only:

1. authoritative #1098 run `31457923695`, artifact `9088724826`, artifact ZIP digest `sha256:11498b73237304f4175f37910596700ed78284bc6106d0c21dcaab66f97b7978`;
2. exact truth-blind signal file `V31_QUALITY_COMPONENT_JOINT_UNIVERSE_SIGNAL.json`, SHA-256 `a3bcea66b72003a38cc492ea3b182d92cd20f3d1b94a43acbc8a0cbdd465ed07`;
3. immutable #950 HDB pretruth family memberships from artifact `9074742322`, artifact ZIP digest `sha256:d940fa255804866f14bc34b1d72467d17adddcfb7d82c954ed5a8d1668aa307a`;
4. the same immutable exposed SonotaCo HDB truth already used by the established development evaluator, loaded only after the 60-family inheritance-gap vector is frozen.

Require the #1098 universe to contain exactly 229 HDB families and exactly 60 `joint_signal == true` families. For every selected family require:

- `positive_quality_suppression == true`;
- `component_closure_opportunity == true`;
- finite `v31_percentile` and `component_best_v31_percentile` in `[0,1]`;
- `inheritance_gap > 0`.

Before any truth is loaded, serialize the exact 60 identities and their frozen statistic to `V46_JOINT_INHERITANCE_GAP_VECTOR.json`. The vector contains no truth, recoverability label, literature budget, panel outcome, target information, MAARSY information, or DMS information.

No subset of the 60 may be selected after truth. No boundary identity from #1136 is used to define the population or gate.

## Truth-aware diagnostic

Only after the 60-family vector is frozen, restore the same #950 memberships and immutable exposed HDB truth.

For every family in the fixed vector, reproduce the established annual own-family F1 semantics exactly:

1. derive the fixed best label using the existing `family_truth` implementation over the two exposed years;
2. if the family is positive, compute annual F1 for that fixed label using the existing `annual_f1_for_fixed_label` implementation;
3. otherwise set annual F1 to zero;
4. define annual recoverability using the already-established fixed criterion `annual_f1 > 0.5`.

For each year separately, split the **same fixed 60 families** into recoverable and nonrecoverable classes. Both classes must be nonempty.

The sole preregistered direction test is:

`median(inheritance_gap | recoverable) < median(inheritance_gap | nonrecoverable)`.

PASS requires that strict median direction in **both 2013 and 2014**. No group-level aggregation, AUC, correlation, regression, p-value, threshold, quantile, top-k, alternate summary, or alternate direction test is authorized. Quartiles/min/max may be reported descriptively for the two already-defined classes, but they do not enter PASS/FAIL.

## Interpretation

PASS supports only this mechanism statement:

> Within the already-fixed #1098 joint-positive HDB population, recoverable families tend to borrow less of their placement evidence from a better component member than nonrecoverable families, in both exposed years.

PASS does **not** authorize a numerical inheritance-gap cutoff, a boundary exception, exclusion of the #1136 entrant, a replacement list, quality placement, component representative selection, pairwise dominance, or any successor order. Any successor requires its own separately motivated, truth-blind rule frozen before first evaluation.

FAIL means the boundary mechanism observed in #1136 does not generalize under this exact population-level median test. The diagnostic must then be closed; no alternate inheritance statistic, transform, threshold, or test may rescue it.

## Explicit prohibitions

No new rank/score/order, selector, replacement, successor, quality retry, component placement, component representative method, Pareto layer, pairwise dominance rule, threshold, top-k, rank window, budget/year exception, component-gap cutoff, component-size rule, q-calibration, alternate component statistic, suppression-magnitude rule, quality/component blend, coefficient, bonus, cap, oracle identity, boundary rescue list, truth-aware group identity, feature/model/k/scaling/diversity/fusion/source-quota search, or post-result second search.

## Firewall

Protected OrbitTrace solar longitude `20°–55°` remains inaccessible. No OrbitTrace target information or target-region events may be accessed. No MAARSY or DMS scientific access is authorized. All outputs must assert these firewall conditions and `SonotaCo = EXPOSED_DEVELOPMENT_ONLY`.
