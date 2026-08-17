# OrbitTrace TopoModal Predictive Tree Cut v1 — frozen development protocol

## Scientific role

This is a separately named **selector successor** to the fixed-scale TopoModal flagship. It changes no TopoModal candidate membership, physical scale, graph radius, density, or hierarchy. Its sole purpose is to replace the failed root-first/prominence ordering with a label-free flat extraction from the already-frozen hierarchy.

The successor is motivated by the exposed SonotaCo full-recoverability diagnostic, which established that every stream recovered by the exact published catalogue-HDBSCAN comparator already exists somewhere in the fixed TopoModal hierarchy while several are ranked hundreds of positions too late. SonotaCo 2013/2014 remains **EXPOSED DEVELOPMENT ONLY**.

All prior selector failures remain closed, including support-resolved cuts, map-equation ranking, finite-death support, lineage selectors, annual confirmation, EOM/excess-mass extraction, significance pruning, rank-density variants, and physical-root Bayesian planted-partition MDL. This successor does not alter or rescue any of them.

## Motivation and distinction

The selector asks whether a fixed TopoModal hierarchy node represents a graph-cohesive structure that generalizes across a deterministic edge holdout. Network cross-validation by splitting node pairs/edges is an established model-selection principle; here it is applied only as a **predictive evidence score on already-frozen meteor-stream hierarchy states**.

This is distinct from the closed PPMDL lane: PPMDL discarded the TopoModal hierarchy and inferred a new Bayesian planted-partition clustering inside physical roots. Predictive Tree Cut keeps every TopoModal membership fixed and selects an antichain from the existing hierarchy by held-out edge evidence.

## 1. Firewall and immutable inputs

Use only the exact HDBSCAN-compatible SonotaCo 2013 and 2014 row universes from the matched-literature benchmark. Protected solar longitude `[20°,55°]` is excluded inclusively upstream.

Reuse byte-for-byte:

- fixed-scale TopoModal pretruth candidate output from run `31983941271`, artifact `9273183576`, candidate SHA-256 `7020ae01b9a3407a15baeca216a167f9d6963e84c7386150bfa24e70530672be`;
- exact published catalogue-HDBSCAN outputs from run `31984184708`;
- the exact matched-literature truth map/evaluator, but only after the selector output is hash-frozen.

No shower label, `iau`, orbit, uncertainty, station metadata, HDBSCAN membership, target information, or post-result quality statistic enters selection.

## 2. Annual projection of the frozen hierarchy

The immutable TopoModal hierarchy was generated on pooled 2013+2014 rows. For each year independently:

1. intersect every frozen TopoModal membership with that year's exact HDBSCAN-compatible event universe;
2. discard annual restrictions below support 4;
3. deduplicate exact annual memberships;
4. retain the lowest original TopoModal rank and complete list of pooled source family IDs only as provenance; neither affects the new score.

No new cluster membership is generated.

The annual restricted family must remain laminar: every pair is either disjoint or one contains the other. Failure of laminarity invalidates the implementation before truth.

For every non-root annual membership, define its parent as the unique smallest strict superset among annual restricted memberships. Exact duplicate restrictions have already been collapsed. Parent uniqueness is a pretruth invariant.

## 3. Exact annual physical graph

Reconstruct the same fixed physical geometry as the flagship:

`Z = (cos(sol)/h_sol, sin(sol)/h_sol, cos(lat)cos(lon)/h_rad, cos(lat)sin(lon)/h_rad, sin(lat)/h_rad, log(v_g)/h_logv)`

with

- `h_sol = 2 sin(5°/2)`;
- `h_rad = 2 sin(4°/2)`;
- `h_logv = ln(1.1)`.

Use the exact simple undirected `cKDTree` radius graph with Euclidean radius `r=1.0`, excluding self edges. Sort annual rows by exact event ID before graph construction. No adaptive radius, kNN graph, kernel, density transform, edge weight, or HDBSCAN-derived graph is permitted.

## 4. Deterministic edge holdout

For each event ID define

`H(eid) = uint64_be(SHA256('ORBITTRACE_TOPOMODAL_PREDICTIVE_TREE_CUT_V1|' + eid)[0:8])`.

For every undirected physical edge `{i,j}`:

