# M2D SACV fallback-rescue v3

## Motivation

SACV-v1 passed the generic GMN benchmark but missed OrbitTrace because its independently selected annual winners failed reciprocal recurrence and therefore triggered exact-parent fallback. RC-v1 showed whole recurrent components are too broad; pair-v2 showed replacing successful SACV selections with recurrence-pair selections sacrifices some generic F1/precision.

v3 makes the narrowest conservative architectural change consistent with those target-excluded results: **successful SACV-v1 outputs are immutable; recurrence-pair selection is invoked only when exact SACV-v1 would fall back to the parent.**

This exact architecture is post-reveal development. OrbitTrace target information is prohibited from GMN development.

## Exact parent behavior

For every immutable M2D parent, first execute exact SACV-v1 annual `select_source` semantics and exact reciprocal validation. If SACV-v1 validates, output its exact two-ball membership byte-for-byte. No recurrence-pair search may override, rerank, shrink, enlarge, or replace a successful SACV-v1 result.

If SACV-v1 does not validate and would output the exact M2D parent, enumerate every annual SACV-admissible center using the unchanged per-center widest admissible radius. Form every cross-year pair passing the exact SACV reciprocal gate. If no pair validates, retain the exact parent fallback.

If one or more fallback-rescue pairs validate, select exactly one by the frozen pair-v2 recurrence score:
1. maximize `min(ab,ba)`;
2. minimize center distance `d`;
3. maximize `min(excess_2022,excess_2023)`;
4. minimize the two-ball union size;
5. lexicographically smallest center-ID pair.

The rescue membership is exactly the union of those two SACV balls restricted to the immutable parent.

## Unchanged constants

Exact SACV-v1 target-excluded GMN universe, M2D parents/ranks, 5 degree solar / 4 degree radiant / 10% speed geometry, radius <=1.0, support >=4, contamination <=0.10, seasonal analog offsets 60..300 by 10 degrees, observed-radius construction, reciprocal validation, and parent fallback remain unchanged.

No score threshold, annual-rank cutoff, component union, halo growth, recursion, reranking, parent switching, pair-score blend, route exception, or post-result rescue is allowed.

## Pretruth gates

Before GMN shower truth opens:
- every parent where exact SACV-v1 validates must reproduce its exact output IDs;
- rescue can occur only on an exact SACV-v1 fallback;
- all memberships/ranks freeze;
- protected [20,55] remains excluded;
- OrbitTrace and SonotaCo truth remain inaccessible.

## Binding scientific gates

Reuse exact #1405 paired same-discovery evaluation. Both Sugar2017 and HDBSCAN2025 must pass every original SACV-v1 gate. Relative to the immutable passed SACV-v1 endpoint, each route must have paired precision >= SACV-v1 and paired F1 >= SACV-v1 (not merely 95% retention), and at least one route must strictly improve precision or F1. At least one fallback parent must be rescued.

PASS: `PASS_M2D_SACV_FALLBACK_V3_GMN_DEVELOPMENT`.

FAIL permanently closes this exact fallback-rescue rule; do not weaken the non-regression gate or alter the rescue score after outcome.
