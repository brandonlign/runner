# OrbitTrace cross-year seed-support expansion v1 — frozen development protocol

## Purpose

The promoted v8 catalogue architecture is a strong recurrent-core finder but a weak membership estimator. On the frozen target-excluded GMN 2022–2023 development artefact, the 95 qualified known-shower matches have median family precision 1.00 but median recall only 0.066; none reaches 0.50 recall. The matched SonotaCo literature benchmark shows the same structural pattern: v8 is closest to the published methods in the 4–9-member regime and falls progressively behind as annual shower size increases.

This successor does **not** alter v8 proposal generation, components, recurrence topology, centroids, scoring, or ranking. It tests one new post-ranking membership layer: use each recurrent family’s seed events from the other year as a target-free support template, and expand membership only to target-year events that lie within the already-frozen v8 family-link radius.

## Frozen architecture

1. Reproduce exact promoted v8 on GMN 2022 and 2023 with solar longitude 20°–55° excluded before labels.
2. Freeze all v8 families, pooled family-year centroids, multiplicity scores, and the exact v8 multiplicity ranking before membership expansion.
3. For each target year `y`, and each frozen v8 family, define the support set as that family’s **original seed events from the other year only**.
4. For every target-year event, compute the minimum exact inherited v8 radiant-speed distance to every eligible family’s other-year seed support.
5. A family is eligible for that event iff the minimum distance is `<= 1.5`, exactly the inherited v8 cross-year family-link radius. No new scale or threshold is introduced.
6. If more than one family is eligible, assign the event to the family with the smallest exact distance, ties by stable family ID.
7. Original same-year seed events are always retained in their original family and are never reassigned.
8. Expansion is one pass only. Newly assigned events cannot become support points, cannot change centroids, cannot change recurrence, and cannot change the v8 ranking.

The expansion is therefore a cross-fitted membership estimator, not a second detector and not graph growth.

## Computational prefilter

Exact eligibility is always decided by the inherited `centroid_distance` function. For speed only, candidate target events may be prefiltered by the mathematically necessary solar-longitude condition implied by distance `<=1.5`: an eligible event must lie within 6° solar longitude of at least one other-year seed event because the solar term is `wrap180(d_sol)/4`. The implementation may use the minimal circular arc containing a family’s support and expand that arc by exactly 6°. Every retained candidate is then checked with the exact full distance. No approximate distance can create an assignment.

## Development panel and blindness

- GMN 2022 and 2023 only, the already-exposed target-excluded development panel.
- Solar longitude 20°–55° remains removed before source-label normalization or any method operation.
- No OrbitTrace coordinate, member, identity, prior target family/rank, or target-region event may enter this work.
- Shower labels may be consulted only after the complete expanded membership payload and its SHA-256 are frozen.
- The SonotaCo 2023/2025 literature benchmark is **not** used to choose any expansion threshold, metric, weight, or variant.

## One-shot rule

There is exactly one candidate membership rule in this experiment:

`other-year frozen seed support + exact v8 metric + exact radius 1.5 + nearest-family exclusive assignment`.

No radius grid, support-count gate, quantile, covariance model, medoid, orbital threshold, iterative growth, density threshold, label-dependent calibration, or benchmark-driven variant is tested.

## Required structural reproduction

Before expansion, the run must reproduce the promoted-v8 development invariants:

- 226 recurrent families;
- 95 qualified known showers;
- multiplicity recovery@100 = 58;
- persistence recovery@100 = 59;
- Brown recovery@100 = 55;
- v3 recovery@100 = 55;
- multiplicity top-100 dominant precision = 0.6884631112636006;
- multiplicity MRR = 0.045531138942766655;
- exact 128-event scoring episodes and Brown equivalence;
- target exclusion and zero label-dependent proposal calibration.

Expansion must leave every family ID, component ID, seed event set, centroid, score, and ranking position unchanged.

## Evaluation

After expanded memberships are hash-frozen, known-shower labels are opened only for evaluation.

Report:

- original and expanded global family matching under the unchanged v8 multiplicity order;
- original and expanded annual best-family precision/recall/F1 in each year;
- annual mean F1 by shower-size bins `4–9`, `10–24`, `25–49`, `50–99`, `100+`, and all eligible showers;
- membership growth, overlap conflicts, and dominant-label precision burden.

## Promotion gates

Promote this membership layer only if all integrity gates pass and all of the following hold:

1. expanded multiplicity recovery@100 >= 58;
2. expanded qualified known-shower matches >= 95;
3. expanded top-100 dominant precision >= 0.65;
4. expanded global macro F1 >= promoted-v8 macro F1 + 0.05;
5. annual all-shower mean F1 improves by at least 0.10 in **both** 2022 and 2023;
6. annual 4–9-member mean F1 does not decline by more than 0.02 in either year;
7. at least one of the `10–24`, `25–49`, `50–99`, or `100+` bins improves by at least 0.10 in both years wherever that bin has eligible showers.

The +0.10 criterion is inherited as the existing literature-comparison definition of a material mean-F1 difference; it is not selected from this result.

## Decision rule

A pass creates a separately named candidate architecture for later independent validation. It does **not** modify the frozen v8 blind protocol, does not authorize OrbitTrace Stage A/B, and does not retroactively claim literature superiority.

A failure is preserved as a no-go for this exact expansion rule. The result may motivate a separately justified architecture only through source/geometry diagnosis, not threshold retuning on the same labels.