- training edge iff `(H(id_i) XOR H(id_j)) mod 2 = 0`;
- held-out edge otherwise.

This split is fixed before truth. No salt, fold count, replicate, or split search is authorized.

## 5. Degree-preserving predictive gain

For each split graph `s ∈ {train,test}` let:

- `M_s` be its total edge count;
- `d_i^s` be vertex degree;
- for candidate `C`, `e_C^s` be observed internal edges;
- `v_C^s = sum_{i∈C} d_i^s`.

Under the standard degree-preserving configuration expectation, define

`lambda_C^s = ((v_C^s)^2 - sum_{i∈C}(d_i^s)^2) / (4 M_s)`.

If either split has zero total edges or nonpositive `lambda`, the candidate predictive gain is exactly zero.

Fit only on the training split the one-sided internal-edge enrichment multiplier

`alpha_C = max(1, e_C^train / lambda_C^train)`.

Score the frozen candidate on held-out edges by the Poisson log-likelihood gain over the degree-preserving null:

`S_C = e_C^test log(alpha_C) - (alpha_C - 1) lambda_C^test`.

Thus a candidate cannot obtain positive evidence by learning an internal-edge deficit; no threshold or pseudocount is fitted.

## 6. Predictive antichain dynamic program

For each annual hierarchy root recursively compare:

- selecting the current node, with value `max(0,S_C)`;
- selecting the union of each child's optimal solution, with value equal to the sum of child values.

Choose the current node iff its value is greater than or equal to the child total. Otherwise choose the child solutions. A zero-valued selected-node option yields no candidate.

The union across hierarchy roots is the complete annual **Predictive Tree Cut**. It must be pairwise disjoint; any overlap is a pretruth implementation failure.

This is the only flat extraction. There is no target number of selected nodes, pruning threshold, depth limit, root quota, support change, or post-hoc overlap rule.

## 7. Frozen candidate order

Rank the selected antichain by:

1. descending held-out predictive gain `S_C`;
2. ascending SHA-256 of sorted annual member IDs as the sole deterministic tie-break.

Original TopoModal rank, prominence, density, root status, HDBSCAN overlap, annual truth, recurrence, orbit, and external metadata do not affect this order.

## 8. Pretruth structural gates

Before shower truth can open, both annual outputs must satisfy all:

- exact immutable TopoModal source/output hashes match;
- exact annual row hashes match;
- physical graph is nonempty and both deterministic edge splits are nonempty;
- annual hierarchy is laminar and every non-root has a unique parent;
- selected candidates are pairwise disjoint;
- every selected gain is finite and strictly positive;
- selected candidate capacity is at least the exact HDBSCAN budget (`11` in 2013, `9` in 2014);
- ranks are contiguous and deterministic;
- no truth/target field was accepted.

Failure stops before truth and is technical, not scientific.

## 9. Binding HDBSCAN development comparison

For each year independently let `B` be the complete exact published-HDBSCAN family count. Take the first `B` Predictive Tree Cut candidates and evaluate them against the complete HDBSCAN family set on the identical row universe using the exact frozen Hungarian maximum-F1 evaluator.

Eligible known showers remain those with at least 4 events in the exact annual row universe.

A year is a win iff both:

- Predictive Tree Cut macro-F1 is strictly greater than HDBSCAN macro-F1;
- recovered showers with assigned F1 > 0.5 are at least the HDBSCAN count.

`PASS_TOPOMODAL_PREDICTIVE_TREE_CUT_V1_HDBSCAN_DEVELOPMENT` requires wins in **both 2013 and 2014**. Any other technically valid result is `FAIL_TOPOMODAL_PREDICTIVE_TREE_CUT_V1_HDBSCAN_DEVELOPMENT`.

## 10. Closure and next step

The first technically valid truth outcome is binding. No edge split, null expectation, enrichment formula, DP tie, annual projection rule, ranking, feature, support, budget, or physical graph parameter may be changed as a v1 rescue.

- Failure permanently closes this exact selector.
- Success immediately freezes the exact selector for a separately preregistered target-excluded GMN scale/generalization test before any promotion claim.

At all times protected `[20°,55°]`, OrbitTrace target information/events, MAARSY, and DMS remain inaccessible.
