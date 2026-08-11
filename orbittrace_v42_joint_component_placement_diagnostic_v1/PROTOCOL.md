# OrbitTrace post-v42 joint-component placement diagnostic v1

## Scientific role

Post-result exposed-SonotaCo diagnostic only after binding v42 failed 2/4. v42 preserved Sugar exactly but degraded both HDB panels when every candidate satisfying the already-frozen joint gate `(quality_rank < v31_rank) AND component_opportunity` used its full immutable quality rank as a promotion key. The later full-universe diagnostic #1098 independently confirmed that the exact joint gate is recoverability-enriched but broad: 60/229 HDB candidates are joint-positive, with only marginal 2014 family-level enrichment.

This diagnostic asks one narrower question before any new successor is defined:

> **Conditional on the already-frozen joint-positive set, is the already-frozen component-best exact-v31 percentile itself a useful truth-free placement/priority signal for annual recoverability?**

No new order, selector, replacement, panel result, threshold, top-k, rank window, coefficient, or successor is evaluated.

SonotaCo 2013/2014 remains **EXPOSED DEVELOPMENT ONLY**.

## Immutable inputs

Use only:

1. authoritative #1098 run `31457923695`, artifact `9088724826`, artifact digest `sha256:11498b73237304f4175f37910596700ed78284bc6106d0c21dcaab66f97b7978`;
2. exact #1098 truth-blind signal file `V31_QUALITY_COMPONENT_JOINT_UNIVERSE_SIGNAL.json`, SHA-256 `a3bcea66b72003a38cc492ea3b182d92cd20f3d1b94a43acbc8a0cbdd465ed07`;
3. immutable #950 pretruth HDB payload from artifact `9074742322`, zip digest `sha256:d940fa255804866f14bc34b1d72467d17adddcfb7d82c954ed5a8d1668aa307a`;
4. immutable exposed SonotaCo truth/comparator artifact `9069505548`, zip digest `sha256:cdea3297c234b0b3a8f09c2208649c8607bb3e9a9004d299f6dcc18536ebb797`;
5. exact frozen-v40 evaluator source at commit `31704c312c09be2765ad3f65a0685d1acfd2b055`, using its existing v22/v24 evaluator semantics and stubs.

Before truth is interpreted, require the #1098 signal to have:

- verdict `PASS_V31_QUALITY_COMPONENT_JOINT_UNIVERSE_SIGNAL_FREEZE`;
- exactly 229 HDB family rows and exactly 60 `joint_signal=true` rows;
- exact graph SHA `2f25aa7d9af1df0a350c034b2280a790c3869a7775bf6d7063d0d1e4cc802b25`;
- exact component SHA `c1b80484502907ad19e0d51d8d48d364f3bf7a27e17576e073fe86ae44f499cd`;
- no selected threshold/top-k/rank-window/alternate Boolean rule/oracle identity;
- all protected-data access flags false.

The signal rows are immutable. Do not recompute or alter joint membership, quality ranks, v31 ranks, component identities, or `component_best_v31_percentile`.

## Fixed diagnostic population

Use **only the 60 HDB candidates with `joint_signal=true` in the frozen #1098 signal file**.

For each candidate, attach annual recoverability under the unchanged fixed family membership and exact #854/v22-v24 truth semantics:

- recoverable in year `y` iff its fixed-label annual `F1_y > 0.5`;
- otherwise nonrecoverable.

No candidate is included or excluded based on truth beyond this diagnostic classification.

## Sole placement statistic

The only tested truth-free placement statistic is the already-frozen #1098 field:

`component_best_v31_percentile`

Lower is better. It is the best normalized exact-v31 percentile among all frozen Sugar/HDB members of that candidate's exact #1072 connected component.

Do not test raw component size, q-calibration, quality rank, suppression magnitude, v31 rank, promotion gain, rank ratios, differences, products, sums, or alternate component aggregations as placement statistics.

## Two preregistered diagnostic levels

For each year separately:

### 1. Family level

Within the fixed 60 joint-positive candidates, split candidates into annual recoverable and nonrecoverable classes. Report counts and the median `component_best_v31_percentile` in each class.

Family-level direction passes iff:

`median(component_best | recoverable) < median(component_best | nonrecoverable)`.

### 2. Diagnostic strict-group level

Using the exact exposed fixed-label strict-group identity only for diagnosis, group the same 60 joint-positive candidates by their fixed shower label; each negative candidate remains its own `NEG/<family_id>` group.

For each such group define one truth-free group placement value:

`group_component_best = min(component_best_v31_percentile among joint-positive candidates in that diagnostic group)`.

A group is annual recoverable iff at least one of its joint-positive candidates has annual `F1 > 0.5` in that year.

Report group counts and median `group_component_best` for recoverable and nonrecoverable groups.

Group-level direction passes iff:

`median(group_component_best | recoverable) < median(group_component_best | nonrecoverable)`.

## Binding interpretation gate

The diagnostic PASS requires the family-level and diagnostic-group-level directions to pass in **both 2013 and 2014**. No minimum effect size beyond strict inequality is selected.

A PASS means only that component-best evidence deserves a separately frozen successor design as a placement/priority coordinate **conditional on the already-frozen joint gate**. It does not authorize any particular total order, threshold, number of promotions, budget window, coefficient, or panel-specific action.

A FAIL closes this exact conditional component-placement hypothesis. Do not rescue it with mean instead of median, another quantile, component size, calibrated q, transformed percentile, rank gap, threshold, top-k, or post-result alternative statistic within this diagnostic.

## Explicit non-search commitments

No:

- new candidate order or panel evaluation;
- selector/replacement rule;
- quality-rank placement retry;
- threshold/top-k/rank-window search;
- component-size or q-calibration statistic;
- alternate component aggregation;
- suppression-magnitude or promotion-gain statistic;
- route/year/budget-specific rule;
- graph/component redefinition;
- feature/model/k/scaling/diversity/fusion/source-quota search;
- oracle identity hard-coding;
- post-result second statistic.

## Firewall

- SonotaCo 2013/2014 is `EXPOSED_DEVELOPMENT_ONLY`.
- Protected OrbitTrace solar longitude `20°–55°` remains inaccessible.
- No OrbitTrace target information or target-region events may be accessed.
- No MAARSY or DMS scientific access is authorized.
- Truth-aware identities may appear only in diagnostic grouping/output and may not define any future successor rule.
