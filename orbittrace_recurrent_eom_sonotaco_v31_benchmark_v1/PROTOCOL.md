# Recurrent-EOM HDBSCAN v1 — frozen SonotaCo/v31 exposed-development benchmark

## Status

This protocol is frozen after the binding target-excluded GMN PASS of recurrent-EOM HDBSCAN v1 and before the first technically valid SonotaCo 2013/2014 portability outcome under this benchmark.

This is **EXPOSED DEVELOPMENT ONLY**, not pristine external validation. The protected OrbitTrace solar-longitude interval `[20°,55°]`, OrbitTrace target information/events, MAARSY, and DMS remain inaccessible.

No result from this benchmark may alter recurrent-EOM v1's HDBSCAN parameters, representation, recurrent-stability definition, cluster extraction, ranking rule, row eligibility, comparator budgets, or evaluation rule. The first technically valid outcome is binding.

## 1. Frozen upstream method

The scientific method is exactly the already-authorized recurrent-EOM HDBSCAN v1 that passed target-excluded GMN development in run `31827903547`.

Pinned recurrent-EOM implementation blob:

`30ac3fa3bc47910370df528fcf3ae8ecb6277b47`

Exact clustering configuration, unchanged from GMN:

- representation: GEO6 = `(cos(sol), sin(sol), sin(lon)*cos(lat), cos(lon)*cos(lat), sin(lat), vg/72)`;
- `min_cluster_size=10`;
- `min_samples=10`;
- Euclidean metric;
- HDBSCAN EOM condensed hierarchy;
- `cluster_selection_epsilon=0`;
- `allow_single_cluster=False`;
- pooled two-year hierarchy;
- annual EOM contribution normalized by accessible event count in that year;
- recurrent cluster stability = the minimum of the two normalized annual EOM values;
- HDBSCAN's own EOM extraction is rerun with that recurrent stability on the unchanged hierarchy;
- candidate ranking = descending recurrent stability, then descending ordinary HDBSCAN stability, then descending member count, then deterministic family ID.

No SonotaCo label, shower identity, literature result, v31 ranking, or comparator budget may enter clustering, cluster selection, membership, or candidate ranking.

## 2. Frozen label-free SonotaCo inputs

Use exact artifact `9050107352`, `orbittrace-final-sonotaco-label-free-preparation-v2`, artifact digest:

`sha256:1296d757b5ea1dd94f9c9077fd769fdc8f00ec06d0881d8548fd1df4608344cc`

Its manifest records `shower_truth_accessed=false`, `target_information_access=false`, `maarsy_scientific_access=false`, and `target_region_retained=false`. The protected interval was removed before any non-solar scientific field was decoded.

Two established matched comparator routes are benchmarked independently, each by pooling its 2013 and 2014 label-free rows before clustering:

### Sugar-matched route

- `sugar_2013.json`: SHA-256 `47fb0b700fbf710c7b061eead343016bd8d182756eb0c7f406507c5739e4c4f8`, 18,638 events.
- `sugar_2014.json`: SHA-256 `bc83c113e9a14b1c6e1ef460ca9a40e05df77f3a449fec6064f8910add04c912`, 15,400 events.

### HDBSCAN-matched route

- `hdbscan_2013.json`: SHA-256 `2433b556d4a859580ef5431d2307ef34c8fa4c15d42841a2ec7b0c11e5f1f158`, 16,028 events.
- `hdbscan_2014.json`: SHA-256 `206692292b2ca252777e40c13c367880740d8e2576d27615f7ea94b7790e3f55`, 13,283 events.

Only `id`, `year`, `sol`, `sun_lon`, `ecl_lat`, and `vg` enter recurrent-EOM. Orbital elements and the hidden `iau`/`complex_key` placeholders do not enter the method.

Every row must satisfy the already-prepared blind exclusion; any `[20°,55°]` row causes fail-closed termination.

## 3. Pre-truth freeze

