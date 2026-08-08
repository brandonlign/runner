# OrbitTrace cross-year two-witness expansion v2 — frozen development protocol

## Purpose

The frozen v1 cross-year seed-support expansion established a specific architectural failure rather than a failure of the underlying v8 seeds. Using one other-year seed event as sufficient membership support materially improved annual shower F1, especially for moderate and large showers, but opened a union of single-seed radius-1.5 balls that admitted 174,594 new events and regressed qualified matches, recovery@100, and top-100 precision.

v2 tests exactly one successor implied by that mechanism: retain the exact v8 seed families and exact v1 cross-year expansion geometry, but require **two distinct original seed events from the other year** to support every newly assigned event. The count two is not selected from a performance grid; it inherits the existing v8/fixed4 minimum repeated-support principle `MIN_ANCHOR_COUNT = 2` and prevents one isolated seed event from opening a full membership ball.

## Frozen base

- Base commit: promoted v8 `c9d6c44704013ba0c9430100e98a29a56b453304`.
- Reproduce exactly 226 v8 recurrent families, pooled-year centroids, 128-event scores, multiplicity order, and all v8 pre-expansion metrics before membership expansion.
- The v8 proposal generator, components, connected family graph, radius 1.5, centroids, multiplicity score, and ranking are immutable.
- v1 is preserved as a no-go and is used only as exact source plumbing for the already-frozen expansion implementation; its result is not retuned.

## Frozen v2 membership rule

For each target year independently:

1. use only each family's **original v8 seed events from the other year** as support;
2. a non-seed target-year event is eligible for that family only when at least **two distinct other-year original seed events** have exact inherited v8 distance `<= 1.5` to it;
3. the necessary-only solar-longitude prefilter remains exactly `4 × 1.5 = 6°` around the support arc and cannot accept an event by itself;
4. if an event is eligible for more than one family, assign it exclusively to the family with the smallest exact distance to its nearest supporting seed; ties use stable family ID;
5. newly assigned events never become support for any later assignment;
6. original v8 seed membership is never removed.

No source shower label, orbital element, v3/Brown score, family rank, known-shower identity, or benchmark result is used to choose membership.

## Prohibited alternatives

This experiment contains exactly one scientific candidate. Do not test:

- one, three, four, or any searched witness count;
- any radius other than inherited 1.5;
- family-specific or density-adaptive radii;
- recursive region growing;
- same-year support;
- centroid-only, medoid, orbital, D_SH, score-weighted, or label-weighted membership;
- second-best margins, probability thresholds, support fractions, or post-hoc pruning;
- reranking after expansion.

Failure is a no-go for this exact two-witness successor and does not authorize changing the witness count from its result.

## Development panel and blindness

- Exact GMN 2022 + 2023 target-excluded development corpus inherited from v8.
- Solar longitude 20°–55° is removed before labels/proposals/scoring/evaluation by the frozen parser.
- All v8 families/ranks and all v2 expanded memberships are frozen and SHA-256 recorded before shower labels are evaluated.
- No OrbitTrace coordinate, identity, member, target-region event, Stage A/B output, or target reveal may be accessed.
- The already-seen SonotaCo literature benchmark is not used to choose a v2 parameter; v2 addresses only the v1 single-witness overexpansion mechanism.

## Scientific gates

Use the exact v1 promotion standard without relaxation:

1. multiplicity recovery@100 after expansion `>= 58`;
2. qualified matches after expansion `>= 95`;
3. top-100 dominant precision after expansion `>= 0.65`;
4. expanded macro F1 `>= v8 macro F1 + 0.05`;
5. all-shower annual mean-F1 gain `>= +0.10` in both 2022 and 2023;
6. 4–9 annual mean-F1 delta `>= -0.02` in both years;
7. at least one of 10–24, 25–49, 50–99, or 100+ has mean-F1 gain `>= +0.10` in both years.

Every v8 reproduction, blindness, exact-128-episode, Brown-equivalence, fixed-radius, no-recursion, exclusive-assignment, pre-label-hash, and two-other-year-witness integrity gate must also pass.

## Decision rule

Promote v2 only if every integrity and scientific gate passes in this one frozen execution. Otherwise preserve it as a no-go. A pass would justify a separately frozen prospective validation and later matched literature comparison; it would not authorize OrbitTrace reveal by itself.
