# OrbitTrace window-owned local persistence cross-scale diagnostic v1

## Role

This is a **zero-label structural diagnostic**, not a shower-recovery experiment. It is motivated by two frozen observations:

1. the physical MeanShift modal-basin diagnostic (#1279) produced much more cross-scale-stable surviving memberships than recurrent-EOM but lost sparse candidate modes;
2. the global Persistable ladder (#1282) remained too low-capacity/coarse, producing only 3–4 fine candidates, while historical wavelet catalogue work showed that transitive overlap across global/local proposals can percolate into too few families.

This successor changes the **spatial organization of candidate generation**: it builds independent local persistence hierarchies in already-established solar-longitude activity windows and uses deterministic window ownership instead of cross-window merging.

## Firewall

Use only target-excluded GMN 2022+2023 geometry. Protected solar longitude `[20°,55°]` is removed through the exact frozen parser before any candidate construction. No shower truth may be read. No SonotaCo, ASFN/EFN event rows, AMOS, MAARSY, DMS, OrbitTrace target information, or target-region event may be accessed.

## Frozen representation and windows

Input representation is exact recurrent-EOM GEO6, unchanged:
`(cos(sol), sin(sol), sin(lon)*cos(lat), cos(lon)*cos(lat), sin(lat), vg/72)`.

Use the already-established catalogue window geometry from the Brown/wavelet lineage:

- window width exactly **10°** in solar longitude;
- centers exactly `0°,5°,...,355°` (72 centers);
- membership in a window iff circular solar-longitude distance to its center is `<=5°`;
- no window is removed merely because its center lies inside the protected interval; the event-level protected interval is already empty before windowing.

## Frozen local persistence primitive

Pinned upstream: `LuisScoccola/persistable@7eb75b2e8d2fe5a18e49248aa7d1c97f829415be`.

For each window independently:

1. if fewer than 4 events are present, emit no candidate and continue;
2. construct `Persistable(X_window, n_neighbors="auto", n_jobs=1)`, uniform measure, Euclidean metric;
3. use exact package `_find_end()` and `compute_defaults()`;
4. use exact package-default midpoint slice (`X/Y_START_LINE`, `X/Y_END_LINE`);
5. construct one midpoint `lambda_linkage` hierarchy;
6. let `B` be the number of strictly positive-persistence bars;
7. if `B<2`, emit no candidate and continue;
8. for every requested cluster count `g=2..min(15,B)`, use exact package `_compute_threshold(g)` and conservative persistence flattening with `keep_low_persistence_clusters=False`;
9. retain non-noise memberships with at least **4** events and take their exact-membership union inside that window.

No preferred g, persistence cutoff, alternate slice, custom neighbor count, or local tuning exists.

## Deterministic window ownership

There is **no cross-window connected-component graph, transitive merge, centroid-link radius, or Jaccard threshold**.

For each local candidate:

1. calculate the circular mean solar longitude from its actual member events;
2. find the nearest center among the fixed 72 centers by circular angular distance;
3. ties are broken by the numerically smaller center;
4. retain the candidate only when its generating window center equals that owner center.

After ownership, exact duplicate memberships (if any) are deduplicated. The family identity is the SHA-256 hash of the sorted event IDs. Ownership is the only overlap-control rule.

## Frozen scale stress

Reuse exact deterministic hashing from PR #1272:

- salt `ORBITTRACE_SCALE_STRESS_V1|`;
- coarse denominator `128`, buckets `0,1,2,3` (~5.8k pooled events);
- fine denominator `1024`, same buckets (~0.7k pooled events);
- each fine subset must be nested inside its corresponding coarse subset.

Comparator: exact recurrent-EOM HDBSCAN `10/10` on the same GEO6 rows/subsets.

## Symmetric cross-scale coherence

For each method and bucket:

1. restrict every coarse candidate to the fine-event universe and discard restricted memberships below 4;
2. deduplicate exact restricted memberships;
3. compute fine→restricted-coarse mean best Jaccard;
4. compute restricted-coarse→fine mean best Jaccard;
5. symmetric bucket score is the arithmetic mean of the two directions.

Pool direction-specific candidate scores across all four buckets before averaging to obtain pooled symmetric coherence. Report exact restricted-match fractions and candidate counts. Extra unmatched local proposals lower the reverse-direction score.

## Frozen gates

PASS requires **all**:

1. window-owned candidate set is nonempty on all eight subsets;
2. every local window respects the architectural <=119 candidate ceiling before ownership/deduplication;
3. every fine window-owned candidate count is at least the corresponding recurrent-EOM candidate count;
4. pooled symmetric mean-best-Jaccard strictly exceeds recurrent-EOM;
5. median of the four window-owned symmetric bucket scores strictly exceeds recurrent-EOM;
6. window-owned persistence strictly wins symmetric bucket score in at least 3 of 4 buckets;
7. pooled fine→coarse directional mean is not below recurrent-EOM;
8. pooled coarse→fine directional mean is not below recurrent-EOM.

A PASS authorizes only a separately frozen target-excluded GMN recovery/ranking successor. A FAIL closes this exact window-owned GEO6 + midpoint persistence-ladder architecture. No result-informed rescue via window width/step, ownership rule, representation, ladder range, min support, neighbor policy, flattening, subset, salt, comparator, coherence metric, or gates is allowed.