# Topomodal lineage-balanced v1 — conditional exposed SonotaCo transfer benchmark

## Status

This protocol is frozen **before the first technically valid target-excluded GMN truth outcome of topomodal lineage-balanced v1**. It is conditional: execute it only if the already-frozen GMN sparse-recovery test returns `PASS_TOPOMODAL_LINEAGE_BALANCED_V1`.

SonotaCo 2013/2014 is **EXPOSED DEVELOPMENT ONLY**, never pristine external validation. This protocol does not authorize access to the protected OrbitTrace solar-longitude interval `[20°,55°]`, OrbitTrace target information/events, MAARSY, or DMS.

No GMN result and no SonotaCo result may change the method, radius, density definition, hierarchy construction, candidate universe, lineage definition, node score, ranking order, row eligibility, comparator budgets, or evaluation semantics below.

## 1. Frozen successor

Use topomodal lineage-balanced v1 exactly as frozen on branch `agent/orbittrace-topomodal-lineage-balanced-v1` before GMN truth:

- protocol blob: `948df181e250d7c27f39ebe5d7f386da52f33ff1`;
- generator blob: `a0305a5a88cfa9cf275fd121693903ac161769ff`;
- evaluator blob: `e4b79f4c4cfa1ade64f81ef6e15d546ffdd2ce2b`.

Scientific method, unchanged:

- GEO6 physical embedding;
- exact Euclidean radius graph, radius `1.0`;
- density `rho_i = degree_i / n` on the accessible pooled catalogue;
- GUDHI ToMATo manual graph/manual density hierarchy;
- minimum reported candidate support `4`;
- candidate universe = every unique support-4 membership in the complete exact ToMATo hierarchy, including surviving/root memberships;
- each hierarchy node is assigned to its surviving active density-mode lineage;
- node score = exact density-level lifetime of that membership between its formation level and the next enclosing merge level, with root outside level fixed at `0`;
- within each lineage, nodes are ordered by decreasing density-level lifetime then deterministic family hash;
- lineage round is the 1-based position within that lineage;
- final global rank = `(lineage_round ascending, density-level lifetime descending, family hash ascending)`.

No labels, shower identities, comparator scores, candidate budgets, SonotaCo outcomes, or GMN truth values may enter candidate generation or ranking.

## 2. Frozen label-free SonotaCo inputs

Reuse the exact label-free SonotaCo preparation and row eligibility from the historical recurrent-EOM/v31 benchmark protocol (`orbittrace_recurrent_eom_sonotaco_v31_benchmark_v1/PROTOCOL.md`, blob `7c269adf77fb8758bd5d95b7a479237f08f8dafd`).

Exact label-free preparation artifact:

- artifact `9050107352`, `orbittrace-final-sonotaco-label-free-preparation-v2`;
- artifact digest `sha256:1296d757b5ea1dd94f9c9077fd769fdc8f00ec06d0881d8548fd1df4608344cc`.

Matched routes and exact accessible row bytes:

### Sugar-matched route

- `sugar_2013.json`: SHA-256 `47fb0b700fbf710c7b061eead343016bd8d182756eb0c7f406507c5739e4c4f8`, 18,638 events;
- `sugar_2014.json`: SHA-256 `bc83c113e9a14b1c6e1ef460ca9a40e05df77f3a449fec6064f8910add04c912`, 15,400 events.

### HDBSCAN-matched route

- `hdbscan_2013.json`: SHA-256 `2433b556d4a859580ef5431d2307ef34c8fa4c15d42841a2ec7b0c11e5f1f158`, 16,028 events;
- `hdbscan_2014.json`: SHA-256 `206692292b2ca252777e40c13c367880740d8e2576d27615f7ea94b7790e3f55`, 13,283 events.

Pool 2013+2014 label-free rows separately for each matched route before constructing the graph/hierarchy. Only `id`, `year`, `sol`, `sun_lon`, `ecl_lat`, and `vg` may enter the successor. Orbital elements and hidden truth placeholders do not enter the method.

Every row must already satisfy the blind exclusion. Encountering any event with solar longitude in `[20°,55°]` is a fail-closed error.

## 3. Mandatory pre-truth freeze

For each route, complete the full exact radius graph, ToMATo hierarchy, all support-4 memberships, active-mode lineages, density-level lifetimes, and complete deterministic lineage-balanced candidate ranking **before** loading any SonotaCo shower truth, historical recurrent-EOM result bytes, v31 result bytes, or literature comparator result bytes into the benchmark process.

