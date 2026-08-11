# OrbitTrace v39 symmetric cross-route best-rank transfer

## Scientific role

Separately frozen exposed-SonotaCo development successor after exact v31 and failed v36/v37/v38.

The candidate-generation question is already closed for the current HDB objective: #1050 proved that the fixed 229-family HDB universe can beat both HDBSCAN literature panels at the exact budgets. #1053 localized the remaining v31 error to a small number of wrong/missing shower groups. Subsequent local-geometry and archetype-rescoring successors failed.

The cross-route diagnostic chain then identified a distinct mechanism without evaluating a successor:

- #1064 froze the inherited radius-1 Sugar↔HDB graph before truth. Of 2,334 edges, 2,308 are same strict shower group, zero join different shower groups, and 26 involve a NEG family after truth is opened diagnostically.
- #1066 froze the normalized rank disagreement `p_hdb-p_sugar` on #1064's already-corresponding physical structures. Missed recoverable HDB groups have a positive and larger median gap than surfaced groups in both years: missed-minus-surfaced median-gap differences +0.0382206 (2013) and +0.0200501 (2014), with 7/8 linked missed groups positive in each year.

Thus some recoverable structures are not absent or unsupported; the HDB route specifically under-ranks a physical structure that the alternative Sugar route ranks better.

v39 tests one canonical parameter-free response: **symmetric best-route percentile transfer along only the already-frozen radius-1 cross-route edges**. A candidate keeps its own exact v31 rank unless a radius-1 counterpart in the other route has a better normalized v31 rank, in which case it may inherit that better percentile. There is no averaging, coefficient, threshold, distance weighting, or route-specific rescue.

SonotaCo 2013/2014 remains exposed development only. A 4/4 result is not external validation.

## Immutable pretruth cross-route graph

Before any SonotaCo truth is loaded, reproduce exactly the #1064 cross-route graph from the immutable #950 candidate centroids using the already-frozen #1049 annual four-coordinate geometry:

For each annual centroid `(sol, lon, lat, log_vg)` pair,

- wrapped solar-longitude difference / 4;
- wrapped longitude difference × `cos(mean latitude)` / 2;
- latitude difference / 2;
- difference in `exp(log_vg)` / 2;
- ordinary Euclidean norm.

Cross-route distance is the maximum of the 2013 and 2014 annual distances. An edge exists iff distance `<= 1.0`.

No graph parameter is selected in v39. The generated pretruth graph must reproduce exactly:

- Sugar families: 267;
- HDB families: 229;
- cross-route edges: 2,334;
- serialized pretruth graph SHA-256: `2f25aa7d9af1df0a350c034b2280a790c3869a7775bf6d7063d0d1e4cc802b25`.

Any mismatch is an engineering/provenance failure and no scientific v39 result exists.

## Immutable exact v31 base ranking

After the graph identity is frozen and verified, load the immutable exposed SonotaCo truth and reproduce exact v31 independently for Sugar and HDB using:

- immutable #950 71-dimensional pretruth feature matrices and fixed family memberships;
- exact shared deterministic strict-whole-shower five-fold assignment across both routes;
- fold-training mean / population-standard-deviation z-scoring over all 71 dimensions, with zero standard deviation replaced by 1.0;
- annual positive definition `annual F1 > 0.5` for the fixed best shower label;
- ordinary Euclidean `k=1` nearest annual-positive and annual-nonpositive references;
- annual margin `d_nonpositive-d_positive`;
- exact annual `min` combiner;
- exact #839 diversity `lambda=0.8`, `scale=1.0`;
- exactly one equal rank-sum with frozen v19.

Required exact parent controls:

- Sugar 2013: `0.2719801488280529 / 16`;
- Sugar 2014: `0.31529041952487225 / 17`;
- HDBSCAN 2013: `0.14888037368183737 / 9`;
- HDBSCAN 2014: `0.15198123772301594 / 9`.

Any mismatch is an engineering/provenance failure, not a scientific v39 outcome.

## Sole v39 scientific change

Let route `R` have `N_R` fixed families and let `r_R(i)` be candidate `i`'s one-indexed exact v31 fused rank. Define its normalized own percentile

`p_self(i) = (r_R(i)-1)/(N_R-1)`.

For every candidate `i`, use only its already-frozen radius-1 neighbors in the opposite route `Q`. If at least one neighbor exists, define

`p_cross(i) = min_j ((r_Q(j)-1)/(N_Q-1))`

over those exact cross-route neighbors. If no neighbor exists, `p_cross` is absent.

Define the sole v39 transferred score

`p_v39(i) = min(p_self(i), p_cross(i))`

when a cross-route neighbor exists, and otherwise

`p_v39(i) = p_self(i)`.

Lower is better.

Within each route, sort all candidates by:

1. smaller `p_v39`;
2. smaller exact own v31 fused rank;
3. lexicographically smaller family ID.

This produces one complete total order for Sugar and one for HDB. The rule is **symmetric**: Sugar can inherit a better HDB percentile by the same formula and HDB can inherit a better Sugar percentile. The literature budget/year is not used to construct either order.

Interpretation: this is an OR-style transfer of the best calibrated rank evidence for the same radius-1 physical structure. It directly implements #1066's diagnosed route-specific under-ranking while refusing to average away a strong own-route score or invent a tunable transfer strength.

## Explicit non-search commitments

v39 has no:

- HDB-only or Sugar-only exception;
- transfer coefficient or averaging weight;
- additive or multiplicative rank-gap penalty;
- positive-gap threshold;
- minimum overlap count;
- radius/metric/feature search;
- distance/Jaccard weighting;
- clipping, exponent, logarithm, temperature, or nonlinear transform;
- neighbor-count or component-size bonus;
- connected-component closure;
- graph propagation depth;
- hard de-duplication;
- panel-year or budget-specific rule;
- change to v31 labels, folds, distances, annual combiner, diversity, v19 fusion, candidates, or memberships;
- post-result rescue within v39.

The first technically valid v39 outcome is binding.

## Binding development gate

Exactly the two total orders defined above are evaluated at the existing frozen literature budgets. A panel wins only if:

- candidate macro-F1 is strictly greater than the frozen literature comparator; and
- recovered `F1 > 0.5` shower count is at least the literature comparator.

v39 passes exposed development only with 4/4 panel wins.

If v39 fails, exact symmetric best-route percentile transfer is permanently rejected. No average/min-max interpolation, coefficient, positive-gap-only variant, HDB-only transfer, rank-window variant, graph-distance weight, component closure, or other rescue is authorized within v39. Any successor must arise from a new diagnostic or a genuinely distinct mechanism.

If v39 passes 4/4, freeze the exact exposed-development reference/application package needed to reproduce the method. Do not call the result external validation and do not automatically access any protected external dataset or target region.

## Firewall

- Protected OrbitTrace solar longitude `20°–55°` remains inaccessible.
- No OrbitTrace target information or target-region events may be accessed.
- No MAARSY or DMS scientific access is authorized.
- No truth-aware identity from #1050/#1053 may enter the graph, ranks, transfer score, order, or freeze.
- Candidate generation and memberships remain fixed and unchanged.
- SonotaCo remains `EXPOSED_DEVELOPMENT_ONLY`.
