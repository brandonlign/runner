# OrbitTrace P20 — recurrent isolated-quartet rescue

## Status

P20 is a preregistered contingency successor frozen **while the exact P19 development run is still in progress and before its scientific result is known**. It is dormant unless P19 returns a genuine scientific development failure. A P19 pass keeps P20 unexecuted.

P20 is deliberately not a P19 parameter variant. P19 starts from an unmatched four-event/two-quartet fixed4 component in one year and searches for a three-event counterpart in the other year. P20 instead tests a different coverage bottleneck: whether a genuine recurrent stream can produce a strong retained fixed4 **quartet proposal in each year** while failing the inherited within-year requirement that a component contain at least two retained quartets.

The target-excluded GMN 2022/2023 development corpus remains the only development data. No SonotaCo 2013/2014 scientific value, MAARSY scientific value, or OrbitTrace target information may enter P20.

## Frozen ancestry

P20 preserves the promoted v8 scientific backbone exactly:

- promoted v8 source commit `c9d6c44704013ba0c9430100e98a29a56b453304`;
- v8 development result SHA-256 `fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b`;
- label-free fixed4 proposal generation from v6;
- first shortlist 64 and audit shortlist 128;
- fixed4 candidate scale 4;
- retained-quartet anchor multiplicity >=2;
- maximum 512 retained quartets per fixed 10° solar-longitude bin;
- exact v6 within-year component construction and hard family graph;
- hard family-link radius 1.5;
- exact v8 pooled same-year centroid repair;
- exact 128-event multiplicity score and hard-family ranking.

The existing v8 hard family universe/ranking remains an immutable non-regression backbone.

## One scientific change

After reconstructing exact retained fixed4 quartets and exact v8 components in each year, P20 identifies **isolated retained quartets**:

1. Start from the exact label-free retained quartet list returned by frozen v6 `label_free_scan_year`.
2. Build the exact v8 within-year components unchanged.
3. Form the set of all event IDs belonging to any exact v8 component in that year.
4. A retained quartet is P20-eligible only if **none** of its four event IDs occurs in any v8 component. A quartet sharing even one event with an existing component is excluded. This prevents P20 from becoming a second representation of already-detected component structure.
5. If the same exact four-event set appears more than once because of fixed-bin proposal bookkeeping, keep exactly one record before cross-year linking, using the frozen label-free order: larger anchor count, then larger bin strength, then larger quartet score, then smaller bin index, then lexicographic event-ID tuple.
6. Compute each eligible quartet centroid with the exact inherited pooled statistic: circular mean for solar longitude and Sun-centered ecliptic longitude, median for ecliptic latitude and geocentric speed.

No event-level expansion, new within-year threshold, learned model, posterior, density estimate, label, or target information is used.

## Reciprocal cross-year quartet recurrence

For every isolated retained quartet in 2022 and 2023:

1. Candidate cross-year partners must have exact inherited centroid distance <=1.5.
2. For each quartet, choose its single nearest eligible quartet in the other year under the exact centroid distance. Ties are resolved before labels by: smaller distance, then larger partner anchor count, then larger partner bin strength, then larger partner score, then lexicographic partner event-ID tuple.
3. A P20 soft family exists only for a **mutual nearest-neighbor pair**: the 2022 quartet chooses the 2023 quartet and the 2023 quartet chooses the 2022 quartet.
4. The reported family membership is exactly the eight quartet events: four from 2022 and four from 2023. There is no halo, envelope, interpolation, member expansion, recursion, or reassignment.
5. Exact event-set duplicates are impossible after mutual one-to-one pairing, but any implementation-level duplicate must be removed by exact full family event-ID tuple only; no overlap/Jaccard threshold is permitted.

The inherited radius 1.5 is reused because it is already the fixed v8 family-link geometry scale. P20 introduces no new scientific radius.

## Ranking

Reconstruct exact v8 hard multiplicity order first. It must remain the complete immutable prefix of the P20 order.

All P20 isolated-quartet families are appended after the hard v8 prefix and ordered before labels by:

1. smaller cross-year quartet-centroid distance;
2. larger minimum anchor count across the two quartets;
3. larger minimum bin strength across the two quartets;
4. larger minimum quartet score across the two quartets;
5. stable family ID.

Thus no P20 family can demote an existing v8 family or alter v8 top-100 ranking.

## Why this mechanism is distinct

P20 tests the inherited **two-quartet component-support floor**, not the P19 other-year event-support floor and not final membership expansion. It can recover a recurrent 4+4-event family even when **neither year forms a v8 component at all**. It therefore addresses a family-generation failure mode that P19 cannot represent.

P20 also differs from earlier linkage-topology successors: those rearranged links among already-existing components. P20 creates recurrent candidates from retained label-free fixed4 proposals that were excluded before component formation.

## Pre-label freeze

The complete exact v8 hard family payload/order plus every P20 quartet-pair family, membership, distance, label-free ranking key, and combined order must be serialized and SHA-256 hashed before the first hidden known-shower label is evaluated.

Known-shower labels may not enter quartet eligibility, deduplication, cross-year pairing, ranking, or any parameter.

## Development gates

P20 uses the same strong primary development standards preregistered for P19 so a successor cannot be promoted merely because it adds candidates monotonically.

Integrity gates require:

- exact target-excluded GMN 2022/2023 panel;
- exact promoted-v8 hard family count and hard multiplicity order reproduced on the unmodified panel;
- exact fixed4 retained-quartet source/gates reproduced;
- every P20 quartet has exactly four events and zero overlap with all existing same-year v8 component events;
- every P20 family is exactly one reciprocal 2022 quartet plus one reciprocal 2023 quartet;
- all cross-year centroid distances <=1.5;
- hard v8 ranking is an exact immutable prefix;
- full pre-label payload hash exists before evaluation;
- no parameter/radius/threshold/ranking/model/variant search;
- no target information access.

Scientific PASS requires all of:

- qualified matches >=95;
- recovery@100 >=58;
- top-100 dominant precision equal to the v8 hard-prefix value within `1e-12`;
- macro F1 >= v8 macro F1 +0.05;
- annual 4–9-member shower mean F1 >= v8 +0.05 in **both 2022 and 2023**;
- combined 4–24-member shower mean F1 strictly greater than v8 in both years;
- the isolated-quartet recurrence path is non-vacuous.

The only PASS is `PASS_P20_RECURRENT_ISOLATED_QUARTET_DEVELOPMENT`. Any power-eligible scientific failure is `FAIL_P20_RECURRENT_ISOLATED_QUARTET_DEVELOPMENT` and permanently rejects this exact rule.

After a P20 result is known, the project may not change quartet eligibility, component-overlap exclusion, radius, reciprocity, deduplication, membership, soft-family order, or development gates and re-present the modified method as the same preregistered test.

## Downstream boundary

A P20 development PASS would not automatically open SonotaCo. It would first require the same fixed internal robustness and final-candidate declaration process required by current governance. Only one explicitly frozen `FINAL_FOR_LITERATURE_TEST` method may consume the permanent SonotaCo 2013/2014 literature test.

The final literature, MAARSY 2020/2021 no-retuning external, and exact-ID blind OrbitTrace gates remain exactly those already frozen in `orbittrace_governance/`.

## Target firewall

P20 source, development, stress testing, selection, and any source-only downstream preparation must not contain or access OrbitTrace coordinates, identity, canonical members, prior target recovery, target-containing candidate output, or any scientific event in solar longitude 20°–55°. The target remains inaccessible until final literature superiority and no-retuning external generalization have both passed.