For each route, the workflow must complete HDBSCAN fitting, recurrent stability, selected nodes, exact memberships, and the full deterministic candidate ranking **before** SonotaCo truth or v31 result bytes are loaded into the benchmark process.

The full two-route candidate payload is serialized as `RECURRENT_EOM_SONOTACO_V1_PRETRUTH.json` and SHA-256 frozen before the truth-download/evaluation step.

Any technical failure before that point is a no-result and may receive engineering-only repairs that provably do not change science.

## 4. Exact evaluation domain

After pre-truth freeze only, load the exact immutable exposed SonotaCo truth/evaluation artifact used by v22-v31:

- artifact `9069505548`;
- truth files `truth_{route}_{year}.json`;
- evaluation files `evaluation_{route}_{year}.json`.

Evaluate recurrent-EOM candidates with the exact established v22/v31 literature-evaluation semantics:

1. restrict each pooled candidate's members to the panel year's truth IDs;
2. retain candidates in the already-frozen recurrent-EOM pooled rank order;
3. truncate to `evaluation_{route}_{year}.json['candidate_budget']['comparator_budget']`;
4. construct the shower-by-candidate F1 matrix using all panel showers with at least four truth events;
5. perform the exact Hungarian maximum-F1 one-to-one assignment;
6. report macro-F1 and count assigned showers with F1 `>0.5`.

No candidate may be removed, inserted, reranked, split, merged, annualized, or otherwise changed after truth load.

## 5. Exact v31 control

Use authoritative v31 run `31509767311`, artifact `9108560001`, artifact digest:

`sha256:b1c3e64cbd58ebcc72ee8fa94df2c73151daf6386441d2299ad0e3836c122e9e`

Pinned `V31_LOCAL_GEOMETRY_OOF_RESULT.json` SHA-256:

`f69555d443f453fd40a769da09b2bbec8bf62cd4a932cd84278bb23305b5ac8e`

The exact v31 controls are:

| Route | Year | Budget | v31 macro-F1 | v31 recovered F1>0.5 |
|---|---:|---:|---:|---:|
| Sugar | 2013 | 34 | 0.2719801488280529 | 16 |
| Sugar | 2014 | 46 | 0.31529041952487225 | 17 |
| HDBSCAN | 2013 | 11 | 0.14888037368183737 | 9 |
| HDBSCAN | 2014 | 9 | 0.15198123772301594 | 9 |

The benchmark must verify these bytes/values exactly before interpreting recurrent-EOM against v31.

## 6. Frozen gates

### Primary gate: stronger than v31

`PASS_RECURRENT_EOM_SONOTACO_V31_SUPERIORITY_V1` requires **all four panels** to satisfy both:

- recurrent-EOM macro-F1 is strictly greater than exact v31 macro-F1; and
- recurrent-EOM recovered F1>0.5 is at least exact v31 recovered count.

This is deliberately stringent. No aggregate score, average, route-specific exception, or tie-break rescue is authorized.

### Secondary reporting: literature comparator

For each panel, also report whether recurrent-EOM beats the existing literature comparator under the same established pair gate: macro-F1 strictly greater and recovered F1>0.5 at least equal. This is descriptive unless all four panels pass.

If the primary v31 gate fails, recurrent-EOM v1 remains a valid **positive HDBSCAN modification on target-excluded GMN** but is not promoted over v31 as the overall OrbitTrace parent. No SonotaCo-informed tuning of recurrent-EOM v1 is authorized.

## 7. Scientific firewall

The result must record:

- `sonotaco_role='EXPOSED_DEVELOPMENT_ONLY'`;
- `blind_exclusion=[20.0,55.0]`;
- `target_information_access=false`;
- `target_region_events_accessed=false`;
- `maarsy_scientific_access=false`;
- `dms_scientific_access=false`;
- `post_result_parameter_search=false`.

No protected OrbitTrace information is required or authorized by this benchmark.
