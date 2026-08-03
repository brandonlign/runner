# Complex-held-out real-shower set model: frozen Stage-0

Status: candidate methodology. GhostStream and the fixed M2026-A1/ESV region are excluded from all training, validation, internal testing, model selection, and threshold selection.

## Authorization

The source audits already passed:

- data artifact `8871850235`, ZIP SHA-256 `5f2501b3eee19b51a5dc81f8493dce67a810ef5c480045dac143de060369534d`;
- 190 eligible showers, 73 strong showers, 172 complete holdout units, 12 multi-shower units, and 1,151,700 quality sporadics;
- baseline artifact `8871912750`, ZIP SHA-256 `d5f7f50262b2cd2f64901db913cd2babb0fccb897391d46b2af25f0f6d4723c4`;
- best baseline: local density, mean weak-episode AUROC `0.7699613699`;
- a fixed `0.10` gain remains mathematically possible.

## Fixed splits

Use the exact five complex-disjoint folds preserved in `baseline_ceiling.json`. Fold `f` is test, fold `(f+1) mod 5` is validation, and the other three folds are training. No shower or related MDC group/parent unit crosses a split.

## Episodes

- 128 events from one year and a fixed ±10° solar-longitude window;
- positives contain `k in {4,6,8,12}` real members from one real shower-year plus real local IAU `-1` background;
- negatives contain only real local IAU `-1` meteors;
- primary weak endpoint uses `k in {4,6,8}`;
- all internal test episodes are deterministic, with two positive and two matched-negative replicates per held-out shower-year and member count;
- no synthetic stream members are allowed.

## Inputs and leakage controls

The network may use only:

- solar longitude relative to the episode center;
- Sun-centered ecliptic radiant;
- geocentric speed;
- reported radiant/speed uncertainties;
- fixed multiscale local-relation summaries computed inside each episode.

It may not use shower code, IAU number, complex key, calendar year, UTC, or absolute solar longitude. The M2026-A1/ESV mask is removed from every sporadic pool before training or internal evaluation.

## Fixed model

A permutation-equivariant set detector with:

- event encoder: two GELU layers, width 64;
- fixed local-relation radii `{1.0,1.5,2.0,2.5,3.0}` in predeclared scaled relative-solar-longitude, Sun-centered radiant, and speed coordinates;
- mean and max set pooling;
- joint episode-presence and event-membership heads;
- AdamW, learning rate `8e-4`, weight decay `1e-4`;
- 10 epochs, 1,536 generated training episodes per epoch, batch size 32;
- fixed joint loss and class weighting;
- best epoch selected only by validation-complex weak AUROC.

A complete second five-fold run zeros relative-solar-longitude inputs as the frozen leakage ablation.

## Thresholds and calibration

- scalar temperature is fit only on validation-complex episode logits;
- membership threshold maximizes validation positive-episode F1 over the fixed grid `0.05..0.95`;
- episode threshold is the 90th percentile of validation negative probabilities;
- no test-complex result may alter a model, threshold, feature, or hyperparameter.

## Frozen internal gates

All must pass:

1. mean weak-episode AUROC ≥ `0.80`;
2. mean AUROC gain over the best frozen baseline ≥ `0.10` (therefore AUROC ≥ `0.8699613699`);
3. mean membership F1 ≥ `0.55` separately for `k=6` and `k=8`;
4. mean negative-episode FPR ≤ `0.10`;
5. every fold's bootstrap upper 95% FPR bound ≤ `0.15`;
6. mean expected calibration error ≤ `0.10`;
7. removing relative solar longitude reduces mean AUROC by no more than `0.10`;
8. no fold supplies more than half of the total positive gain;
9. at least four of five folds beat their frozen local-density baseline.

If any internal gate fails, verdict is `KILL_COMPLEX_HELDOUT_SET_MODEL`. No external-control or GhostStream run is permitted.

If every internal gate passes, verdict is only `PROCEED_TO_UNTOUCHED_EXTERNAL_CONTROL`. The method is still not successful until the independently defined external weak-stream control passes the already frozen 99th-percentile and membership-mask gate.

## Prohibited rescue

Do not rescue a failure by changing the relation radii, episode size, member counts, architecture, loss, thresholds, fold assignment, solar-longitude window, baseline, or required gain. Do not add absolute solar longitude, shower identifiers, synthetic positives, or GhostStream data.
