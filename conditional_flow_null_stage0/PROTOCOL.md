# Cross-fitted conditional-flow sporadic null: frozen screening

Status: candidate methodology. This is a cheap two-extreme-year kill screen, not a validation benchmark. GhostStream is excluded from all design and is not evaluated.

## Methodological question

Can a conditional normalizing-flow model of the shower-removed sporadic background calibrate the maximum of a complete multiscale local-density search on held-out real background better than an established local KDE-style resampling null?

The potential contribution is not “use a normalizing flow.” It is cross-fitted calibration of the complete adaptive search under a flexible conditional background model. A failure of held-out calibration kills this formulation even if injection power improves.

## Frozen source data

- exact real-shower audit artifact `8871850235`;
- artifact ZIP SHA-256 `5f2501b3eee19b51a5dc81f8493dce67a810ef5c480045dac143de060369534d`;
- shower-removed IAU `-1` events from 2019, 2021, 2023, and 2025;
- labeled real showers are used only for the post-calibration injection panel.

## Cross-fitting

- evaluation years: 2019 and 2025, selected before execution as the earliest and latest available years;
- each evaluation model trains only on the other three years;
- at most 80,000 deterministic training events per fold;
- no held-out background event enters training or model selection.

## Conditional flow

- target variables: Sun-centered ecliptic longitude, ecliptic latitude, and geocentric speed;
- condition: sine and cosine of solar longitude;
- six alternating affine coupling layers, hidden width 64;
- AdamW, learning rate `8e-4`, weight decay `1e-5`;
- three epochs, batch size 2,048;
- architecture and optimization are fixed before execution.

## KDE comparator

For each target solar longitude, sample a training event from the ±6° neighborhood with a Gaussian solar-longitude kernel of width 3°, then apply fixed joint-feature jitter of 1.5° in Sun-centered longitude, 1.2° in latitude, and 0.7 km/s in speed.

## Held-out null scenes

- 12 fixed centers at 30° spacing;
- ±6° windows;
- 128 real held-out IAU `-1` meteors per scene;
- preserve every scene’s observed solar-longitude values exactly when generating synthetic catalogs;
- 12 synthetic catalogs per model and scene;
- adaptive statistic: maximum local neighbor count over radii `{0.8,1.0,1.2,1.5,1.8}` in fixed scaled solar-longitude/radiant/speed coordinates;
- empirical p-value uses the complete synthetic maximum distribution.

## Injection panel

- four deterministic labeled showers per evaluation year;
- real member counts `k in {4,6,8}` plus real held-out local background;
- threshold is the synthetic 90th percentile generated for the exact scene solar-longitude values;
- primary weak power uses k=4 and k=6.

## Frozen continuation gates

All must pass:

1. flow nominal-10% held-out false-positive rate ≤ `0.20`;
2. flow mean low-tail calibration error improves over KDE by at least `0.02`;
3. flow nominal-10% error improves over KDE by at least `0.03`;
4. weak-injection power is no more than `0.10` below KDE;
5. flow calibration error is lower in both evaluation years.

Failure gives `KILL_CONDITIONAL_FLOW_NULL_SURROGATE`. Do not train longer, widen the network, change the conditioner, alter KDE bandwidths, add year labels, or run GhostStream.

Passing would authorize only a full four-year runner benchmark with more windows and synthetic catalogs. It would not establish the method.
