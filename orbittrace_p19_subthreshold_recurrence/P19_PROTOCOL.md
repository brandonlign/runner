# OrbitTrace P19 — subthreshold reciprocal recurrence

## Status

P19 is a separately named target-free successor architecture frozen after the scientific no-go of B1 and after the P18 matched-literature no-go established that the remaining bottleneck is not only final membership assignment. It is developed only on the already-used, target-excluded GMN 2022/2023 panel. It must never consume the exposed SonotaCo 2023/2025 matched outcomes as tuning input.

P19 changes only **cross-year family existence for otherwise unmatched fixed4 components**. The exact promoted v8 detector, proposal generation, within-year components, hard cross-year family graph, pooled same-year centroids, 128-event multiplicity scoring, and hard-family ranking remain unchanged.

A P19 development pass would authorize only a separately frozen matched-literature comparison on a genuinely fresh panel selected under an independent metadata-only reservation. It would not establish literature superiority, external generalization, or OrbitTrace discovery.

## Scientific motivation

The post-v8 evidence now separates two bottlenecks.

1. P1/P2/P3/P4/P5/P6/P10/P11/P12/B1 show that much better final membership F1 is possible, but repeated membership-only successors lose qualified families or precision.
2. P18 matched benchmarking showed a family-coverage deficit in addition to membership error.
3. Earlier recurrence successors changed links **between already-detected components** (mutual/complete linkage, support-overlap, exact support contact) and did not solve the problem.

P19 therefore tests a different structural hypothesis: a real weak stream can produce a valid fixed4 component in one year while the counterpart year contains coherent support that falls exactly one event below the inherited four-event component floor. Hard recurrence then discards the family even though the second year contains geometrically reciprocal evidence.

## Target firewall

- Development years are GMN 2022 and 2023 only.
- Solar longitude 20°–55° remains removed by the inherited parser before proposal generation, family construction, label storage, or evaluation.
- No OrbitTrace coordinate, member, identity, historical family/rank, target-containing result, target-region event, or reveal artifact may enter P19.
- No SonotaCo matched comparator output may enter P19 development.
- Labels are first used only after the complete hard+soft family payload and order are frozen and SHA-256 hashed.

## Frozen ancestry

P19 requires the exact promoted v8 development result:

- v8 source commit: `c9d6c44704013ba0c9430100e98a29a56b453304`;
- v8 run: `31217916558`;
- v8 artifact: `9009728299`;
- v8 artifact digest: `sha256:88d2d607e05d027015c338f7e23b64a6195e55ae24f1b2ac745f5e9bc6df599e`;
- v8 result JSON SHA-256: `fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b`;
- 226 hard recurrent families;
- 95 qualified matches;
- multiplicity recovery@100 = 58;
- multiplicity macro F1 = 0.1736657194465356;
- top-100 dominant precision = 0.6884631112636006.

Inherited constants remain exact:

- label-free fixed4 proposal generation from v6;
- four-event / two-quartet within-year component floor;
- cross-year hard-family centroid link radius 1.5;
- minimum hard family recurrence of two years;
- v8 pooled same-year centroid repair;
- exact v8 multiplicity score and ordering.

## One P19 recurrence rule

P19 first reconstructs the exact v8 hard family universe and hard multiplicity ranking. It then considers only fixed4 components that belong to no hard recurrent v8 family.

For each unmatched component in a seed year:

1. In the other year, remove every event already belonging to **any** fixed4 component. This makes the soft support genuinely subthreshold rather than a second way of linking an already-detected component.
2. Find events whose exact inherited radiant/speed centroid distance to the seed centroid is at most 1.5.
3. The trigger is the nearest **three** such events. Three is fixed because it is exactly one event below the inherited four-event component floor; it is not selected from labels.
4. All three trigger events must be pairwise within exact inherited distance 1.5.
5. Their pooled centroid, using the inherited circular-mean/median statistic, must be within 1.5 of the seed centroid.
6. Reciprocity is required: among unmatched components in the seed year, the trigger centroid's nearest component within 1.5 must be the original seed component.
7. If the trigger passes, reported support in the other year is every unclaimed event lying in the **intersection** of the inherited 1.5-radius balls around the seed centroid and trigger centroid.
8. Soft events never become components, never become training/support points, and never recurse.
9. Exact duplicate event-set hypotheses are deduplicated deterministically by stronger seed-component evidence, then seed event count, then stable component ID. No overlap fraction or Jaccard threshold exists.

The distance 1.5 is inherited; no new radius or multiplier is introduced. There is no score threshold, posterior threshold, density threshold, event-count search, triplet-size search, or variant search.

## Ranking

The exact v8 hard multiplicity order is an immutable prefix. P19 soft families are appended only after all 226 hard families, ordered before labels by:

1. larger seed component strength;
2. smaller trigger maximum seed distance;
3. larger seed event count;
4. stable family ID.

This makes top-100 v8 ranking non-regression structural rather than fitted. P19 can improve coverage and deeper family quality without displacing a promoted hard family.

## Development evaluation

The exact v8 evaluator is used on the combined order after the pre-label payload hash is frozen. Annual size-bin diagnostics use only the already target-excluded hidden labels and the same family event sets.

P19 passes development only if every integrity gate and every scientific gate passes:

- qualified matches >= 95;
- recovery@100 >= 58;
- top-100 dominant precision >= v8 minus 0.02;
- macro F1 improves by at least +0.05;
- mean F1 for the 4–9-event shower bin improves by at least +0.05 in **both** 2022 and 2023;
- combined 4–24-event mean F1 is strictly higher in both years;
- the soft recurrence path is non-vacuous.

Because the hard v8 ranking is an exact prefix, the top-100 conditions are principally integrity checks. The material gates are macro-F1 and sparse-bin gains.

A scientific failure is `FAIL_P19_SUBTHRESHOLD_RECIPROCAL_RECURRENCE_DEVELOPMENT` and permanently rejects this exact rule. No change to triplet size, radius, reciprocity, support intersection, ordering, or gates may be made from the observed result.

## Pass boundary

A development pass authorizes only:

1. freezing P19 exactly;
2. obtaining a **new**, genuinely fresh matched SonotaCo panel under a separately preregistered metadata-only exposure audit;
3. comparing the unchanged P19 method fairly against the frozen Sugar and catalogue-HDBSCAN interfaces under the already frozen pairwise broad/sparse superiority rules.

External validation and the final target-containing search remain unauthorized until those later gates pass without retuning.
