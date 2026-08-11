# OrbitTrace v31 three-way full-universe selectivity diagnostic v1

## Scientific role

Post-result exposed-SonotaCo diagnostic only after:

- #1091 established the exact candidate direction `(quality_suppression > 0) AND component_closure_opportunity` among recoverable HDB groups missed by exact v31;
- #1098 froze that exact direction over all 229 HDB families and found it recoverability-enriched but broad: 60/229 families are joint-positive;
- binding v42 showed that giving all 60 their full immutable quality-rank placement is harmful at the tiny literature budgets;
- binding v43 showed that conservative `max(p_quality,p_component_best)` placement does not change the top-9/top-11 memberships;
- #1114 independently showed that all #1091 joint-positive missed recoverable groups also have positive direct cross-route rank disagreement, with 5/9 missed vs 0/9 surfaced in 2013 and 4/9 vs 0/9 in 2014;
- #1113 independently showed that, within the fixed 60-family #1098 gate, lower frozen `component_best_v31_percentile` is strongly associated with annual recoverability.

The remaining selector question is whether the direct cross-route sign from #1066/#1114 actually removes false positives from the broad fixed 60-family gate when extended to the complete HDB universe.

This diagnostic evaluates **no candidate total order, placement rule, replacement, literature panel, threshold, top-k, rank window, or successor**.

SonotaCo 2013/2014 remains `EXPOSED_DEVELOPMENT_ONLY`.

## Immutable inputs

Use only the fixed public-development identities already frozen in the repository:

1. immutable #950 Sugar/HDB pretruth payload and memberships;
2. exact frozen #839 ranker source;
3. exact v31 reconstruction through frozen-v40 source commit `31704c312c09be2765ad3f65a0685d1acfd2b055`;
4. exact #1064 radius-1 cross-route graph SHA-256 `2f25aa7d9af1df0a350c034b2280a790c3869a7775bf6d7063d0d1e4cc802b25`;
5. exact #1072 connected-component SHA-256 `c1b80484502907ad19e0d51d8d48d364f3bf7a27e17576e073fe86ae44f499cd`;
6. authoritative #1098 full-universe joint-signal file from run `31457923695`, artifact `9088724826`, file SHA-256 `a3bcea66b72003a38cc492ea3b182d92cd20f3d1b94a43acbc8a0cbdd465ed07`;
7. authoritative #1114 three-way group diagnostic from run `31458509957`, artifact `9088912217`, result SHA-256 `31681b318f6e2732cd8338d484959dfdcade08d65b7f90225d9a0c269d4630eb`.

The #1098 file must contain exactly 229 HDB families and exactly 60 `joint_signal=true` families, with all threshold/top-k/rank-window/alternate-Boolean/oracle/protected-access flags false.

The #1114 file is authorization only. Its truth-aware group identities may not enter the candidate-level signal vector.

Before outcome recoverability is inspected, reproduce exact v31 route orders and require the four parent controls:

- Sugar 2013 `0.2719801488280529 /16`;
- Sugar 2014 `0.31529041952487225 /17`;
- HDB 2013 `0.14888037368183737 /9`;
- HDB 2014 `0.15198123772301594 /9`.

No v31 quantity is changed.

## Exact candidate-level direct cross-route sign

Use the exact frozen #1064 radius-1 bipartite graph. For each HDB family `i`:

- `p_hdb(i) = (r_hdb_v31(i)-1)/228`;
- let `N(i)` be its direct radius-1 Sugar neighbors in the frozen graph;
- if `N(i)` is empty, `direct_crossroute_positive(i)=false`;
- otherwise define

`p_sugar_direct_best(i) = min((r_sugar_v31(j)-1)/266 for j in N(i))`

and

`direct_crossroute_positive(i) = [p_sugar_direct_best(i) < p_hdb(i)]`.

This is the full-family extension of the already-frozen #1066/#1114 sign: the corresponding physical structure has a directly linked Sugar candidate ranked better than the HDB family under exact v31.

No edge distance, neighbor count, overlap weight, component closure, route-budget normalization, magnitude threshold, ratio, transform, or alternate direct-neighbor aggregation is tested here. The minimum direct Sugar rank is already the predeclared #1066 convention.

## Exact three-way selector flag

For each fixed HDB family, inherit #1098 without modification:

- `positive_quality_suppression`;
- `component_closure_opportunity`;
- `joint_signal = positive_quality_suppression AND component_closure_opportunity`.

Define exactly:

`threeway_signal = joint_signal AND direct_crossroute_positive`.

The complete 229-family vector must be written and SHA-256 frozen before annual recoverability summaries are computed.

## Truth-aware conditional selector audit

The scientific question is **incremental specificity inside the already-supported 60-family gate**, not another comparison of the inherited gate against the entire universe.

For each year separately, attach unchanged fixed-label annual recoverability (`F1_y > 0.5`) using the exact v22/v24 semantics.

### Family level

Within the 60 #1098 joint-positive families, partition into:

- `threeway`: `threeway_signal=true`;
- `joint_only`: `joint_signal=true AND direct_crossroute_positive=false`.

Report counts, recoverable counts, and recoverable fractions.

Family-level refinement passes iff

`P(recoverable | threeway) > P(recoverable | joint_only)`.

### Diagnostic strict-group level

For diagnosis only, use the unchanged fixed-label strict-group identity (`SHOWER/<best_label>` for positive recurrent families; unique `NEG/<family_id>` otherwise) among the same 60 joint-positive families.

A group is a `threeway_group` iff it contains at least one three-way family. Its recoverability is evaluated using only the three-way families in that group.

A `joint_only_group` is a joint-positive group containing no three-way family. Its recoverability is evaluated using its joint-only families.

Report counts, recoverable counts, and recoverable fractions.

Group-level refinement passes iff

`P(recoverable | threeway_group) > P(recoverable | joint_only_group)`.

Truth-aware group identity is diagnostic only and cannot enter any later candidate rule.

## Binding interpretation gate

The exact three-way full-universe refinement direction passes only if **all** of the following hold:

1. the truth-free three-way family count is at least 1 and strictly less than 60, so the third sign genuinely prunes the frozen #1098 gate without selecting an empty set;
2. the family-level refinement inequality passes in both 2013 and 2014;
3. the strict diagnostic-group-level refinement inequality passes in both 2013 and 2014.

No minimum effect size, maximum selector size, significance threshold, odds-ratio cutoff, required number of recovered families, oracle cardinality, literature budget, or panel score is selected.

A PASS means only that the direct cross-route sign is a defensible **selector refinement** of the fixed #1098 gate. Combined with the separately frozen #1113 component-priority diagnostic, it may justify one separately frozen successor architecture. It does not authorize that successor automatically.

A FAIL closes categorical use of this exact three-way selector refinement. Do not rescue it with magnitude thresholds, OR/XOR logic, pairwise fallback, edge-distance cutoffs, top-k, rank windows, component-size conditions, year/budget exceptions, or post-result alternative Boolean combinations.

## Explicit non-search commitments

No:

- new candidate total order or literature panel evaluation;
- placement/promotion key;
- replacement rule;
- threshold/effect-size search;
- top-k or rank-window selection;
- direct-neighbor distance/overlap/count rule;
- alternate neighbor aggregation;
- alternate Boolean combination;
- component-size/q statistic;
- quality-suppression magnitude transform;
- route/year/budget-specific action;
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
