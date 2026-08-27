# OrbitTrace v31 internal v19-suppression diagnostic v1

## Scientific role

Post-result exposed-development mechanism diagnostic only. This diagnostic does not define, evaluate, select, or authorize a successor ranking.

Exact v31 is an equal rank-sum of two already-frozen constituent orders after the local-geometry leg's fixed #839 diversity step:

1. the v31 local-geometry/diversity order;
2. the immutable v19 order.

The residual HDB problem is known from #1053 to require only a small 1–2 shower-group correction at the fixed budgets, while broad external quality/component promotion lines have repeatedly failed. #1046 already froze, for every eligible HDB shower group, the exact ranks of its best fixed candidate in the raw local-margin, diversity, v19, and final v31 fused orders together with the surfaced/missed recoverability status. It evaluated no constituent-disagreement statistic or successor.

This diagnostic asks one internal question:

> Are recoverable-but-missed HDB shower groups specifically those for which the independent v19 leg ranks the group's frozen best candidate substantially better than the v31 local-geometry/diversity leg does?

The sole statistic is

`v19_advantage = ((diversity_rank - 1) / 228) - ((v19_rank - 1) / 228)`.

Positive values mean v19 ranks the frozen candidate better than the local-geometry/diversity leg. The denominator merely normalizes the two ranks over the fixed 229-family HDB universe; no fitted coefficient or threshold is introduced.

SonotaCo 2013/2014 remains `EXPOSED_DEVELOPMENT_ONLY`, never external validation.

## Immutable source

Use only authoritative #1046:

- run `31451236076`;
- artifact `9086399760`;
- artifact ZIP digest `sha256:a2c373df77ef7e0065c1d8aceb1f6e5826f1e30b6286f2331c362d959f1d7f69`;
- result file `diag/V31_HDB_MISSED_LABEL_RANKGAP_DIAGNOSTIC.json` SHA-256 `e4e09546e17b9a5da7ce12ad9af4bb7129533fd9b5be846ebc859719f01a9758`;
- execution commit `2dd05e8d42a9620a015ea7ca880cc436c32a49d6`.

Require #1046 to reproduce exact v31 HDB controls:

- 2013: `0.14888037368183737 / 9`, budget 11;
- 2014: `0.15198123772301594 / 9`, budget 9.

Require #1046 role `POST_RESULT_DIAGNOSTIC_ONLY_NO_SUCCESSOR_SELECTED`, verdict `PASS_V31_HDB_MISSED_LABEL_RANKGAP_DIAGNOSTIC`, and its prohibitions on new rank/cutoff/threshold/parameter search and protected-data access.

The diagnostic consumes #1046's already-frozen annual rows unchanged. It does not reselect a family within a truth group, recompute candidate memberships, or use #1053 oracle identities.

## Frozen comparison

Independently for 2013 and 2014:

- `surfaced` = rows with `v31_surfaced_recoverable == true`;
- `missed` = rows with `recoverable_but_missed == true`.

For every row in those two strata, compute exactly the single `v19_advantage` above from the stored `best_candidate_diversity_rank` and `best_candidate_v19_rank`.

Report for each stratum:

- count;
- median, mean, q25, q75, minimum, maximum `v19_advantage`;
- count/fraction with strictly positive advantage;
- the complete frozen per-group rows plus derived advantage.

The sole preregistered direction passes for a year iff BOTH:

1. `median(v19_advantage | missed) > 0`;
2. `median(v19_advantage | missed) > median(v19_advantage | surfaced)`.

The diagnostic PASS requires that direction in both 2013 and 2014. No effect-size threshold is selected.

## Interpretation boundary

PASS supports only the mechanism statement that v31's equal fusion is internally suppressing some recoverable HDB groups that the independent v19 leg ranks more favorably than the local-geometry/diversity leg, consistently across both exposed years.

PASS does not authorize direct v19 promotion, a rank-difference threshold, top-k correction, budget-specific replacement, route/year exception, oracle identity list, or successor order. A candidate-level full-universe audit would still be required before any separately frozen successor.

FAIL closes this exact internal constituent-disagreement mechanism. No absolute-value, ratio, log transform, raw-local instead of diversity rank, fused-rank difference, threshold, quantile, alternative summary, or post-result second test may rescue it.

## Explicit prohibitions

No new candidate order, score used for ranking, selector, replacement, literature panel, successor, rank-gap threshold, top-k, rank window, effect-size cutoff, fusion-weight search, alternate constituent pair, feature/model/k/metric/scaling/diversity change, source quota, oracle identity, boundary rescue list, or post-result second search.

## Firewall

Protected OrbitTrace solar longitude `20°–55°` remains inaccessible. Do not access OrbitTrace target information or target-region events. Do not access MAARSY or DMS scientifically. Every output must assert these conditions and `SonotaCo = EXPOSED_DEVELOPMENT_ONLY`.
