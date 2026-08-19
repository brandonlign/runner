# M2D blind OrbitTrace rediscovery v1

## Scientific question

Can the already-defined support-resolved TopoModal + annual-density internal-mass (`M_2D`) method recover OrbitTrace when the scan and ranking are constructed without OrbitTrace coordinates, activity interval, family identity, canonical member IDs, HDBSCAN assignments, or any prior reveal output?

## Method identity

The scientific method is fixed to the existing M2D line:

- physical GEO embedding and radius `1.0`;
- support-resolved TopoModal cut with minimum support `4`;
- annual-density internal persistence mass
  `M_2D(S) = (1 / |S|) * sum_{B subseteq S} |B| A(B)`;
- final order: `M_2D` descending, then frozen modal contrast descending, then family hash ascending.

No shower labels or OrbitTrace information may enter candidate generation or ranking.

## Data

Use the already-audited target-free GMN catalogue loader from the prior blind-catalogue application. The intended scientific corpus is GMN 2022 and 2023 SPORADIC residuals with the target interval retained. Those two years contain the canonical historical OrbitTrace sample only for the later exact-ID reveal; the scan may not access that table.

The loader/source interface is inspected before scientific execution solely to reuse the existing full-catalogue transport. Source inspection may not read meteor rows or target information and cannot score M2D.

## Reveal

The complete M2D candidate payload and total order must be persisted and SHA-256 frozen before the canonical OrbitTrace event table is opened. Reveal is exact event-ID intersection only. No coordinate, radiant, speed, orbital, activity-time, nearest-neighbour, family merge, member expansion, or reranking operation is allowed after reveal.

Report for the best-overlap frozen family:

- global rank and candidate count;
- exact canonical IDs recovered in 2022 and 2023;
- total exact overlap;
- precision and recall relative to the 18 canonical 2022+2023 members;
- whether the family meets `>=4` exact IDs in each year and `>=8` total.

Classify:

- `FULL_M2D_BLIND_ORBITTRACE_REDISCOVERY` if the above exact-ID gate passes at rank <=25;
- `PARTIAL_M2D_BLIND_ORBITTRACE_REDISCOVERY` if it passes at rank <=100;
- otherwise `NO_M2D_BLIND_ORBITTRACE_REDISCOVERY`.

The first technically valid execution under a frozen scan architecture is binding. Technical failures before a candidate ranking is frozen may be repaired without changing the scientific method.