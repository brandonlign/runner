# Partial-conjunction event support: frozen screening

Status: candidate methodology. This deterministic 40-shower complex-balanced panel can only kill the formulation; it cannot validate it. GhostStream is broadly masked from every sporadic pool and is not evaluated.

## Methodological question

Can event-level recurrence across distinct years reject one-year artifacts without the severe weak-stream power loss seen in cycle-consistent transport?

For every event, compute its nearest-event similarity to each of the other three years. The event receives the second-largest of those three similarities, so it contributes only when supported by at least two distinct other years. The scene statistic is the sum of the twelve strongest event scores.

This differs from annual template confirmation, simple summed cross-year support, and cycle-consistent one-to-one transport.

## Frozen data and panel

- exact real-shower audit artifact `8871850235`, ZIP SHA-256 `5f2501b3eee19b51a5dc81f8493dce67a810ef5c480045dac143de060369534d`;
- exact complex-fold artifact `8871912750`, ZIP SHA-256 `d5f7f50262b2cd2f64901db913cd2babb0fccb897391d46b2af25f0f6d4723c4`;
- eight deterministic eligible showers per fold;
- GMN years 2019, 2021, 2023, and 2025;
- 64 events per year and ±10° solar-longitude windows;
- positives contain k in `{4,6,8}` real members in exactly three years;
- one-year artifacts contain the same total `3k` real members in one year;
- negatives use only real local IAU `-1` background;
- broad GhostStream mask is fixed before execution.

## Baselines

1. third-strongest annual local-density score;
2. simple summed event-level cross-year support.

The radius for each method is selected only on the next validation fold. Detection thresholds are the validation-negative 95th percentiles.

## Frozen continuation gates

All must pass:

1. mean AUROC ≥ `0.90`;
2. mean k=4/6 detection ≥ `0.60`;
3. mean one-year-artifact detection ≤ `0.10`;
4. mean detection-minus-artifact utility exceeds annual confirmation by at least `0.10`;
5. mean utility exceeds simple summed support by at least `0.05`;
6. candidate has the best utility in at least four of five folds.

Failure gives `KILL_PARTIAL_CONJUNCTION_EVENT_SUPPORT`. Do not relax the distinct-year requirement, alter the top-event count, change the threshold quantile, tune radii, or apply the score to GhostStream.
