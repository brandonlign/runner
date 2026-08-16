# OrbitTrace deterministic Persistable cross-scale diagnostic v1

## Activation condition

This protocol is frozen **before** the synthetic selector audit outcome. It may execute only if the exact synthetic audit `orbittrace_persistable_auto_selector_audit_v1` returns `PASS_PERSISTABLE_AUTO_SELECTOR_SYNTHETIC_FEASIBILITY`. A synthetic FAIL permanently blocks this execution.

## Role and firewall

Zero-label structural diagnostic only. Use target-excluded GMN 2022+2023 only. Protected solar longitude `[20°,55°]` is removed through the exact frozen parser before clustering. No shower truth may be read. No SonotaCo, ASFN/EFN event rows, AMOS, MAARSY, DMS, OrbitTrace target information, or target-region event may be accessed.

## Frozen method

Use `LuisScoccola/persistable` commit `7eb75b2e8d2fe5a18e49248aa7d1c97f829415be` and the byte-identical automatic selector frozen in the synthetic audit:

- `Persistable(X, n_neighbors="auto", n_jobs=1)`;
- package uniform probability measure and Euclidean metric;
- exact package `_find_end()` and `compute_defaults()` first/second default slices;
- package-default prominence-vineyard granularity;
- inspect prominence gaps 2..min(15,last available gap), excluding gap 1;
- `delta_g(t)=max(P_g(t)-P_{g+1}(t),0)/max(P_1(t),1e-15)`;
- choose gap with largest mean delta over all default vineyard positions, tie smaller gap;
- choose vineyard position maximizing that already-selected gap, tie earliest;
- conservative persistence flattening with the selected gap as requested cluster count;
- no fallback or alternate selector.

Input representation is exact recurrent-EOM GEO6, unchanged:
`(cos(sol), sin(sol), sin(lon)*cos(lat), cos(lon)*cos(lat), sin(lat), vg/72)`.

No physical rescaling, feature change, learned metric, or year input is allowed.

## Frozen scale stress

Reuse exact deterministic hashing from PR #1272:

- salt `ORBITTRACE_SCALE_STRESS_V1|`;
- coarse denominator `128`, buckets `0,1,2,3` (~5.8k events);
- fine denominator `1024`, same buckets (~0.7k events);
- fine subset must be nested inside the corresponding coarse subset.

Comparator: exact recurrent-EOM HDBSCAN `10/10` on the same GEO6 rows/subsets.

Persistable returned labels are converted to candidate memberships by retaining non-noise clusters with at least **4** members. This is reporting-only and does not alter the Persistable hierarchy or flattening.

## Cross-scale metric

For each bucket:

1. restrict every coarse candidate to the fine-event universe and retain restricted memberships with >=4 members;
2. for each fine candidate, compute its maximum Jaccard overlap with any restricted coarse candidate;
3. report candidate-unweighted mean best Jaccard, median best Jaccard, and exact restricted-match fraction.

Compute the same quantities for recurrent-EOM.

## Frozen gates

PASS requires **all**:

1. Persistable returns at least one eligible candidate on all eight subsets;
2. in every fine subset, Persistable eligible-candidate count is at least the recurrent-EOM candidate count;
3. pooled candidate-unweighted mean best Jaccard is strictly greater than recurrent-EOM;
4. median of the four bucket mean-best-Jaccards is strictly greater than recurrent-EOM;
5. Persistable strictly wins mean-best-Jaccard in at least 3 of 4 buckets.

A PASS authorizes only a separately frozen target-excluded GMN recovery/ranking successor. A FAIL closes this exact automatic Persistable + GEO6 architecture. No result-informed rescue via gap metric/range, default slices, vineyard resolution, `n_neighbors`, representation, min reporting support, flattening mode, subset, salt, comparator, or gate is allowed.
