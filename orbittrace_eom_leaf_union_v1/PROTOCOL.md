# OrbitTrace EOM + leaf multi-resolution density-synchronous union v1 — frozen protocol

## Scientific goal
Test one structural multi-resolution candidate architecture aimed directly at the repeated failure pattern in target-excluded GMN development: broad EOM families preserve recovery, while finer families often improve purity/early rank, but forcing the detector to choose only one resolution destroys one of those benefits.

v1 keeps a **single exact HDBSCAN condensed tree**, computes the existing density-synchronous recurrent stability unchanged, and exposes **both**:
1. the ordinary density-synchronous EOM-selected families from that tree; and
2. HDBSCAN's native finest `leaf` families from that same tree.

Distinct parent/descendant candidates are intentionally allowed to coexist. Only exact-identical memberships are deduplicated. The union is ranked by the exact existing raw density-synchronous stability order; there is no leaf bonus, source weighting, blend, threshold, or new score.

The project goal is unchanged. A GMN PASS requires total recovered@100 >= **184** (+5 over the frozen 179 winner) with no annual regression in recovered@50, recovered@100, top-100 dominant precision, MRR, or median top-500 fragmentation. Only a clean GMN pass may earn one separately frozen SonotaCo transfer test.

## Independent motivation fixed before outcome
Recent preregistered results establish a consistent resolution tradeoff without supporting post-result tuning:
- the frozen density-synchronous EOM winner recovers 179 total @100 but includes very broad selected families;
- lowering only `min_cluster_size` to 4 preserved total recovery at 179 and improved precision/@50, but reduced MRR;
- forcing EOM to reject all >1%-corpus families improved precision to ~0.81 but collapsed recovery to 164;
- size-normalized reranking and fold-persistence reranking both lost substantial recovery.

Those outcomes support one distinct structural hypothesis: **the parent-or-descendants exclusivity of flat EOM selection may be the bottleneck**, not the existence of either broad or fine structure itself.

HDBSCAN natively implements exactly the two resolutions used here. In `get_clusters`, `cluster_selection_method='eom'` performs the excess-of-mass parent-vs-subtree decision; `cluster_selection_method='leaf'` selects the finest leaves of the same condensed cluster tree. Native labels map selected cluster IDs in sorted numeric order. No custom hierarchy resolution is invented.

A repository/branch/code search before freezing found no prior OrbitTrace `cluster_selection_method='leaf'`, EOM+leaf union, overlapping ancestor/descendant HDBSCAN candidate pool, or equivalent multi-resolution flat-candidate experiment.

## Binding baseline
Compare only against the frozen density-synchronous recurrent-EOM GMN winner:
- workflow run `31852836840`;
- artifact `9238142199`;
- winner prelabel SHA256 `efce0617a738a0372ec5b007fb87b46912accd8419f0f768829c4c0cb7d62993`;
- winner result SHA256 `ca6aeed2b82739003ea5d39b59e869df876de2962164344a938fe4935ea38711`;
- 2022 recovered@100 = 89;
- 2023 recovered@100 = 90;
- total recovered@100 = **179**;
- ordered-membership SHA256 `e8f374ad03e7072463118ee6440a54d96d11e3aab17202cfe336f866530224f2`.

The frozen artifact supplies the comparison metrics only. v1 constructs its EOM and leaf candidates together from one newly reconstructed, fully pinned tree so all successor stability values are internally comparable on one hierarchy. A successor need not reproduce the frozen winner's exact membership hash; it must beat its frozen metrics under the hard +5 gate.

## Data and firewall
- GMN 2022+2023 development only.
- Protected solar longitude 20°–55° is excluded before clustering.
- OrbitTrace target information and protected-region events remain inaccessible.
- Known-shower labels cannot be indexed until the full EOM+leaf candidate union, exact deduplication, scores, and final order are durably persisted.
- SonotaCo 2013/2014, ASFN, EFN, AMOS, MAARSY, and DMS are not accessed in this endpoint.

## Representation and hierarchy held fixed
Use exact inherited GEO6:

`[cos(sol), sin(sol), sin(sun_lon)*cos(ecl_lat), cos(sun_lon)*cos(ecl_lat), sin(ecl_lat), vg/72]`.

Fit exact `hdbscan==0.8.43` on the complete accessible pooled 2022+2023 GEO6 set with:
- `min_cluster_size=10`;
- `min_samples=10`;
- `metric='euclidean'`;
- `cluster_selection_method='eom'` at model fit;
- `cluster_selection_epsilon=0.0`;
- `allow_single_cluster=False`;
- `prediction_data=False`.

Compute ordinary HDBSCAN stability and the exact existing density-synchronous recurrent stability on this one condensed tree. The density-synchronous kernel, annual normalization, year bookkeeping, and stability values are unchanged.

## EOM source candidates
Using the exact density-synchronous stability dictionary, obtain EOM labels through native `hdbscan._hdbscan_tree.get_clusters` with:
- `cluster_selection_method='eom'`;
- `allow_single_cluster=False`;
- `cluster_selection_epsilon=0.0`;
- `max_cluster_size=0`.

