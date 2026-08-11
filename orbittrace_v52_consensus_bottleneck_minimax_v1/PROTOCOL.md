# OrbitTrace v52 consensus-bottleneck minimax fusion v1

## Scientific role

Separately frozen exposed-development successor after binding v51 consensus-bottleneck diagnostic PASS. Exact v31 remains the parent.

v51 reproduced exact v31 and captured the two already-frozen HDB inputs to v31's final equal rank-sum fusion: the v31 local-geometry/diversity order and immutable v19 order. Across all 229 HDB families, the sole diagnostic statistic `consensus_bottleneck = max(local_rank_percentile, v19_rank_percentile)` was dramatically lower among annual recoverable than nonrecoverable families in both 2013 and 2014. v51 evaluated no successor order.

v52 makes exactly one scientific change to exact v31:

- Sugar remains exact v31, including the existing equal rank-sum fusion;
- HDB replaces only the final equal rank-sum of the exact same two constituent orders with a minimax consensus order;
- for each HDB family, define `b = max((local_rank-1)/228, (v19_rank-1)/228)`;
- sort all 229 HDB families by `(b, exact_v31_fused_rank, family_id)`, lower first.

The exact-v31 fused rank is only a deterministic parent-preserving tie-break when two families have identical bottleneck. No coefficient, threshold, top-k, Pareto layer, or budget rule is introduced.

SonotaCo 2013/2014 remains `EXPOSED_DEVELOPMENT_ONLY`, not external validation.

## Immutable authorizer

Before current outcome truth is used to evaluate v52, pin authoritative v51:

- run `31493423814`;
- artifact `9101972590`;
- artifact digest `sha256:56258a0be52d83c0d6dbfcffdb9fd9a2c6b73587ba8d92d7bdccdef9729868c9`;
- execution head `3da2587e569a7487db51df2ad1e2624b75e88c61`;
- captured vector `capture/V51_V31_CONSENSUS_BOTTLENECK_VECTOR.json`, SHA-256 `5f20a8bedb6e7b8d6c06d66e45d5037057a9853ded35a2b360333d6ea5e2c4cc`;
- diagnostic result `diag/V51_V31_CONSENSUS_BOTTLENECK_DIAGNOSTIC.json`, SHA-256 `fef1d2c5bb83748de5c5511615915e76ce6fcd0801afbddb0e01bab09b9ab76d`;
- captured local HDB order SHA `9898a2ad69f251595b0de4ce5763ffb6641ad27141b6e54f839ebe240eb94595`;
- exact-v31 HDB fused order SHA `85ac3f29a443c35b3812cf28c99ef13474fc3e0455458e20b41cec64d942073d`.

Require v51 verdict `PASS_V51_V31_CONSENSUS_BOTTLENECK_DIAGNOSTIC`, role `POST_V31_INTERNAL_CONSENSUS_BOTTLENECK_DIAGNOSTIC_ONLY_NO_SUCCESSOR_EVALUATED`, 229-family vector identity, both annual median directions, and all explicit no-successor/no-rank/no-threshold/no-budget-search flags.

## Complete truth-blind order freeze

Before evaluating the current v52 outcome, construct the complete HDB order using only the frozen v51 capture vector and its exact-v31 fused order:

1. require exactly 229 unique HDB identities;
2. require every local/v19 rank to be a permutation of `1..229`;
3. recompute each bottleneck exactly as `max((local_rank-1)/228,(v19_rank-1)/228)` and require equality with v51's captured value;
4. reconstruct exact-v31 fused ranks from the frozen v31 order;
5. sort by `(consensus_bottleneck, exact_v31_fused_rank, family_id)`.

Freeze the entire order before current outcome evaluation. The exact frozen v52 HDB order SHA-256 is:

`75fb44015e348c6b1bf0367e74db8e273e29862e132b5ef3305b2ddb409d8cc7`.

Truth-blind structural consequences of this sole rule are frozen descriptively:

- 217/229 final positions differ from exact v31;
- 117 families move upward;
- 100 move downward;
- 12 are unchanged;
- maximum upward displacement is 55 ranks;
- maximum downward displacement is 71 ranks.

At the two already-existing literature budgets, the frozen rule happens to alter each HDB prefix by exactly one family. This is a descriptive consequence only and does not define the order, select a family, or authorize a budget-specific rule.

## Evaluation

The workflow must reproduce all four exact v31 controls first using the frozen parent implementation.

Then evaluate exactly one v52 method:

- Sugar execution must remain byte-identical to exact v31;
- HDB must use the same exact local/diversity and immutable v19 constituent orders captured by v51;
- the runtime HDB v52 order must equal the pre-frozen SHA `75fb44015e348c6b1bf0367e74db8e273e29862e132b5ef3305b2ddb409d8cc7` exactly.

PASS requires all four existing SonotaCo literature pair gates. The first technically valid outcome is binding.

## Explicit prohibitions

No mean/rank-sum blend with bottleneck, coefficient, exponent, softmax, geometric mean, alternate max/min convention, Pareto front, threshold, quantile, top-k, rank window, budget/year/route exception, alternate tie-break, direct local-only or v19-only order, diversity retuning, feature/model/k/metric/scaling change, component/quality signal, source quota, oracle identity, boundary rescue list, or post-result second search is authorized.

If v52 fails, the exact minimax consensus-bottleneck fusion is permanently closed.

## Firewall

Protected OrbitTrace solar longitude `20°–55°` remains inaccessible. Do not access OrbitTrace target information or target-region events. Do not access MAARSY or DMS scientifically. Every output must assert these conditions and `SonotaCo = EXPOSED_DEVELOPMENT_ONLY`.
