# OrbitTrace v54 full-universe v19-advantage diagnostic v1

## Scientific role

This is a post-v52/post-#1157 **exposed-development mechanism diagnostic only**. It does not define, evaluate, select, or authorize a successor ranking.

Binding state entering this diagnostic:

- exact v31 remains the strongest 2/4 parent;
- v52 lexicographic minimax fusion is permanently rejected at 2/4;
- #1157 `PASS_V31_INTERNAL_V19_SUPPRESSION_DIAGNOSTIC` established, on the already-frozen #1046 recoverable-group representatives, that recoverable-but-missed HDB groups tend to have substantially larger positive `v19_advantage` than surfaced recoverable groups in both 2013 and 2014;
- #1157 explicitly does not authorize a v19 promotion rule and requires a full-universe candidate-level audit first.

The present diagnostic performs exactly that audit on the complete fixed 229-family HDB universe.

SonotaCo 2013/2014 remains `EXPOSED_DEVELOPMENT_ONLY`, not external validation.

## Immutable inputs

Use only:

1. binding v51 rank-vector artifact from run `31493423814`, artifact `9101972590`, ZIP SHA-256 `56258a0be52d83c0d6dbfcffdb9fd9a2c6b73587ba8d92d7bdccdef9729868c9`;
2. exact v51 vector file SHA-256 `5f20a8bedb6e7b8d6c06d66e45d5037057a9853ded35a2b360333d6ea5e2c4cc`, canonical SHA-256 `0e13b3f9e6b791a13a3e90d853f8704573b1264dffcb67236e6423491ad70020`;
3. binding #1157 run `31495853601`, artifact `9102914767`, ZIP SHA-256 `2441cb6fb4401601976ada3feb59db6cf658bc8eba4f0e5a3bc06b743aa8c167`, diagnostic-result SHA-256 `165f094fafa0f0f1e78b57dca83fbbf2aeee5d15bdefc9ba4b6f349d495e0aa7`;
4. immutable #950 pretruth HDB payload artifact `9074742322`, ZIP SHA-256 `d940fa255804866f14bc34b1d72467d17adddcfb7d82c954ed5a8d1668aa307a`;
5. immutable exposed SonotaCo truth artifact `9069505548`, ZIP SHA-256 `cdea3297c234b0b3a8f09c2208649c8607bb3e9a9004d299f6dcc18536ebb797`.

The #1157 artifact is an authorizer only. Its surfaced/missed identities, budgets, group labels, and annual F1 values must not enter the v54 full-universe split or statistic.

## Frozen pre-outcome candidate split

For every one of the 229 fixed HDB families, use only the two already-frozen v51 constituent ranks:

- `local_rank_percentile = (local_rank - 1) / 228`;
- `v19_rank_percentile = (v19_rank - 1) / 228`.

Define exactly one statistic:

`v19_advantage = local_rank_percentile - v19_rank_percentile`.

Define exactly one natural binary split:

- `POSITIVE_V19_ADVANTAGE` iff `v19_advantage > 0`, equivalently `v19_rank < local_rank`;
- `NONPOSITIVE_V19_ADVANTAGE` otherwise.

Zero is not a tuned threshold. It is the exact constituent-rank crossing where the immutable v19 leg begins ranking a candidate more favorably than the exact-v31 local/diversity leg.

Before current diagnostic annual recoverability is attached, serialize all 229 family identities with only local rank, v19 rank, normalized ranks, `v19_advantage`, and the binary split. Require the complete population and both classes to be nonempty. Freeze this vector before loading the current diagnostic truth artifact.

No rank window, literature budget, top-k, boundary identity, #1046/#1157 surfaced/missed identity, group label, component/quality/topology signal, annual F1, or recoverability label may enter this split.

## Sole truth-aware diagnostic

After the complete 229-family split is frozen, restore immutable #950 memberships and exposed truth and use the already-established exact own-family semantics:

1. derive each family's fixed best truth label with the existing `family_truth` implementation;
2. if positive with a fixed label, calculate annual F1 using the existing `annual_f1_for_fixed_label`; otherwise annual F1 is zero;
3. annual recoverability is the already-established fixed criterion `annual_f1 > 0.5`.

For each year separately calculate:

- recoverability fraction among `POSITIVE_V19_ADVANTAGE` families;
- recoverability fraction among `NONPOSITIVE_V19_ADVANTAGE` families.

The sole preregistered gate is:

`recoverability_fraction(POSITIVE_V19_ADVANTAGE) > recoverability_fraction(NONPOSITIVE_V19_ADVANTAGE)`

in **both 2013 and 2014**.

PASS requires both strict inequalities. No effect-size threshold is selected.

## Interpretation

PASS supports only:

> Across the complete fixed HDB candidate universe, the natural constituent disagreement `v19_rank < local_rank` enriches annual recoverability in both exposed years, consistent with #1157's observation that equal v31 fusion suppresses some recoverable groups favored by v19.

PASS does not itself authorize a v19-only order, best-rank/minimum-rank fusion, promotion, threshold, top-k correction, rank-window rule, budget replacement, weighted fusion, or any other successor. Any successor must be separately named and its complete total order frozen before first literature evaluation.

FAIL permanently closes this exact full-universe positive-v19-advantage enrichment mechanism. Do not rescue it with a nonzero advantage threshold, absolute gap, quantile, ratio, year-specific split, group aggregation, top-k restriction, or alternative constituent pair.

## Explicit prohibitions

No new candidate order, selector, replacement rule, v19-only evaluation, minimum/best-rank order, weighted or nonlinear fusion, threshold search, quantile search, rank window, literature budget analysis, boundary identity, #1046/#1157 missed identity, group aggregation, AUC, correlation, regression, p-value, component/quality/topology rescue, feature/model/k/metric/scaling/diversity/source-quota search, or post-result second search.

## Firewall

Protected OrbitTrace solar longitude `20°–55°` remains inaccessible. Do not access OrbitTrace target information or target-region events. Do not access MAARSY or DMS scientifically. Every output must assert these conditions and `SonotaCo = EXPOSED_DEVELOPMENT_ONLY`.
