# OrbitTrace PhysCore-HDBSCAN v1 — frozen exposed-development protocol

## Scientific question

Can a meteor-physics membership regularizer improve the exact published 2025 catalogue-HDBSCAN detector without changing HDBSCAN itself?

This successor treats the published HDBSCAN output as an immutable proposal catalogue. It does not tune, rerun, split, re-rank, or otherwise alter the HDBSCAN hierarchy/EOM selection. It only removes proposal members that lack recursively self-consistent support at the independently frozen OrbitTrace physical scale.

## Exact parent comparator

The parent is the exact published catalogue-HDBSCAN implementation already frozen in the OrbitTrace matched-literature benchmark:

- 2013 artifact `9273244387` from workflow run `31984184708`;
- 2014 artifact `9273244072` from workflow run `31984184708`;
- HDBSCAN 0.8.44;
- published GEO6 representation/quality filtering;
- `min_cluster_size=100`;
- `min_samples=100`;
- Euclidean metric;
- EOM selection.

Its frozen candidate catalogues contain 11 families in 2013 and 9 in 2014.

## PhysCore refinement

For each published HDBSCAN family independently:

1. Use only the events already assigned to that HDBSCAN family.
2. Embed them in the exact previously frozen TopoModal physical coordinates: `[cos(sol)/h_sol, sin(sol)/h_sol, cos(lat)cos(lon)/h_rad, cos(lat)sin(lon)/h_rad, sin(lat)/h_rad, log(vg)/h_logv]`, with `h_sol = 2 sin(5 deg / 2)`, `h_rad = 2 sin(4 deg / 2)`, and `h_logv = ln(1.1)`.
3. Build the exact Euclidean radius-1 graph.
4. Compute its maximal 3-core by recursively removing every active event with fewer than 3 active other neighbours. Equivalently, an event must retain support from at least 4 events including itself, matching the already-frozen TopoModal support floor.
5. If at least four events survive, the surviving union is the refined family. The core is not split into connected components. If fewer than four survive, preserve the original HDBSCAN family unchanged.
6. Preserve the original HDBSCAN family order and output exactly one refined family for every parent family. Candidate count therefore remains exactly 11 (2013) / 9 (2014).

No threshold, scale, support, HDBSCAN parameter, component split, branch score, candidate count, or ranking is free after this protocol.

## Why this is distinct

This is not FLASC-style branch detection: PhysCore does not infer or report branches and does not split an HDBSCAN cluster. It is a domain-specific fixed-physical-scale membership regularizer applied after published HDBSCAN selection.

It is also not a TopoModal successor: no ToMATo hierarchy or persistence ranking is used. Only the previously frozen physical metric and support floor are reused as an independent physical coherence prior.

## Label-free activation gates

Before any shower truth is opened:

- source and output hashes are frozen;
- protected solar longitude `[20,55]` is absent;
- every candidate is a subset of its exact parent HDBSCAN family;
- every candidate has at least four events;
- candidate counts equal exact HDBSCAN counts in both years;
- no event outside the corresponding frozen annual HDBSCAN row universe can enter;
- at least one family is strictly refined in each year;
- target information/events, MAARSY and DMS remain inaccessible.

## Binding exposed-development gate

After the pretruth freeze, evaluate against exactly the same SonotaCo 2013/2014 truth mapping and matched Hungarian macro-F1 semantics as the flagship literature benchmark.

`PASS_PHYSCORE_HDBSCAN_V1_DEVELOPMENT` requires both years to satisfy:

- PhysCore macro-F1 strictly greater than exact published HDBSCAN macro-F1; and
- PhysCore recovered-shower count at F1 > 0.5 at least the exact published HDBSCAN count.

Anything else is `FAIL_PHYSCORE_HDBSCAN_V1_DEVELOPMENT`.

The first technically valid outcome is binding. A failure does not authorize changes to the physical scale, support floor, peeling rule, fallback, family order, HDBSCAN settings, metrics, truth mapping, or pass gate.

## Scientific role and firewall

SonotaCo 2013/2014 is EXPOSED DEVELOPMENT ONLY. This is not pristine external validation. Protected `[20°,55°]`, OrbitTrace target information/events, MAARSY, and DMS remain inaccessible.
