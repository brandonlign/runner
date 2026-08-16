# OrbitTrace independent-year mutual-nearest HDBSCAN v1 — frozen protocol

## Scientific goal
Test one structural recurrence architecture aimed directly at cross-survey generalization: do **not** let unequal annual sampling density determine a single pooled HDBSCAN hierarchy. Instead, build the density hierarchy independently in GMN 2022 and 2023, select ordinary HDBSCAN EOM clusters inside each year, and retain only one-to-one cross-year cluster pairs that are mutual nearest neighbors in the inherited physical GEO6 centroid space.

A GMN development pass requires a meaningful improvement over the frozen density-synchronous recurrent-EOM winner: total recovered@100 >= **184** (+5 over 179) with no annual regressions in recovered@50, recovered@100, top-100 dominant precision, MRR, or top-500 fragmentation. Only a clean GMN pass earns one separately frozen SonotaCo transfer test.

## Independent motivation fixed before outcome
The current pooled recurrent/density-synchronous lineage measures recurrence on a hierarchy whose geometry is first built from the union of both years. Because accessible event counts differ substantially (315,024 in 2022 versus 423,658 in 2023), a pooled density tree can encode year-specific sampling density before the recurrence objective is applied.

The new mechanism removes that coupling at its source. Each year gets its own density hierarchy under identical HDBSCAN settings. Cross-year recurrence is then imposed only after annual cluster formation through a deterministic, parameter-free mutual-nearest correspondence in the same GEO6 physical representation already used by the promoted method.

This is not a reranker, member filter, density rescaling, or alternative pooled EOM aggregation. A repository/branch audit before freezing found no prior OrbitTrace detector using this exact architecture: independent annual HDBSCAN EOM trees followed by reciprocal nearest-centroid pairing and a shared recurrence rank.

Older cross-year component/seed expansion experiments are scientifically distinct: they expanded memberships of a pre-existing sparse-detector family universe and did not construct or pair independent annual HDBSCAN trees.

## Binding baseline
Compare only against the frozen density-synchronous recurrent-EOM GMN winner:
- run `31852836840`;
- artifact `9238142199`;
- 2022 recovered@100 = 89;
- 2023 recovered@100 = 90;
- total recovered@100 = **179**;
- ordered-membership SHA256 `e8f374ad03e7072463118ee6440a54d96d11e3aab17202cfe336f866530224f2`.

The baseline is read from its frozen artifact and is never recomputed for comparison.

## Data and firewall
- GMN 2022 and 2023 development only.
- Solar longitude 20°–55° is excluded before either annual hierarchy is built.
- OrbitTrace target information and protected-region events are inaccessible.
- Known-shower labels cannot be indexed until both annual trees, annual selected clusters, reciprocal pair mapping, complete pooled candidate memberships, scores, and final order are durably persisted.
- SonotaCo 2013/2014, ASFN, EFN, AMOS, MAARSY, and DMS are not accessed in this endpoint.

## Representation held fixed
Use exact inherited GEO6 with no transformation:

`[cos(sol), sin(sol), sin(sun_lon)*cos(ecl_lat), cos(sun_lon)*cos(ecl_lat), sin(ecl_lat), vg/72]`.

No Z-score, whitening, seasonal-background factor, orbital element, uncertainty proxy, learned metric, or feature weighting enters v1.

## Annual detector held fixed
For each year independently, fit exact `hdbscan==0.8.43` on that year's accessible GEO6 rows with:
- `min_cluster_size=10`;
- `min_samples=10`;
- `metric='euclidean'`;
- `cluster_selection_method='eom'`;
- `cluster_selection_epsilon=0.0`;
- `allow_single_cluster=False`;
- `prediction_data=False`.

Compute ordinary HDBSCAN stability on that annual condensed tree and use the repository's exact `selected_eom_nodes` / `eom_labels` mirror. Before any truth access, the resulting annual partition must equal the canonical `model.labels_` partition exactly. Any mismatch is a technical no-result.

