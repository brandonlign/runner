# OrbitTrace v31 three-way consensus diagnostic v1

## Scientific role

Post-result exposed-SonotaCo diagnostic only after:

- #1091 showed that `(quality_suppression > 0) AND component_closure_opportunity` is strongly enriched among recoverable HDB groups missed by exact v31;
- #1093 independently showed that `(quality_suppression > 0) AND (crossroute_rank_gap > 0)` is enriched among missed recoverable HDB groups;
- #1098 showed the #1091 candidate-level AND survives a full-universe selectivity audit but is broad (60/229 HDB families);
- v42 showed that direct full-quality-rank placement of the broad #1091 gate selects harmful tiny-budget entrants;
- v43 showed that the conservative shared-support placement leaves the top-9/top-11 memberships unchanged.

The remaining question is selector specificity, not promotion strength. This diagnostic tests exactly one parameter-free refinement: whether recoverable groups missed by v31 preferentially satisfy **all three already-frozen positive directions simultaneously**.

No new rank, score, selector order, replacement rule, literature panel, promotion position, or successor is evaluated.

## Immutable sources

Consume only the authoritative completed diagnostic results:

1. #1091, first valid run `31456963941`, artifact `9088402091`, result SHA-256 `2edb949dbab2d7cbf6ed5e808e2a049116eb0934b25b356572463b615d730842`.
   - exact fields: `positive_quality_suppression`, `component_closure_opportunity`, `joint_signal`;
   - exact joint definition: `(quality_suppression > 0) AND component_closure_opportunity`.

2. #1093, valid repaired run `31457199102`, artifact `9088482597`, result SHA-256 `62ed82eeb4f10b4371ec2072af7de527482ab070866693a2230be564ebf6af35`.
   - exact fields: `quality_positive`, `crossroute_positive`, `concordant_positive`;
   - exact direct cross-route sign: `crossroute_rank_gap > 0`.

Require exact agreement between sources, separately in 2013 and 2014, on:

- the 18 annual-recoverable strict HDB groups;
- representative family identity;
- exact v31 rank;
- surfaced/missed status;
- quality-positive sign and quality-suppression value.

No representative may be reselected and no source statistic may be recomputed or transformed.

## Sole diagnostic statistic

For each frozen annual recoverable-group representative define exactly:

`threeway_positive = positive_quality_suppression AND component_closure_opportunity AND crossroute_positive`.

Equivalently, it is the #1091 joint-positive condition intersected with the already-frozen positive direct cross-route rank-disagreement sign from #1093.

No magnitude, sum, product, ratio, rank window, top-k, component size, threshold beyond the already-frozen strict zero signs, OR/XOR rule, pairwise alternative, or weighted Boolean combination is authorized.

## Frozen summaries

Separately for 2013 and 2014, preserve the exact 9 surfaced / 9 missed recoverable-group split and report for each class:

- group count;
- #1091 joint-positive count/fraction;
- #1093 direct-crossroute-positive count/fraction;
- three-way-positive count/fraction;
- complete audit rows with group, representative, v31 rank, surfaced flag, the three Boolean source signs, and the two frozen continuous diagnostics (`quality_suppression`, `crossroute_rank_gap`) for provenance only.

## Predeclared interpretation gate

The three-way selector direction is supported only if **both** conditions hold in **both 2013 and 2014**:

1. at least one missed recoverable group is `threeway_positive`; and
2. the three-way-positive fraction among missed recoverable groups is strictly greater than the three-way-positive fraction among surfaced recoverable groups.

No minimum effect size, required cardinality beyond one, significance threshold, maximum selector size, or oracle-based target count is selected.

A PASS does not authorize a deployable order. It may justify one separately frozen full-universe three-way audit before any successor ranking is evaluated.

A FAIL closes this exact three-way conjunction. Do not rescue it with OR logic, pairwise fallback, magnitude cutoffs, top-k, rank windows, component-size rules, year/budget exceptions, or post-result alternate Boolean combinations.

## Explicit non-search commitments

No new feature/model/rank/fusion/graph/component/candidate/membership change; no signal transform; no threshold/effect-size search; no alternative Boolean-combination search; no selector order; no promotion position; no literature panel evaluation; no source quota; no oracle identity rule; no post-result second statistic.

## Firewall

- SonotaCo 2013/2014 remains `EXPOSED_DEVELOPMENT_ONLY`.
- Protected OrbitTrace solar longitude `20°–55°` remains inaccessible.
- No OrbitTrace target information or target-region events may be accessed.
- No MAARSY or DMS scientific access is authorized.
- Oracle identities from #1050/#1053/#1071 may not define the statistic or gate.
