# OrbitTrace cross-year observed-support envelope expansion v4 — frozen development protocol

## Purpose

Target-excluded membership-expansion v1–v3 all established the same positive mechanism: the exact promoted-v8 sparse recurrent families are high-purity seeds whose membership severely under-recovers real showers, and cross-year expansion can materially improve annual F1, especially for large showers. They also isolated the failure mechanism progressively:

- v1: any original other-year seed event within radius 1.5 admitted 174,594 new members;
- v2: requiring two event witnesses still admitted 168,808 because event witnesses were highly redundant within components;
- v3: collapsing each source component to one frozen centroid still admitted 162,646, proving that the fixed 1.5 family-link tolerance itself is too broad when reinterpreted as a membership envelope.

v4 changes only the *membership width* around each already-existing source component. It does not change detection, recurrence, family topology, scoring, or ranking.

## Pre-existing width definition

Before v1–v3 existed, frozen support-overlap v9 preregistered the parameter-free observed component radius

`R_obs(c) = max_e D(c.centroid, e)`

where `e` ranges over every unique original member event of component `c` and `D` is the exact frozen v6/v8 metric:

- wrapped solar-longitude difference / 4;
- wrapped Sun-centered longitude difference × cos(mean ecliptic latitude) / 2;
- ecliptic-latitude difference / 2;
- geocentric-speed difference / 2;
- Euclidean norm.

v9 failed because it used these widths to *replace cross-year recurrence adjacency*. That no-go does not test their use as a post-detection membership envelope while preserving the passed v8 recurrence graph and ranking.

v4 reuses this exact pre-existing width definition without modification.

## Frozen v4 membership rule

For each target year independently:

1. Reproduce the exact promoted-v8 target-excluded family universe and multiplicity ranking first.
2. For each family, take only its original frozen components from the other year.
3. For each source component, compute the exact v9 observed radius from all and only its original unique component member events.
4. Define the effective membership radius as

   `R_eff(c) = min(1.5, R_obs(c))`.

   The cap is the unchanged v8 predecessor family-link tolerance. v4 can therefore never open a membership ball broader than v3.
5. A non-seed target-year event is eligible for a family iff it lies within `R_eff(c)` of at least one of that family's other-year component centroids.
6. If multiple components in one family admit the event, that family's distance is the smallest raw exact centroid distance among admitting components.
7. If multiple families admit the event, assign it exclusively to the family with the smallest such raw exact distance; stable family ID breaks exact ties.
8. Original v8 seed events are retained. Newly assigned events never become support. No recursive growth occurs.

## Frozen base and blindness

- Base commit: promoted v8 `c9d6c44704013ba0c9430100e98a29a56b453304`.
- GMN development years: 2022 and 2023 only.
- Solar longitude 20°–55° is removed by the already-audited parser before label access.
- Exact v8 226-family structure, pooled family-year centroids, 128-event scoring, multiplicity values, and ranking must reproduce before expansion.
- No OrbitTrace coordinate, member, identity, target family, target-region event, Stage A/B output, reveal result, or literature-benchmark result may enter membership construction.

## No-search rule

There is no search over radius multiplier, radius quantile, percentile, offset, cap, component-count threshold, witness count, density threshold, pruning rule, normalized-distance tie break, recursive growth, reranking, score fusion, or evaluation endpoint.

The maximum-member radius is inherited exactly from preregistered v9. The 1.5 cap is inherited exactly from v8/v3. If this exact v4 fails, it is a permanent no-go and does not authorize a max-to-quantile rescue or any tuning of the cap.

## Evaluation and promotion gates

Reuse the exact v1/v2/v3 gates without relaxation. All must pass:

- multiplicity recovery@100 >= 58;
- qualified matches >= 95;
- top-100 dominant precision >= 0.65;
- global macro F1 gain >= 0.05 over v8;
- all-shower annual mean-F1 gain >= 0.10 in both 2022 and 2023;
- 4–9 annual-member mean F1 may not regress by more than 0.02 in either year;
- at least one of 10–24, 25–49, 50–99, or 100+ annual-member bins must gain >=0.10 mean F1 in both years;
- every inherited and v4-specific integrity/blindness gate must pass.

A pass promotes only the membership-expansion architecture for later fresh validation. It does not retroactively alter promoted v8, authorize OrbitTrace target access, or establish superiority over literature methods without a separately frozen fresh matched benchmark.