For each selected annual cluster C record:
- exact sorted member IDs;
- ordinary EOM stability `E(C)`;
- survey-normalized stability `S(C)=E(C)/N_year`;
- member count;
- arithmetic GEO6 centroid over the cluster's annual members.

## Sole cross-year recurrence mechanism: mutual nearest annual clusters
Let annual 2022 clusters be A_i and annual 2023 clusters be B_j.

1. Compute ordinary squared Euclidean distance between every pair of annual GEO6 centroids.
2. For every A_i, select the nearest B_j. For exact distance ties choose the smaller deterministic annual cluster ID.
3. For every B_j, independently select the nearest A_i with the same tie rule.
4. Retain a cross-year family **only** when A_i and B_j select each other.
5. Each retained family's membership is the exact union of the two matched annual memberships. Because annual EOM clusters are disjoint and mutual-nearest matching is one-to-one, retained pooled families cannot share annual clusters.

There is **no distance threshold**, no k search, no radius, no matching optimization, no second-neighbor rule, no many-to-one pairing, and no learned cross-year mapping.

## Shared recurrence score and ranking
For a retained pair `(A_i,B_j)` define one recurrence score:

`R = min(S(A_i), S(B_j))`.

Final pooled order is:
1. descending `R`;
2. descending `S(A_i)+S(B_j)`;
3. descending pooled member count;
4. ascending deterministic family ID.

Centroid distance is recorded for audit but does not enter rank, avoiding a second geometric tuning mechanism.

## Pretruth freeze
Before any known-shower label is indexed, persist:
- exact source/input hashes and event counts;
- annual condensed-tree SHA256 values;
- annual selected node sets and partition-identity checks;
- every annual selected cluster's membership, normalized stability and GEO6 centroid;
- complete nearest-neighbor maps in both directions;
- exact reciprocal-pair list;
- every pooled pair membership, recurrence score and final order;
- candidate count, largest-family size and ordered-membership SHA256;
- firewall state.

## Binding structural gates
Before truth, require:
- at least 100 reciprocal pooled families;
- largest pooled family <=1% of all accessible events;
- no repeated annual cluster in two pooled families;
- pooled memberships differ from the frozen 179 winner;
- both annual custom EOM partitions exactly reproduce HDBSCAN's canonical partitions.

Failure of a structural gate is a binding scientific failure unless caused by a source/runtime mismatch before the method output is formed.

## Binding GMN success gate
PASS requires all of:
1. total recovered@100 >= **184**;
2. 2022 recovered@50 >= frozen winner and recovered@100 >=89;
3. 2023 recovered@50 >= frozen winner and recovered@100 >=90;
4. top-100 dominant precision not lower in either year;
5. MRR not lower in either year;
6. median top-500 fragmentation not higher in either year;
7. every structural, reproducibility, source-pin and firewall gate passes.

Anything else is FAIL.

## Transfer rule
A GMN PASS is only the first goal-level step. Freeze the exact algorithm before one exposed SonotaCo 2013/2014 benchmark. On another survey with two annual catalogues, apply the same survey-local rule: independent annual GEO6 HDBSCAN trees, reciprocal nearest-centroid pairing, minimum normalized annual stability rank. GMN-derived numerical centroids or scores are never transferred.

Broad generalization still requires a genuinely untouched external survey; SonotaCo remains exposed development evidence only.

## No rescue
If v1 fails, permanently close this exact independent-year reciprocal-centroid architecture. Do not retry after outcome with:
- a centroid-distance threshold;
- k>1 or second-neighbor logic;
- Hungarian/global matching;
- many-to-one matching;
- medoids or alternate centroids;
- alternate stability normalization/aggregation;
- centroid distance in the rank;
- feature scaling or geometry changes;
- leaf selection;
- HDBSCAN parameter changes;
- reranking, filtering, blending, or target-guided exceptions.

Any later successor must have a distinct independently motivated mechanism.