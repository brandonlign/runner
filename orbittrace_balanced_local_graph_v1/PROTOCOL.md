# OrbitTrace balanced cross-year local graph v1 — frozen protocol

## Scientific goal
Build a detector whose geometry is explicitly survey-relative before family formation, so the method is less dependent on absolute event density and has a plausible route to cross-survey transfer.

This is not a reranker, member veto, HDBSCAN successor score, conformal classifier, or target-specific rule.

## Data role
- Development geometry: GMN 2022+2023 only.
- Solar longitude 20°–55° is excluded before every method operation.
- OrbitTrace target information is forbidden.
- Known-shower labels are not used in Stage 0 and may not influence the graph, components, ranking, or structural gate.
- SonotaCo 2013/2014, ASFN, EFN, AMOS, MAARSY, and DMS are not accessed in this GMN development stage.

## Frozen representation
Use the exact inherited GEO6 representation:

`[cos(sol), sin(sol), sin(lon)*cos(lat), cos(lon)*cos(lat), sin(lat), vg/72]`

No feature fitting, whitening, learned metric, uncertainty proxy, or axis-weight search is allowed.

## Frozen local scale
`k = 10`, inherited from the current HDBSCAN `min_samples=10`.

For each event, compute its same-year local scale `r_i` as the Euclidean GEO6 distance to its 10th *other* event in that same year.

## Frozen cross-year graph
1. For every 2022 event, query its 10 nearest 2023 events in ordinary GEO6.
2. For every 2023 event, query its 10 nearest 2022 events in ordinary GEO6.
3. An undirected cross-year edge `(i,j)` is eligible only if the pair is reciprocal: each event lies in the other's cross-year top-10 list.
4. For an eligible edge define the dimensionless local-scale distance

   `s_ij = d_ij / sqrt(r_i * r_j)`.

5. Retain the edge iff `s_ij <= 1.0`.

The threshold 1.0 is not tuned: it is the identity condition that the cross-year separation is no larger than the geometric mean of the two surveys' local 10-neighbor scales.

No same-year graph edge is used. This deliberately makes recurrence across years part of family formation rather than a post-hoc score.

## Frozen family formation
- Families are connected components of the retained undirected bipartite graph.
- Drop components with fewer than 10 total events, inheriting the current minimum cluster size.
- No family expansion, merge, split, rescue, HDBSCAN, DBSCAN, clique search, or iterative refit is allowed.

## Frozen ranking
Rank retained components lexicographically by:
1. larger `min(n_2022, n_2023)`;
2. larger cross-year balance `2*min(n_2022,n_2023)/(n_2022+n_2023)`;
3. larger total member count;
4. stable SHA256 family identifier.

No labels or comparator outcomes enter the ranking.

## Stage 0 — label-free structural gate
Before any known-shower label value is indexed, freeze all candidate memberships/order and report graph/component diagnostics.

Stage 0 passes only if all are true:
- at least 100 retained candidate families exist, so top-100 evaluation is meaningful;
- the largest retained family contains at most 1% of all accessible events, preventing a percolated giant component;
- no single retained family contains more than 5% of all events assigned to retained families;
- the mechanism is nonvacuous: at least one reciprocal edge is rejected by local-scale `s>1` and at least one is retained by `s<=1`.

A Stage-0 failure kills v1 as specified. No graph/rank/threshold tuning is authorized after seeing Stage-0 geometry.

## Binding Stage 1 GMN performance gate
Only if Stage 0 passes, the exact frozen candidate memberships/order may be evaluated against the already-used target-excluded GMN known-shower labels.

Relative to the current density-synchronous recurrent-EOM development winner (2022 @100=89, 2023 @100=90, total=179), PASS requires:
- total recovered@100 >= 184 (+5 minimum);
- for each year independently, recovered@50 and recovered@100 are not lower;
- for each year independently, top-100 dominant precision and MRR are not lower;
- median top-500 fragmentation is not higher in either year;
- all firewall/reproducibility checks pass.

Anything else is a FAIL. No post-result parameter search or scientific rescue is authorized.

## Transfer rule
A GMN PASS only earns a separately frozen exposed-SonotaCo transfer benchmark against the frozen literature comparators. It does not establish generalization by itself. A genuinely untouched external dataset is still required for the final broad-generalization claim.