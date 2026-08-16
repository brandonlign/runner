# OrbitTrace Persistable persistence-ladder cross-scale diagnostic v1

## Activation condition

This protocol is frozen before the synthetic persistence-ladder audit outcome. It may execute only if the exact synthetic audit on `agent/orbittrace-persistable-ladder-audit-v1` returns `PASS_PERSISTABLE_LADDER_SYNTHETIC_FEASIBILITY`. A synthetic FAIL permanently blocks this GMN execution.

## Role and firewall

Zero-label structural diagnostic only. Use target-excluded GMN 2022+2023 only. Protected solar longitude `[20°,55°]` is removed through the exact frozen parser before clustering. No shower truth may be read. No SonotaCo, ASFN/EFN event rows, AMOS, MAARSY, DMS, OrbitTrace target information, or target-region event may be accessed.

## Frozen ladder method

Pinned upstream: `LuisScoccola/persistable@7eb75b2e8d2fe5a18e49248aa7d1c97f829415be`.

Input representation is exact recurrent-EOM GEO6, unchanged:
`(cos(sol), sin(sol), sin(lon)*cos(lat), cos(lon)*cos(lat), sin(lat), vg/72)`.

For every subset:

1. `Persistable(X, n_neighbors="auto", n_jobs=1)`, uniform measure, Euclidean metric.
2. Use exact package `_find_end()` and `compute_defaults()`.
3. Use exact package-default midpoint slice (`X/Y_START_LINE`, `X/Y_END_LINE`).
4. Construct that one `lambda_linkage` hierarchy once.
5. Let `B` be the number of strictly positive-persistence bars.
6. For every requested cluster count `g=2..min(15,B)`, use the package exact `_compute_threshold(g)` and `persistence_based_flattening(..., flattening_mode="conservative", keep_low_persistence_clusters=False)`.
7. Retain non-noise memberships with at least **4** events and take the exact-membership union across all `g`.
8. No candidate ranking, preferred `g`, manual selection, alternative slice, or fallback exists.

The architectural candidate ceiling is `sum(2..15)=119` before exact-membership deduplication.

## Frozen scale stress

Reuse exact deterministic hashing from PR #1272:

- salt `ORBITTRACE_SCALE_STRESS_V1|`;
- coarse denominator `128`, buckets `0,1,2,3` (~5.8k events);
- fine denominator `1024`, same buckets (~0.7k events);
- each fine subset must be nested inside its corresponding coarse subset.

Comparator: exact recurrent-EOM HDBSCAN `10/10` on the same GEO6 rows/subsets.

## Symmetric cross-scale coherence

For each method and bucket:

1. restrict every coarse candidate to the fine-event universe; drop restricted memberships below 4;
2. compute fine→restricted-coarse mean best Jaccard;
3. compute restricted-coarse→fine mean best Jaccard;
4. symmetric bucket score is the arithmetic mean of the two directional means.

Pool direction-specific candidate scores across all four buckets before averaging to form a pooled symmetric score. Also report exact restricted-match fractions and candidate counts. Extra unmatched candidates reduce the reverse directional mean rather than helping automatically.

## Frozen gates

PASS requires **all**:

1. ladder candidate set nonempty on all eight subsets;
2. ladder candidate count <=119 on all eight subsets;
3. every fine ladder candidate count is at least the corresponding recurrent-EOM candidate count;
4. pooled symmetric mean-best-Jaccard strictly exceeds recurrent-EOM;
5. median of the four ladder symmetric bucket scores strictly exceeds recurrent-EOM;
6. ladder strictly wins the symmetric bucket score in at least 3 of 4 buckets;
7. pooled fine→coarse directional mean is not below recurrent-EOM;
8. pooled coarse→fine directional mean is not below recurrent-EOM.

A PASS authorizes only a separately frozen target-excluded GMN recovery/ranking successor. A FAIL closes this exact default-midpoint persistence-ladder + GEO6 architecture. No result-informed rescue via representation, midpoint slice, ladder range, support, neighbor policy, flattening, subset, salt, comparator, coherence metric, candidate ceiling, or gates is allowed.
