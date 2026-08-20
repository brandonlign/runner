# M2D SACV recurrence-pair extraction v2

## Motivation

RC-v1 established on target-excluded GMN that recurrence-before-selection improves paired F1 on both literature routes but whole recurrence-component union loses precision because validated local hypotheses can percolate within a broad M2D parent. RC-v1 is closed and is not retuned here.

v2 returns to the minimal causal repair of SACV-v1: preserve all admissible annual local hypotheses until recurrence is evaluated, then select exactly one validated 2022/2023 hypothesis pair rather than one annual winner or one connected component.

The architectural motivation originated after the revealed #1406/#1407 target failure, so v2 is post-reveal development. OrbitTrace target data remain forbidden from this GMN run.

## Unchanged SACV machinery

Exact passed SACV-v1 constants and geometry are inherited unchanged: target-excluded GMN 2022/2023 universe; immutable M2D parent ranks/memberships; 5 degree solar, 4 degree radiant, 10% speed physical scaling; radius <=1.0; support >=4; contamination <=0.10; seasonal analog offsets 60..300 degrees by 10; widest admissible observed radius per center; exact reciprocal cross-year validation; exact-parent fallback if no validated recurrence pair exists.

## Pair selection

Enumerate every annual center having an admissible SACV-v1 radius. For every 2022 x 2023 pair, retain it only if the exact SACV reciprocal validation passes: center distance is within both radii and each hypothesis ball contains at least four opposite-year parent members.

Select exactly one validated pair by the frozen lexicographic recurrence score:

1. maximize `min(ab, ba)` — bottleneck opposite-year support;
2. minimize center distance `d` — strongest geometric recurrence;
3. maximize `min(excess_2022, excess_2023)` — weakest-year local excess;
4. minimize union membership size;
5. stable center-ID pair tie break.

Output membership is exactly the union of the two selected SACV balls, restricted to the immutable M2D parent. No component union, halo growth, recursion, deduplication against other parents, reranking, threshold search, score blending, or target-aware choice is allowed.

## Firewall

All annual hypotheses, validated pairs, chosen pair, and output IDs freeze before GMN shower truth opens. Protected solar longitude [20,55] remains excluded. OrbitTrace target IDs/coordinates/events/membership/rank and SonotaCo truth are inaccessible.

## Binding gates

The exact #1405 same-parent paired evaluator is reused. Both Sugar2017 and HDBSCAN2025 must pass every original SACV gate. Relative to immutable SACV-v1, each route must have mean paired precision >= SACV-v1 and mean paired F1 >=95% of SACV-v1; at least one route must strictly improve precision or F1.

PASS: `PASS_M2D_SACV_PAIR_V2_GMN_DEVELOPMENT`. FAIL closes this exact pair score/rule without rescue.
