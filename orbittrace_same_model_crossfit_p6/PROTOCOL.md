# OrbitTrace P6 same-model cross-fit membership protocol

## Status

Source/protocol-only successor after authoritative P5 no-go. No P6 truth evaluation, literature comparison, external validation, target-region event, or OrbitTrace target information is accessed by this freeze.

## Structural diagnosis fixed before P6 truth

P3-P5 set each family-direction `seed_floor` with the deterministic family-excluded cross-fit model for that direction, but then score candidate events with the separate final all-family P2 model. Those probability scales are not guaranteed to be interchangeable.

This is not a truth-derived hypothesis. An artifact-only audit of the frozen P5 pretruth payload (`p3_crossfit_pretruth.json`) showed that among the 439 P3-reliable directions, at least 41 directions contain a Pareto-frontier held-out recurrent-seed vector whose probability under the final all-family model is below the seed floor defined by its own held-out-fold model. Across the 742 reliable-direction frontier vectors, 43 have this contradiction. The diagnostic uses no known-shower label values and does not identify any target event or catalogue shower.

## Sole P6 change

For each family-direction:

1. retain the exact deterministic five-fold family split from P3;
2. retain the exact held-out-fold model, held-out recurrent-seed `seed_floor`, local negative-tail test, and reliable/unreliable decision;
3. retain the exact P4 coordinate-wise held-out-seed envelope;
4. retain the exact P5 joint support by one actual held-out recurrent-seed vector;
5. **score that direction's candidate rows with the same held-out-fold scaler/logistic model that scored its held-out recurrent seeds and set its `seed_floor`;**
6. use those same-model candidate probabilities for the unchanged odds/responsibility calculation.

The final all-family P2 model may still be fit/frozen for lineage identity and diagnostics, but it cannot determine P6 proposal inclusion or proposal odds.

## What does not change

- exact promoted-v8 226 recurrent families, order, seeds, and multiplicity ranking;
- exact P2 `[d_obs, D_SH]` two-view representation, OAS construction, local +/-5 degree negatives, minimum 128 negatives, weighting, StandardScaler, L2 logistic `C=1.0`, solver/settings;
- exact P3 five-fold hash split, `seed_floor > 0.5`, local negative tail <=0.10, and >=4 target-year seeds;
- exact P4 coordinate envelope;
- exact P5 joint held-out-seed support frontier;
- exact unit-background conflict model and strict responsibility >0.5;
- no recursive growth, no refit from new members, no reranking;
- no threshold, quantile, multiplier, offset, family-specific tuning, parameter sweep, or known-shower-guided selection.

## Frozen development gates

P6 must satisfy every existing integrity/firewall gate plus all substantive gates unchanged:

- exact v8 baseline reproduced;
- exact 226 v8 families/order and every v8 seed preserved;
- qualified known-shower matches >=95;
- recovery@100 >=58;
- top-100 dominant precision >=0.65;
- macro F1 >=0.2536657194465356;
- large-shower mean recall >=1.5x v8;
- large-shower mean precision >=0.85;
- expansion nonvacuous;
- all cross-fit/model/decision/membership payloads frozen before any known-shower label value is read;
- every surviving proposal must record the same fold that defines its reliability gate.

There is exactly one primary P6 configuration. A genuine P6 FAIL rejects this exact configuration. Later parallel branches are not eligible as outcome-selected second chances.
