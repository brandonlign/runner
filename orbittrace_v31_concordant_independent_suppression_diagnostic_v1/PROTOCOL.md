# OrbitTrace v31 concordant independent-suppression diagnostic v1

## Scientific role

Post-result exposed-SonotaCo diagnostic only after #1066 and #1086 independently identified two one-sided signals associated with recoverable HDB groups missed by exact v31, while broad cross-route component rerankers v39/v40/v41 failed.

The joint nested oracle #1071 proves one deployable HDB ranking extremely close to v31 can clear both exposed HDB panels: only one top-9 replacement and two top-11 replacements are required. Therefore the remaining need is a sparse, selective correction signal, not another global rerank.

This diagnostic tests one parameter-free conjunction of the two already-frozen independent signals. It evaluates no new candidate order, threshold, selector, replacement, panel score, or successor.

## Immutable source diagnostics

Consume only the authoritative completed artifacts:

1. **Cross-route rank disagreement #1066**
   - run `31454523913`;
   - artifact `9087524827`;
   - source result `V31_CROSSROUTE_RANK_DISAGREEMENT_DIAGNOSTIC.json`;
   - exact signal `crossroute_rank_gap = p_hdb - p_sugar`, where positive means the frozen Sugar radius-1 physical neighbor is ranked better than the HDB representative.

2. **Frozen-quality suppression #1086**
   - run `31456339844`;
   - artifact `9088169870`;
   - digest `sha256:b0f9499280f9e8cc4d1f6f8a04d4871a306ea085a8eaee03bba0d002c35d5641`;
   - exact signal `quality_suppression = p_v31 - p_quality`, where positive means the immutable pre-SonotaCo #839/#853 quality prior ranks the same HDB representative better than exact v31.

Require both source diagnostics to retain their diagnostic-only roles, exact annual 18-group / 9 surfaced / 9 missed structure, and all protected-data access flags false.

For each year and strict recoverable HDB shower group, require the group name, HDB representative family identity, exact v31 rank, and surfaced/missed flag to agree between the two authoritative source artifacts. No representative may be reselected.

## Sole diagnostic statistic

For each frozen annual recoverable-group representative define exactly two Boolean signs:

- `crossroute_positive = crossroute_rank_gap > 0`;
- `quality_positive = quality_suppression > 0`.

Define exactly one conjunction:

`concordant_positive = crossroute_positive AND quality_positive`.

If #1066 records no usable Sugar rank for a representative, `crossroute_positive=false`.

No magnitude, sum, product, ratio, absolute value, coefficient, weight, threshold other than the mathematically fixed zero sign, rank window, top-k, component size, or alternative Boolean combination is authorized.

## Truth-aware descriptive grouping

Preserve the already-frozen surfaced/missed classification from the source diagnostics separately for 2013 and 2014.

For surfaced and missed recoverable groups report:

- group count;
- cross-route-positive count/fraction;
- quality-positive count/fraction;
- concordant-positive count/fraction;
- representative audit rows with both frozen continuous signals and all three Boolean flags.

## Predeclared interpretation gate

The concordant-independent-suppression direction is supported only if **both** conditions hold in **both 2013 and 2014**:

1. at least one missed recoverable group is `concordant_positive`; and
2. the concordant-positive fraction among missed recoverable groups is strictly greater than the concordant-positive fraction among surfaced recoverable groups.

No minimum effect size, significance cutoff, required cardinality beyond one, or oracle-based target count is selected.

A PASS does not authorize a deployable order. Any successor must separately freeze how the candidate-wise sign conjunction is computed for the full fixed HDB universe and how it can alter v31 while preserving the sparse-correction lesson from #1071.

If the gate fails, this exact dual-positive conjunction is rejected. Do not rescue it with OR logic, weighted sums, nonzero cutoffs, top-k, rank windows, component-size conditions, year/budget exceptions, or post-result alternative combinations.

## Non-search commitments

No new feature/model/rank/fusion/graph/component/candidate/membership change; no signal transform; no cutoff search; no top-k/rank-window search; no route/year/budget-specific successor; no source quota; no oracle identity rule; no post-result second statistic.

## Firewall

- SonotaCo 2013/2014 remains `EXPOSED_DEVELOPMENT_ONLY`.
- Protected OrbitTrace solar longitude `20°–55°` remains inaccessible.
- No OrbitTrace target information or target-region events may be accessed.
- No MAARSY or DMS scientific access is authorized.
- Truth-aware identities from #1050/#1053/#1071 cannot define the conjunction, gate, or any later deployable rule.
