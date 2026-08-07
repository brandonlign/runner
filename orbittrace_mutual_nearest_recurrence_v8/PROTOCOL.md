# OrbitTrace mutual-nearest bottleneck-recurrence v8 — frozen development protocol

## Purpose

v8 is a separately named successor after the preregistered v7 one-to-one family formulation failed its scientific gates despite passing every integrity/power gate. The v7 source semantics and result identify a specific architectural problem: maximizing global match cardinality can reassign a component away from its locally closest physical counterpart in order to increase the total number of pairs.

v8 makes one fixed change to the family-association rule and one pre-existing structural ranking explicit as the discovery output. It does not search matching variants, radii, thresholds, weights, or endpoints.

## Development data and blindness

- GMN 2022 and 2023 development years only.
- Solar longitude 20°–55° remains removed by the already-audited frozen parser before label normalization or any target-region use.
- No 2024–2026 catalogue is loaded.
- No source shower label enters proposal generation, component formation, cross-year association, structural ranking, episode scoring, or rank freezing.
- Labels are consulted only after every v8 ranking is frozen.
- No OrbitTrace coordinate, member list, family identity, target-region event, or target score may enter development.

## Frozen inherited machinery

Unchanged from passed label-free v6 and failed-but-integrity-clean v7:

- exact label-free fixed4 anchored-quartet proposal generator;
- 4° angular / 10% speed geometry;
- first shortlist 64; exact audit shortlist 128;
- minimum anchor multiplicity 2;
- maximum 512 retained quartets per fixed 10° bin;
- component minimum 4 events / 2 quartets;
- exact frozen centroid-distance definition;
- cross-year eligibility radius **1.5**;
- exact local episode size 128;
- multiplicity `M=(multi-anchor-v3 energy / Brown peak)^2`;
- Brown and total-v3 comparators;
- no label-dependent calibration threshold;
- no RRF;
- no threshold, radius, cap, weight, endpoint, or parameter-grid search.

## The only v8 family-association change: reciprocal nearest neighbors

Let A be the 2022 components and B the 2023 components. For every component, calculate the exact frozen centroid distance to components in the other year. An edge is eligible only if distance <= the unchanged radius 1.5.

For each component in A, select its nearest eligible component in B, breaking an exact distance tie by stable component id. Independently, for each component in B, select its nearest eligible component in A with the same deterministic tie rule.

A recurrent v8 family exists **only when the two selections are reciprocal**. Therefore:

- every family contains exactly one 2022 and one 2023 component;
- no component can occur in more than one family;
- no global cardinality objective can steal a locally closest pair;
- no alternating-year transitive percolation can occur;
- no new distance threshold or margin parameter is introduced.

## Frozen primary discovery ranking

The primary catalogue-discovery ranking is the immutable support code's pre-existing `min_year_strength` ranking, here named **bottleneck recurrence**. This score existed in frozen support source SHA-256 `fa18a19c08c6824c66606cbd92095dc3605cbcc30f17a468c9e525e7c6ff4a62` before the v7 result and is not selected from a post-v7 ranking grid.

For a two-year family the frozen support definition is:

`min_year_strength = min(year_strength_2022, year_strength_2023) * sqrt(2)`

and the exact pre-existing support ranking/tie rules are reused unchanged.

Rationale: a recurrent discovery should be limited by its weaker annual manifestation rather than by total event count or by forcing a globally maximal assignment. This is a structural recurrence score, not a shower-label score.

The following are comparators/secondary outputs only:

- plain structural `persistence` ranking from the same frozen support code;
- multiplicity M;
- Brown;
- total-v3.

Multiplicity remains scientifically useful as a separate sparse-episode recognition output, but v8 does not force it to be the catalogue-discovery rank after v7 showed that it is not invariant to corrected family semantics.

## Frozen development gates

### Integrity / power

All must pass:

- exact frozen v6/source self-tests and exact target-excluded 2022–2023 panel;
- the preserved v7 result is `FAIL_ONE_TO_ONE_FAMILY_V7_DEVELOPMENT` with every v7 integrity gate true;
- zero label-dependent calibration events and no proposal score threshold;
- at least 24 scannable bins in each year;
- every family edge is reciprocal nearest-neighbor under the exact frozen distance and <=1.5;
- every family contains exactly one component from each year;
- no component is reused;
- at least 100 recurrent families;
- exact local episode size 128 for every family/year;
- Brown equivalence error <=1e-10;
- at least 72 qualified known showers, assessed only after rank freezing.

### Scientific

The primary bottleneck-recurrence discovery output must satisfy all of:

1. recovered qualified known showers at top 100 >= **55** (the inherited v6 structural-recovery floor);
2. top-100 dominant precision >= **0.50**;
3. top-100 recovery >= the same-family plain persistence comparator.

Multiplicity, Brown, and total-v3 are reported without becoming promotion gates. No alternative frozen support ranking is evaluated for promotion in this one-shot development.

## Promotion boundary

A v8 pass authorizes only a separately frozen external-validation protocol on a scientifically fresh survey. It does not rehabilitate v7, reinterpret the two terminal SAAMER v6 power-inconclusive panels, or authorize OrbitTrace reveal.

## No-go rule

If v8 fails, do not alter reciprocal-nearest semantics, radius 1.5, the bottleneck ranking, proposal cap, component gates, or scientific floors to make this panel pass. Preserve the result as a no-go for this formulation. No OrbitTrace target reveal follows a failure.
