# OrbitTrace label-free sparse-support one-to-one family v7 — frozen development protocol

## Purpose

This is a separately named successor to label-free sparse-support multiplicity v6. It addresses one source-semantic defect found by the zero-data family-link audit: the frozen v6 family builder uses unconstrained connected components of a cross-year graph, so alternating-year paths can merge multiple components from the same year into one family, after which the family `centroids` dictionary retains only one centroid per duplicated year.

v7 changes **only cross-year family formation**. Proposal generation, component generation, geometry, radius, local episodes, multiplicity score, rankings, blindness, and evaluation gates remain inherited from v6.

## Development data and blindness

- Development years: GMN 2022 and 2023 only.
- Solar longitude 20°–55° is removed by the already-audited frozen parser before label normalization or any target-region use.
- No 2024–2026 catalogue is loaded.
- Shower labels do not enter proposal generation, component formation, family matching, episode scoring, or ranking.
- Labels are first consulted only after all v7 rankings are frozen.
- No OrbitTrace coordinate, member list, family identity, score, or target-region event may enter this development.

## Frozen inherited v6 machinery

Unchanged from the passed v6 development:

- exact fixed4 anchored-quartet structural proposal generator with **no label-dependent calibration threshold**;
- 4° angular / 10% speed geometry inherited from the frozen fixed4 source;
- first shortlist 64 and exact audit shortlist 128;
- minimum anchor multiplicity 2;
- maximum 512 retained quartets per fixed 10° bin;
- component minimum 4 events and 2 quartets;
- cross-year centroid-distance definition unchanged;
- **family-link radius remains exactly 1.5**;
- exact local episode size 128;
- multiplicity `M=(multi-anchor-v3 energy / Brown peak)^2`;
- primary ranking: worst-year multiplicity descending, then geometric-mean multiplicity descending, then stable family id;
- Brown, total-v3, and structural persistence remain comparators only;
- no RRF;
- no threshold, radius, cap, weight, endpoint, or parameter grid search.

## The only v7 scientific change: one-component-per-year recurrence

After v6 component generation, split components into the two frozen development years. An eligible edge exists iff the **unchanged frozen centroid distance is <= 1.5**.

v7 forms recurrent families by a deterministic bipartite assignment with the following lexicographic objective:

1. **maximize the number of cross-year matched component pairs** subject to one component being used at most once;
2. among maximum-cardinality matchings, **minimize total frozen centroid distance**;
3. stable component-id ordering is used for deterministic tie handling.

The implementation uses a square assignment with dummy unmatched nodes. The unmatched penalty is derived mechanically as `FAMILY_LINK_RADIUS + 1`, not tuned from data. Any eligible real-real match therefore strictly improves the objective over leaving both endpoints unmatched. An independent deterministic maximum-cardinality bipartite matcher must reproduce the same cardinality.

Every v7 family therefore contains exactly two components: one from 2022 and one from 2023. No component may appear in more than one family. Family event ids are the union of the two matched components; family year strengths and centroids are taken directly from those two components. No same-year transitive percolation is possible.

## Frozen development gates

### Integrity / power

All must pass:

- exact frozen v6/source self-tests and target-excluded 2022–2023 panel;
- zero label-dependent calibration events and no proposal score threshold;
- at least 24 scannable bins in each year;
- every matched edge has frozen centroid distance <= 1.5;
- assignment cardinality equals an independent maximum-cardinality bipartite solution;
- every family has exactly one component from each year;
- no component is reused across families;
- at least 100 recurrent families;
- exact local episode size 128 for every family/year;
- Brown equivalence error <= 1e-10;
- at least 72 qualified known showers, assessed only after ranking freeze.

### Scientific

The same inherited v6 development floors are retained:

- structural persistence recovers at least 55 qualified known showers in the top 100;
- multiplicity recovers at least one more than Brown in the top 100;
- multiplicity recovers at least 90% of structural persistence top-100 recovery;
- multiplicity recovers at least 54 qualified known showers in the top 100;
- multiplicity top-100 dominant precision is at least 0.50.

A pass only promotes the corrected family semantics for a separately frozen validation stage. It does **not** rehabilitate or reinterpret either terminal SAAMER v6 power-inconclusive result and does not authorize OrbitTrace reveal.

## No-go rule

This is one fixed successor, not a family-link hyperparameter study. If v7 fails, the matching objective, link radius 1.5, proposal cap, component gates, multiplicity score, and scientific floors will not be altered to make this development panel pass. The result will be preserved as a no-go for this formulation.
