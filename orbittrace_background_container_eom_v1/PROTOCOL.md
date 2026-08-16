# OrbitTrace background-container capped density-synchronous EOM v1 — frozen protocol

## Scientific goal
Test one structural change aimed directly at the current detector's largest visible failure mode: broad background containers are allowed to win the EOM parent-vs-children comparison and occupy the top of the candidate ranking even when they contain tens of thousands of meteors. v1 keeps the exact winning GEO6 tree and exact density-synchronous recurrent stability, but uses HDBSCAN's native `max_cluster_size` EOM rule so clusters larger than a fixed fraction of the accessible survey corpus cannot be selected as meteor-shower candidates and must yield to their descendant substructure.

The project goal is unchanged. A GMN development PASS requires total recovered@100 >= **184** (+5 over the frozen 179 winner) with no annual regression in recovered@50, recovered@100, top-100 dominant precision, MRR, or median top-500 fragmentation. Only a clean GMN pass may earn a separately frozen SonotaCo transfer test.

## Independent motivation and pretruth evidence
The frozen 179 winner itself, inspected from its already-frozen prelabel artifact without consulting any new truth, selects extremely broad candidate nodes including pooled memberships of 44,439, 32,458, 19,760, and 19,303 events. These are far above the 1%-of-corpus structural sanity limit that was already preregistered in multiple later successor protocols before their outcomes.

This experiment does not invent a custom penalty. HDBSCAN's native EOM `get_clusters` implementation exposes `max_cluster_size`; during EOM selection, a node whose cluster size exceeds this value is rejected and its subtree stability is propagated upward, forcing selection to proceed into descendants. The exact upstream implementation is therefore used rather than a post-hoc family deletion or rerank.

A repository/branch/commit audit before freezing found no prior OrbitTrace recurrent-EOM or density-synchronous experiment using HDBSCAN's EOM `max_cluster_size` control or an equivalent rule that forces oversized pooled hierarchy nodes to split.

## Binding baseline
Compare only against the frozen density-synchronous recurrent-EOM GMN winner:
- workflow run `31852836840`;
- artifact `9238142199`;
- 2022 recovered@100 = 89;
- 2023 recovered@100 = 90;
- total recovered@100 = **179**;
- ordered-membership SHA256 `e8f374ad03e7072463118ee6440a54d96d11e3aab17202cfe336f866530224f2`.

The baseline metrics and memberships are read from the frozen artifact. The baseline is not recomputed for comparison.

## Data and firewall
- GMN 2022+2023 development only.
- Protected solar longitude 20°–55° is excluded before clustering.
- OrbitTrace target identity/information and protected-region events remain inaccessible.
- Known-shower labels cannot be indexed until the complete successor hierarchy, selected capped-EOM nodes, memberships, scores and final order are durably written.
- SonotaCo 2013/2014, ASFN, EFN, AMOS, MAARSY and DMS are not accessed in this endpoint.

## Representation and hierarchy held fixed
Use exact inherited GEO6:

`[cos(sol), sin(sol), sin(sun_lon)*cos(ecl_lat), cos(sun_lon)*cos(ecl_lat), sin(ecl_lat), vg/72]`.

Fit exact `hdbscan==0.8.43` with the winner's unchanged hierarchy settings:
- `min_cluster_size=10`;
- `min_samples=10`;
- `metric='euclidean'`;
- `cluster_selection_method='eom'`;
- `cluster_selection_epsilon=0.0`;
- `allow_single_cluster=False`;
- `prediction_data=False`.

The condensed tree and exact density-synchronous recurrent stability calculation are unchanged from the winner.

## Sole scientific change: native EOM maximum selectable size
Let `N` be the complete accessible target-excluded pooled event count before truth. Define the maximum selectable candidate size by the fixed survey-relative rule:

`MAX_CLUSTER_SIZE = floor(0.01 * N)`.

For the frozen GMN development corpus `N=738,682`, so the binding cap is **7,386 events**.

Call HDBSCAN's exact native `get_clusters` EOM selector with the winner's density-synchronous stability dictionary and:
- `allow_single_cluster=False`;
- `cluster_selection_epsilon=0.0`;
- `max_cluster_size=7386`;
- all other selection semantics unchanged.

No candidate is deleted after selection. Oversized hierarchy nodes are prevented from being selected *inside the EOM parent-vs-subtree decision itself*, exactly as HDBSCAN implements `max_cluster_size`.

A pure-Python mirror of the capped EOM node-selection rule must independently reproduce the exact native selected-node partition before truth. The only difference from the existing mirror is the native condition `cluster_size[node] > MAX_CLUSTER_SIZE`, which forces that node to lose to its subtree.

Rank selected candidates by the exact inherited order:
1. descending density-synchronous stability;
2. descending ordinary HDBSCAN stability;
3. descending member count;
4. deterministic family ID.

The cap does not enter ranking because every selected family must already satisfy it.

## Pretruth freeze
Before known-shower labels are indexed, persist:
- exact source/input hashes and event counts;
- unchanged condensed-tree SHA256;
- `max_cluster_fraction=0.01` and binding integer cap 7,386;
- native capped labels and pure-Python selected-node mirror identity;
- complete ordered candidate memberships and scores;
- candidate count, smallest/largest selected family size;
- list/count of frozen-winner selected nodes above the cap, derived only from the frozen prelabel membership sizes;
- ordered-membership SHA256;
- firewall state.

## Binding structural gates
Require:
1. native capped-EOM partition exactly equals the pure-Python capped-EOM node mirror;
2. at least one oversized winner node is made unselectable, proving the mechanism is active;
3. every successor family has <=7,386 members;
4. at least 100 successor families;
5. ordered memberships differ from the 179 winner;
6. condensed hierarchy and density-synchronous stability source are unchanged;
7. all source-pin, reproducibility, and firewall checks pass.

## Binding GMN success gate
PASS requires all of:
1. total recovered@100 >= **184**;
2. 2022 recovered@50 not below the frozen winner and recovered@100 >=89;
3. 2023 recovered@50 not below the frozen winner and recovered@100 >=90;
4. top-100 dominant precision not lower in either year;
5. MRR not lower in either year;
6. median top-500 fragmentation not higher in either year;
7. every structural, source-pin, reproducibility, and firewall gate passes.

Anything else is FAIL.

## Transfer rule
A GMN PASS is only the first goal-level step. Freeze this exact **1% accessible-corpus** rule before one exposed SonotaCo 2013/2014 transfer benchmark. On another survey, compute the cap only as `floor(0.01*N_accessible)` from that survey's unlabeled accessible corpus; no GMN candidate identities or numerical cluster sizes transfer.

Broad generalization still requires a genuinely untouched external survey after exposed SonotaCo development evidence.

## No rescue
If v1 fails, permanently close this exact 1%-capped EOM architecture. Do not retry after outcome with:
- 0.5%, 2%, or any alternative cap;
- an absolute-size cap;
- post-hoc deletion of oversized candidates;
- reranking by size or size-normalized stability;
- different `min_cluster_size` or `min_samples`;
- alternate geometry, feature scaling, orbital features, or background weights;
- leaf selection or epsilon changes;
- target-guided exceptions.

Any later successor must have a distinct independently motivated mechanism.