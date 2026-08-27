# Cycle-consistent partial transport: frozen screening gate

Status: candidate methodology. GhostStream is excluded from the data pool by a deliberately broad solar-longitude/radiant/speed mask and is not used for design, parameter selection, or evaluation.

## Motivation and prior failure boundary

ReplicaStream combined annual template p-values and failed under shared annual structure. It did not establish event-level correspondences across years. This screening tests a distinct object: partial one-to-one cross-year correspondences among individual meteor events.

The candidate is only a cheap screening surrogate. A pass could authorize a true unbalanced multi-marginal optimal-transport benchmark. A failure kills this transport direction before expensive implementation.

## Frozen source data

- exact real-shower audit artifact `8871850235`;
- artifact ZIP SHA-256 `5f2501b3eee19b51a5dc81f8493dce67a810ef5c480045dac143de060369534d`;
- exact complex-disjoint fold artifact `8871912750`;
- artifact ZIP SHA-256 `d5f7f50262b2cd2f64901db913cd2babb0fccb897391d46b2af25f0f6d4723c4`;
- GMN years 2019, 2021, 2023, and 2025;
- deterministic panel of eight eligible showers from each of the five complete holdout folds, chosen only by a fixed hash of IAU number.

The 40-shower panel can kill the formulation but cannot validate it.

## Frozen scenes

- 64 events per year for four years;
- positive scenes contain `k in {4,6,8}` real shower members in exactly three years and real local IAU `-1` backgrounds;
- negative scenes contain only real local backgrounds;
- one-year artifacts contain the same total `3k` real shower members in one year and none in the other years;
- one deterministic replicate per shower and member count;
- fixed ±10° solar-longitude windows;
- coordinates: relative solar longitude, Sun-centered ecliptic radiant, and geocentric speed with fixed physical scales.

## Candidate

For every year pair and radius, greedily construct a partial one-to-one minimum-distance matching. Join pairwise matches into connected cross-year components. A component contributes only if it spans at least three years; it is penalized when it contains multiple events from the same year. The score sums the twelve strongest cycle-consistent components.

Candidate radii are frozen before execution and selected only on the validation fold.

## Baselines

1. pooled local density;
2. third-strongest annual local density (`annual_confirmation`);
3. simple cross-year nearest-neighbor support without one-to-one cycle consistency.

Every radius is selected on the next validation fold and evaluated on the complete held-out fold.

## Frozen continuation gates

All must pass:

1. candidate mean weak-scene AUROC at least `0.90`;
2. candidate mean AUROC no more than `0.03` below simple cross-year support;
3. candidate one-year-artifact detection rate at most `0.10`, using a threshold frozen at the validation-negative 90th percentile;
4. artifact detection improves over simple cross-year support by at least `0.05`;
5. at least four of five folds show no material AUROC collapse relative to simple cross-year support.

Failure gives `KILL_CYCLE_CONSISTENT_PARTIAL_TRANSPORT`. Do not tune radii, component weights, panel membership, scene size, or active-year count afterward. Do not implement full unbalanced transport or apply the score to GhostStream after a failure.
