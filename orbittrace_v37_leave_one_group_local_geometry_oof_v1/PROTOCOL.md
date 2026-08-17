# OrbitTrace v37 leave-one-strict-shower-group-out local-geometry ranker

## Scientific role

Separately frozen exposed-SonotaCo development successor after v31 and failed v36. v31 remains the strongest genuine method at 2/4; v36's density-normalized distance contrast is permanently rejected.

The motivating evidence is structural rather than result tuning:

- #1020/#1021 found that missed HDB recoverable shower groups have weaker fold-training support/local geometry than surfaced groups.
- #1050 proved that the fixed HDB candidate universe is sufficient to beat HDBSCAN at the exact 11/9 budgets.
- #1053 localized the residual v31 failure to a small number of wrong/missing shower groups at those budgets.
- v36 showed that merely normalizing the absolute distance scale does not solve the problem.

v31's deterministic five-fold OOF evaluation excludes the held-out shower group **and every unrelated shower group assigned to the same fold**. That is stricter than the deployment situation for a genuinely unseen shower, where the new shower itself is absent from training but unrelated exposed-development shower groups remain available. Because the diagnosed failure is specifically weak training support, this coarse-fold removal can create artificial reference starvation.

v37 therefore changes exactly the anti-leakage reference construction: each strict shower group is scored leave-one-group-out against **all and only** families from every other strict group across both routes. This is maximal training support subject to the same no-same-shower leakage rule.

SonotaCo 2013/2014 remains exposed development only. A success is not external validation.

## Immutable scientific components

Keep exactly from v31:

- immutable #950 71D pretruth features, fixed family memberships, candidates, centroids and v19 order;
- strict group identities shared across Sugar and HDBSCAN so every family tied to shower X is excluded together;
- annual positive labels `F1_y > 0.5` for the fixed best shower label;
- ordinary Euclidean distance over all 71 dimensions;
- training-reference mean / population-standard-deviation z-scoring with zero standard deviation mapped to 1.0;
- `k=1` nearest annual-positive and nearest annual-nonpositive reference;
- annual score `d_nonpositive - d_positive`;
- final geometry score `min(margin_2013, margin_2014)`;
- exact #839 diversity `lambda=0.8`, `scale=1.0`;
- exactly one equal rank-sum with frozen v19;
- exact fixed literature budgets and evaluator.

## Sole scientific change: maximal leakage-safe references

For every strict group `G`:

1. held-out examples are every Sugar/HDB family with strict group `G`;
2. reference examples are every family whose strict group is not `G`;
3. all 71 feature means/stds are fitted only on those reference examples;
4. annual positive/nonpositive reference sets are formed only from those reference examples;
5. every family in `G` is scored with the unchanged v31 `d_nonpositive-d_positive` rule in each year.

No fixed five-fold assignment is used by the successor score. No same-group family can enter its own reference set. No route-specific exception exists.

This is leave-one-**strict-shower-group**-out, not leave-one-family-out: siblings and cross-route manifestations of the same exposed shower are excluded together exactly as required by the anti-leakage rule.

## Parent control

Before v37 is accepted as technically valid, the same payload/code path must reproduce exact v31 using the original deterministic five-fold references:

- Sugar 2013 `0.2719801488280529 / 16`;
- Sugar 2014 `0.31529041952487225 / 17`;
- HDBSCAN 2013 `0.14888037368183737 / 9`;
- HDBSCAN 2014 `0.15198123772301594 / 9`.

A parent-control failure is technical/provenance only and yields no v37 scientific result.

## Binding evaluation

Exactly one v37 order is evaluated. A panel wins only if macro-F1 is strictly above literature and recovered `F1>0.5` count is at least literature. Development PASS requires 4/4 wins. The first technically valid result is binding.

If v37 fails, exact leave-one-strict-group-out local geometry is permanently rejected. No partial-fold size, group subsampling, route-specific pool, same-group exception, k/metric/scaling/feature/threshold/annual-combiner/diversity/fusion/source-quota/budget rule, or post-result rescue is authorized within v37.

If v37 passes 4/4, freeze the exact full exposed-development reference package; do not call the result external validation and do not access protected validation automatically.

## Firewall

- Protected OrbitTrace solar longitude `20°–55°` remains inaccessible.
- No OrbitTrace target information or target-region event access.
- No MAARSY or DMS scientific access.
- No #1050/#1053 oracle identity may enter the scoring or selection rule.
- Candidate generation and memberships remain unchanged.
