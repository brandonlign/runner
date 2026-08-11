# OrbitTrace v53 local-v19 Pareto-dominator diagnostic v1

## Scientific role

This is a post-v52 **exposed-development mechanism diagnostic only**. It does not define, evaluate, select, or authorize a successor ranking.

Binding context before this diagnostic:

- v31 remains the parent;
- v51 showed across all 229 fixed HDB families that annual-recoverable families have substantially lower `max(local_rank_percentile, v19_rank_percentile)` in both exposed years;
- v52 then translated that mechanism into one frozen lexicographic minimax total order and bindingly failed 2/4, degrading both HDB panels despite changing only one membership in each tiny literature prefix.

Therefore the v51 population signal is real, but the particular v52 scalarization is closed. This diagnostic asks a different, purely ordinal two-dimensional question without choosing another total order:

> **Across the complete fixed 229-family HDB universe, are annual-recoverable families Pareto-dominated by fewer other families in the exact-v31 local-rank × v19-rank plane?**

For family `i` with exact integer ranks `(r_local_i, r_v19_i)`, define the sole statistic

`pareto_dominator_count(i) = # {j != i : r_local_j <= r_local_i AND r_v19_j <= r_v19_i AND at least one inequality is strict}`.

Lower is better. A count of zero means the family lies on the first nondominated frontier, but **frontier membership is not itself the diagnostic and no frontier/Pareto order is evaluated**.

The statistic is parameter-free and invariant to monotone rescaling of either exact-v31 input rank. It is distinct from v51's worst-rank scalar and from v52's minimax total order.

SonotaCo 2013/2014 remains `EXPOSED_DEVELOPMENT_ONLY`, not external validation.

## Immutable source vector

Use only the binding v51 capture artifact:

- run `31493423814`;
- artifact `9101972590`;
- artifact digest `sha256:56258a0be52d83c0d6dbfcffdb9fd9a2c6b73587ba8d92d7bdccdef9729868c9`;
- vector SHA-256 `5f20a8bedb6e7b8d6c06d66e45d5037057a9853ded35a2b360333d6ea5e2c4cc`;
- vector canonical SHA-256 `0e13b3f9e6b791a13a3e90d853f8704573b1264dffcb67236e6423491ad70020`;
- v51 diagnostic result SHA-256 `fef1d2c5bb83748de5c5511615915e76ce6fcd0801afbddb0e01bab09b9ab76d`, verdict `PASS_V51_V31_CONSENSUS_BOTTLENECK_DIAGNOSTIC`.

Require exactly 229 unique family identities. Require both `local_rank` and `v19_rank` to be complete permutations of integers 1..229. Require the established input-order identities:

- local SHA `9898a2ad69f251595b0de4ce5763ffb6641ad27141b6e54f839ebe240eb94595`;
- v19 SHA `e1e82ad70fb8c575ee7ee269906668931f07cbe3375c15ab84b0717b1f2c85dc`;
- exact-v31 fused SHA `85ac3f29a443c35b3812cf28c99ef13474fc3e0455458e20b41cec64d942073d`.

The v51 vector must contain no diagnostic recoverability labels or annual own-family F1.

## Frozen Pareto-dominator vector

Before current v53 diagnostic truth is attached, compute `pareto_dominator_count` for **all 229 families** using only the frozen local/v19 ranks.

For each family serialize only:

- family identity;
- exact local rank;
- exact v19 rank;
- Pareto-dominator count.

Require, as truth-blind structural identities fixed before outcome:

- minimum dominator count `0`;
- maximum dominator count `188`;
- exactly `133` distinct dominator-count values.

These are integrity consequences of the complete frozen v51 rank plane, not selection thresholds.

The vector must not contain current annual F1, recoverability, literature budget, boundary identity, v52 substituted identity, component/quality/topology signal, target information, MAARSY information, DMS information, or any proposed successor rank/order.

## Sole truth-aware diagnostic

Only after the complete 229-family Pareto-dominator vector is frozen, restore the same immutable #950 HDB memberships and exposed SonotaCo truth used by the established diagnostics.

For each family reproduce the existing own-family annual-F1 semantics exactly:

1. derive the fixed best label with the existing `family_truth` implementation over both exposed years;
2. if positive with a fixed label, compute annual F1 with the existing `annual_f1_for_fixed_label`; otherwise annual F1 is zero;
3. define annual recoverability by the already-established criterion `annual_f1 > 0.5`.

For each year separately, split the complete fixed 229-family population into recoverable and nonrecoverable classes. Both must be nonempty.

The sole preregistered gate is:

`median(pareto_dominator_count | recoverable) < median(pareto_dominator_count | nonrecoverable)`.

PASS requires this strict direction in **both 2013 and 2014**.

Quartiles/min/max may be reported descriptively for the two already-defined classes but do not enter PASS/FAIL.

No representative-group aggregation, AUC, correlation, regression, p-value, frontier-membership test, Pareto-layer test, alternate dominance convention, threshold, quantile, top-k, rank window, literature-budget analysis, or successor panel evaluation is authorized.

## Interpretation

PASS supports only:

> Annual-recoverable HDB families tend to be dominated by fewer alternatives simultaneously better in both exact-v31 constituent ranks, in both exposed years.

PASS does **not** automatically authorize ranking by dominator count, Pareto depth, nondominated layers, or any other total order. A successor would require its own separately frozen truth-blind total-order rule.

FAIL permanently closes this exact dominator-count mechanism diagnostic. Do not rescue it with weak/strict dominance variants, Pareto layers, frontier-only tests, weighted dominance, group aggregation, thresholds, or year-specific use.

## Explicit prohibitions

No new candidate order, selector, replacement, Pareto/frontier successor, dominator-count literature ranking, threshold, quantile, top-k, rank window, budget/year exception, alternate dominance convention, fusion weight, rank algebra, component/quality/topology rescue, v52 identity rescue, boundary identity, oracle family, feature/model/k/metric/scaling/diversity search, or post-result second search.

## Firewall

Protected OrbitTrace solar longitude `20°–55°` remains inaccessible. Do not access OrbitTrace target information or target-region events. Do not access MAARSY or DMS scientifically. Every output must assert these conditions and `SonotaCo = EXPOSED_DEVELOPMENT_ONLY`.