Use the existing pure-Python `selected_eom_nodes` mirror and require exact selected-node/label-count identity. For every EOM label/node pair, freeze exact sorted member IDs, member count, density-synchronous stability, ordinary stability, and node ID.

## Leaf source candidates
On the **same condensed tree and same density-synchronous stability dictionary**, obtain native leaf labels through `get_clusters` with:
- `cluster_selection_method='leaf'`;
- `allow_single_cluster=False`;
- `cluster_selection_epsilon=0.0`;
- `max_cluster_size=0` (irrelevant to native leaf selection, fixed explicitly).

Independently derive the expected finest leaves using the native `get_cluster_tree_leaves(cluster_tree)` helper, where `cluster_tree = tree[tree['child_size'] > 1]`. Require:
- native positive leaf-label count equals the number of sorted native leaf node IDs;
- every emitted leaf family has at least the frozen 10-member minimum;
- every leaf's member count equals the count implied by its native labels;
- all leaf scores are taken from the same density-synchronous and ordinary-stability dictionaries used for EOM candidates.

For every leaf label/node pair, freeze exact sorted member IDs, member count, density-synchronous stability, ordinary stability, and node ID.

## Sole scientific change: exact-membership union across two native resolutions
Start with the complete same-run EOM candidate list and then add every same-run leaf candidate.

Deduplicate **only** when the exact sorted membership tuple is identical:
- if an EOM and leaf candidate have identical membership, require their node ID and both stability values to be numerically identical within `1e-12`; keep one candidate marked with both sources;
- distinct memberships are never removed merely because one contains, overlaps, or is an ancestor/descendant of another.

No Jaccard threshold, containment threshold, overlap suppression, parent penalty, leaf bonus, source quota, diversity rule, or candidate-budget prefilter is allowed.

The resulting candidate family ID is a deterministic hash of its exact membership. Source metadata (`eom`, `leaf`, or both) is provenance only and never enters ranking.

## Final ranking held fixed
Order the exact EOM+leaf union by the inherited density-synchronous order:
1. descending density-synchronous stability;
2. descending ordinary HDBSCAN stability;
3. descending member count;
4. ascending deterministic family ID.

No source identity enters the rank. No new score is introduced.

## Pretruth freeze
Before any known-shower label is indexed, persist:
- exact source/input hashes and accessible event counts;
- condensed-tree SHA256;
- same-run EOM selected node IDs and candidate count;
- native leaf node IDs and candidate count;
- EOM and leaf labels/count audits;
- exact duplicate-membership list and source merge audit;
- complete union memberships, source metadata, raw stability scores, and final order;
- union candidate count, smallest/largest family size, and ordered-membership SHA256;
- count of leaf-only candidates added beyond EOM;
- count of proper EOM/leaf parent-descendant membership overlaps retained in the union;
- firewall state.

## Binding structural gates
Before truth, require all:
1. at least 100 same-run EOM candidates;
2. at least 1 native leaf candidate;
3. at least 1 nonduplicate leaf candidate is added beyond EOM;
4. native leaf label count exactly equals independently derived leaf-node count;
5. every exact-membership duplicate is merged with score/node identity verified;
6. no exact membership duplicates remain in the final union;
7. at least one retained nonidentical EOM/leaf proper-subset relationship exists, proving multi-resolution overlap is active;
8. every candidate has >=10 members;
9. the union order/membership hash differs from the frozen 179 winner;
10. all source-pin, tree-integrity, density-synchronous reconstruction, and firewall checks pass.

A failure of these structural gates after the hierarchy is successfully formed is a binding scientific failure unless it is demonstrably a source/runtime error before the candidate architecture is produced.

## Binding GMN success gate
PASS requires all:
1. total recovered@100 >= **184**;
2. 2022 recovered@50 not below frozen winner and recovered@100 >=89;
3. 2023 recovered@50 not below frozen winner and recovered@100 >=90;
4. top-100 dominant precision not lower in either year;
5. MRR not lower in either year;
6. median top-500 fragmentation not higher in either year;
7. every structural, source-pin, reproducibility, and firewall gate passes.

Anything else is FAIL.

## Transfer/generalization rule
A GMN PASS is only the first goal-level step. If and only if v1 passes, freeze this exact same-tree EOM+leaf union algorithm before one exposed SonotaCo 2013/2014 benchmark against the existing frozen literature comparators. The same survey-local hierarchy, density-synchronous scoring, exact-membership union, and ranking rule must transfer unchanged.

SonotaCo remains exposed development evidence. Broad generalization still requires a genuinely untouched external survey afterward.

## No rescue
If v1 fails, permanently close this exact EOM+leaf union architecture. Do not retry after outcome with:
- leaf-only selection;
- all hierarchy nodes;
- intermediate depth levels;
- leaf boosts/penalties or source weights;
- source quotas;
- overlap/Jaccard/containment suppression;
- parent-child diversity rules;
- size normalization;
- rank fusion or source-specific rank blending;
- different HDBSCAN parameters or geometry;
- floor-4 leaves;
- post-result candidate filtering;
- target-guided exceptions.

Any later successor must have a distinct independently motivated mechanism.