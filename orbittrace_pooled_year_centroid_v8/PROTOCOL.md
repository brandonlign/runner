# OrbitTrace pooled-year-centroid v8 — frozen development protocol

## Purpose

v7 proved that enforcing one cross-year component per year fragments recurrent shower structure and is a scientific no-go. The preceding source-only audits also proved a narrower semantic defect in v6: connected recurrent families may legitimately contain multiple components from the same year, but the frozen family object stores year centroids through a dictionary comprehension and silently keeps only one centroid for duplicated years.

v8 repairs only that representation defect while preserving the passed v6 family graph and family universe.

## Frozen family construction

- Candidate generation, quartet formation, component generation, cross-year links, connected-family graph, family IDs, event unions, family counts, persistence ranking, component gates, and the 1.5 family-link radius are exactly the passed v6 implementation.
- Multiple components from the same year remain allowed inside a recurrent family.
- For each family-year, the episode centroid is recomputed from the union of unique events belonging to every component from that year.
- The pooling statistic is copied exactly from the source-audited component centroid construction:
  - solar longitude `sol`: circular mean;
  - Sun-centered ecliptic longitude `sun_lon`: circular mean;
  - ecliptic latitude `ecl_lat`: median;
  - geocentric speed `vg`: median.
- No component-centroid averaging, weighting rule, medoid, one-to-one matcher, radius change, or alternate pooling statistic is tested.

## Development panel and blindness

- GMN 2022 and 2023 only.
- Solar longitude 20°–55° is removed by the already-audited frozen parser before source-label normalization.
- Proposal generation, family construction, pooled centroids, local episodes, v3/Brown/multiplicity scores, and all four rankings are completed before known-shower labels are consulted.
- No OrbitTrace coordinate, member, identity, prior target family, or target-region event may enter this development.

## Scoring and rankings

- Exact 128-event local episodes.
- Exact multi-anchor v3 and independent Brown comparator.
- Multiplicity remains `M=(v3/Brown)^2`.
- Primary ranking remains worst-year multiplicity, then geometric-mean multiplicity, then stable family ID.
- Brown and total-v3 are comparators.
- Label-free persistence remains the separate structural comparator.
- No RRF, threshold search, radius search, cap search, weight search, endpoint search, or pooling-rule search.

## Required structural reproduction

v8 must preserve the passed v6 structure rather than create a new candidate universe:

- exactly 226 recurrent families;
- exactly the same family IDs/component IDs/event IDs and label-free persistence ordering before centroid replacement;
- persistence benchmark must reproduce 59 known showers recovered in the top 100 and 95 qualified matches;
- at least one family must contain multiple same-year components, proving the repair is non-vacuous;
- every pooled centroid must be computed from unique family-year events using the source-audited statistic above.

## Scientific gates

The same v6 gates are retained without relaxation:

1. label-free persistence recovery@100 >= 55;
2. multiplicity recovery@100 >= Brown recovery@100 + 1;
3. multiplicity recovery@100 >= ceil(0.90 × persistence recovery@100);
4. multiplicity recovery@100 >= 54;
5. multiplicity top-100 dominant precision >= 0.50.

The general integrity floors also remain unchanged: >=100 recurrent families, >=72 qualified known showers, >=24 scannable bins each year, exact 128-event episodes, exact Brown equivalence, zero label-dependent calibration, and no score threshold.

## Decision rule

Pass only if every structural, integrity, and scientific gate passes. Failure is a scientific no-go for pooled-year-centroid v8 and does not authorize any alternative centroid pooling rule or OrbitTrace reveal.

A pass authorizes a separately frozen external-validation protocol on a still-fresh survey. AMOR 1990–1999 is currently reserved for that role and must remain unopened until v8 passes.
