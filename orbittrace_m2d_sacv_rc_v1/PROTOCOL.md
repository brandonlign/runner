# M2D SACV recurrence-component extraction v1

## Question

Can the already-passed SACV local hypothesis machinery solve the residual purity failure by moving selection *after* cross-year recurrence rather than selecting one annual maximum first?

This is a target-excluded GMN development successor. The revealed OrbitTrace postmortem in #1407 motivates the architectural question but no OrbitTrace ID, coordinate, event, rank, membership, or target score may enter construction or evaluation.

## Frozen parent and unchanged science

Parent is exact passed SACV v1 from #1405. The following are unchanged: target-excluded GMN 2022/2023 universe; M2D parent candidates/ranks/memberships; physical embedding (5 degree solar, 4 degree radiant, 10% speed); maximum radius 1.0; support floor 4; 10% contamination maximum; Moorhead-style seasonal analog offsets 60..300 degrees by 10 degrees; observed-radius candidate set; and SACV reciprocal cross-year validation.

For each annual parent slice, v1 formerly selected one globally strongest admissible center before recurrence. RC-v1 instead retains every center that has an admissible SACV radius. For each center, the radius remains exactly SACV-v1's widest admissible observed radius.

## Recurrence graph

For every 2022 hypothesis and every 2023 hypothesis, create a validated edge iff the exact SACV-v1 cross-year rule holds: center distance is within both annual radii and each ball contains at least four opposite-year parent members.

Take connected components of the validated bipartite hypothesis graph. Isolated annual hypotheses are ignored.

Each component membership is the union of the exact parent events lying in any annual SACV ball represented by that component. No event outside the immutable M2D parent may enter.

Exactly one component is selected per M2D parent by the frozen target-free lexicographic recurrence-support score:

1. maximum number of validated cross-year edges;
2. then maximum number of hypothesis nodes;
3. then maximum summed `min(ab, ba)` cross-year support over component edges;
4. then maximum summed `min(excess_2022, excess_2023)` over component edges;
5. then deterministic member-set SHA-256.

If no validated recurrence component exists, output the exact parent membership, matching SACV-v1's conservative fallback philosophy.

No component density threshold, radius/support search, annual-rank cutoff, edge threshold, target-aware tie break, pruning, recursion, reranking, parent switching, or post-result rescue is allowed in v1.

## Pretruth firewall

All hypothesis lists, edges, components, selected memberships, and hashes freeze before GMN shower truth opens. Protected solar longitude [20,55] remains excluded. SonotaCo and all OrbitTrace target information are inaccessible.

## Binding development gates

Use the exact #1405 same-parent paired evaluator. Both Sugar2017 and HDBSCAN2025 routes must still pass every original SACV gate: paired n >=20; nonempty fraction >=0.75; mean extraction precision >=0.80 and > parent; extraction F1 >=0.75x parent; nonempty precision nonregression >=0.50; at least one strict refinement.

Additionally, relative to the immutable passed SACV-v1 endpoint, each route must have precision >= SACV-v1 and F1 >=95% of SACV-v1, and at least one route must strictly improve either precision or F1.

PASS: `PASS_M2D_SACV_RC_V1_GMN_DEVELOPMENT`.

FAIL: `FAIL_M2D_SACV_RC_V1_GMN_DEVELOPMENT` and this exact component-selection formulation is closed.