Serialize both complete route rankings to a single immutable pretruth artifact and SHA-256 seal it before truth/evaluation access.

A technical failure before the pretruth SHA exists is a no-result and may receive engineering-only repair only if candidate memberships/ranking semantics remain byte-for-byte/scientifically unchanged.

## 4. Frozen evaluation semantics

After pretruth freeze only, load the same immutable exposed SonotaCo truth/evaluation artifact used by v22-v31 and recurrent-EOM:

- artifact `9069505548`;
- `truth_{route}_{year}.json`;
- `evaluation_{route}_{year}.json`.

For each of the four panels use the exact historical matched evaluator:

1. restrict each pooled successor candidate's members to that panel year's truth IDs;
2. preserve the already-frozen pooled lineage-balanced candidate order;
3. truncate to `evaluation_{route}_{year}.json['candidate_budget']['comparator_budget']`;
4. include every panel shower having at least four truth events;
5. construct the shower-by-candidate F1 matrix;
6. use the exact Hungarian maximum-F1 one-to-one assignment;
7. report macro-F1 and number of assigned showers with F1 `>0.5`.

No candidate may be removed, inserted, reranked, split, merged, annualized, or otherwise altered after truth load.

Exact panel budgets remain:

- Sugar 2013: `34`;
- Sugar 2014: `46`;
- HDBSCAN 2013: `11`;
- HDBSCAN 2014: `9`.

## 5. Frozen controls

### Selected parent: recurrent-EOM HDBSCAN v1

Use binding run `31829200215`, artifact `9230008341`, result SHA-256 `c2395a86be5ba8a8b801210ac6e64b97c446e724991207aef85062ee00b89f12`.

Exact recurrent-EOM panel controls:

| Panel | macro-F1 | recovered F1>0.5 |
|---|---:|---:|
| Sugar 2013 | 0.3752906816 | 23 |
| Sugar 2014 | 0.4377312230 | 24 |
| HDBSCAN 2013 | 0.1914598192 | 11 |
| HDBSCAN 2014 | 0.1685878550 | 9 |

### v31 control

Use authoritative v31 run `31509767311`, artifact `9108560001`, pinned result SHA-256 `f69555d443f453fd40a769da09b2bbec8bf62cd4a932cd84278bb23305b5ac8e`.

Exact v31 controls:

| Panel | macro-F1 | recovered F1>0.5 |
|---|---:|---:|
| Sugar 2013 | 0.2719801488280529 | 16 |
| Sugar 2014 | 0.31529041952487225 | 17 |
| HDBSCAN 2013 | 0.14888037368183737 | 9 |
| HDBSCAN 2014 | 0.15198123772301594 | 9 |

Historical literature controls, descriptive only:

- Sugar 2013: `0.2037265747 / 13`;
- Sugar 2014: `0.2590152773 / 15`;
- HDBSCAN 2013: `0.1681302505 / 10`;
- HDBSCAN 2014: `0.1568959558 / 9`.

The benchmark must verify pinned control bytes/values exactly before scientific interpretation.

## 6. Frozen transfer gates

Primary verdict `PASS_TOPOMODAL_LINEAGE_BALANCED_SONOTACO_V1` requires **all four panels** to satisfy both relative to the selected recurrent-EOM parent:

- successor macro-F1 is **strictly greater** than recurrent-EOM macro-F1; and
- successor recovered F1>0.5 count is **at least** the recurrent-EOM recovered count.

No averaging, route-specific exception, aggregate rescue, or tie-break rescue is authorized.

Secondary reporting must also state the identical pair gate versus v31 and versus the literature comparator on each panel, but these do not replace the primary recurrent-EOM gate.

If any primary panel fails, the exposed transfer verdict is FAIL and this exact successor is not rescued or tuned using SonotaCo outcomes.

## 7. Firewall and role

Every output must record:

- `sonotaco_role='EXPOSED_DEVELOPMENT_ONLY'`;
- `conditional_on_gmn_pass=true`;
- `blind_exclusion=[20.0,55.0]`;
- `target_information_access=false`;
- `target_region_events_accessed=false`;
- `maarsy_scientific_access=false`;
- `dms_scientific_access=false`;
- `post_result_parameter_search=false`.

This protocol authorizes no OrbitTrace target access and no pristine-validation claim.