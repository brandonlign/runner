# OrbitTrace v38 positive-archetype diminishing-returns selector

## Scientific role

Separately frozen exposed-SonotaCo development successor after v31 and the failed v36/v37 successors.

The remaining HDB bottleneck is fixed-budget shower-set selection inside the already-sufficient fixed candidate universe (#1050). Diagnostic #1058 then found a concrete truth-free set-level defect in exact v31: its selected HDB prefixes repeatedly spend scarce slots on candidates supported by the same ordered pair of annual nearest-positive training shower groups.

At HDB 2013 budget 11, exact v31 uses only 6 distinct positive-reference archetype signatures, leaving 5 duplicate slots; 7/9 recoverable-but-missed strict groups have a signature absent from the selected prefix. At HDB 2014 budget 9, exact v31 uses only 5 signatures, leaving 4 duplicate slots; again 7/9 recoverable-but-missed groups have an absent signature. #1058 evaluated no new rank or replacement rule.

v38 tests exactly one parameter-free set-selection response: retain exact v31 fused rank as the quality prior, but apply reciprocal-rank-style diminishing returns to repeated positive-reference archetype signatures. It is deliberately softer than hard de-duplication: a highly ranked repeat may still beat a much weaker new signature.

SonotaCo 2013/2014 remains exposed development only. A pass is not external validation.

## Immutable v31 computation

Reproduce exact v31 using:

- immutable #950 71D pretruth features and fixed family memberships;
- exact shared deterministic strict-whole-shower five-fold assignment across Sugar and HDBSCAN;
- fold-training mean / population-standard-deviation z-scoring across all 71 dimensions, zero standard deviation replaced by 1.0;
- annual positive definition `F1_y > 0.5` for the fixed best shower label;
- ordinary Euclidean `k=1` nearest annual-positive and annual-nonpositive references;
- annual margin `d_nonpositive - d_positive`;
- exact annual `min` combiner;
- exact #839 diversity (`lambda=0.8`, `scale=1.0`);
- exact one equal rank-sum with frozen v19.

The resulting exact v31 fused order is the sole base quality order.

## Positive-reference archetype signature

While computing the unchanged v31 annual nearest-positive distance, record the strict group identity of the exact nearest annual-positive fold-training family in each year. Strict whole-shower leakage remains prohibited because the held-out candidate's strict shower group is absent from its fold training references.

For each candidate define exactly one ordered signature:

`A(i) = (nearest_positive_group_2013(i), nearest_positive_group_2014(i))`.

The pair is ordered by year. No unordered version, one-year version, family identity, distance threshold, hierarchy collapse, similarity merge, graph merge, source field, or alternate signature is authorized.

## Sole v38 scientific change

Let `r(i)` be candidate `i`'s one-indexed rank in the exact v31 fused order. Construct a new total order greedily.

Initially no candidates are selected and every signature count is zero. At each position, for every unselected candidate compute

`priority(i) = r(i) * (1 + n_selected(A(i)))`,

where `n_selected(A(i))` is the number of already-selected candidates with exactly the same ordered signature.

Select the candidate with the smallest priority. Break an exact priority tie by the smaller original v31 fused rank. Increment only that signature's selected count and repeat until all candidates are ordered.

Equivalently, the exact v31 reciprocal-rank quality `1/r` receives the canonical harmonic diminishing-return factor `1/(1+n)` for repeated evidence archetypes. There is no coefficient, exponent, temperature, threshold, cap, window, budget dependence, route-specific rule, or randomization.

The same algorithm is applied independently to the Sugar candidate order and the HDBSCAN candidate order. Evaluation remains by the frozen literature top-budget prefixes, but the v38 total order itself does not use the panel budget or year.

## Parent control

The technically valid run must reproduce exact v31 before evaluating v38:

- Sugar 2013: `0.2719801488280529 / 16`;
- Sugar 2014: `0.31529041952487225 / 17`;
- HDBSCAN 2013: `0.14888037368183737 / 9`;
- HDBSCAN 2014: `0.15198123772301594 / 9`.

Any mismatch is an engineering/provenance failure and yields no v38 scientific outcome.

## Binding development gate

Exactly one v38 total order per route is evaluated. The first technically valid outcome is binding.

A panel wins only if:

- candidate macro-F1 is strictly greater than the frozen literature comparator; and
- recovered `F1 > 0.5` shower count is at least the literature comparator.

Development PASS requires 4/4 panel wins.

If v38 fails, this exact multiplicative occurrence-count diminishing-return rule is permanently rejected. No alternate coefficient, additive penalty, hard de-duplication, signature cap, occurrence exponent, budget-normalized penalty, rank window, threshold, signature variant, route-specific version, feature/metric/k/scaling change, annual combiner, diversity/fusion change, source quota, or post-result rescue is authorized within v38.

If v38 passes 4/4, freeze only the exact exposed-development reference material required to reproduce its full-training application. A pass does not authorize protected validation or an external-superiority claim.

## Firewall

- Protected OrbitTrace solar longitude `20°–55°` remains inaccessible.
- No OrbitTrace target information or target-region events may be accessed.
- No MAARSY or DMS scientific access is authorized.
- Truth-aware identities from #1050/#1053 may not enter the v38 score, signature, selector, code path, or freeze.
- Candidate generation and memberships remain unchanged.
- SonotaCo is `EXPOSED_DEVELOPMENT_ONLY`.
