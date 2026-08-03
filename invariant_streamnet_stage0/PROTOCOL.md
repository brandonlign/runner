# InvariantStreamNet Stage-0 protocol

**Frozen before authoritative real-data execution: 2026-08-03.**

## Question

Can a physics-informed permutation-equivariant neural detector learn sparse meteor-stream geometry from several real survey backgrounds, transfer to a completely unseen meteor network and unseen stream morphology, and outperform a strong handcrafted matched-track baseline at the same operating false-positive rate?

This is a kill test. It is separate from GhostStream and must not be applied to GhostStream unless every continuation gate passes.

## Data split

- Training backgrounds: CAMS, EDMOND, and SonotaCo shower-removed subsets released with Shober (2026).
- Held-out network: GMN. No labeled GMN patches are used for model training or baseline training.
- Unlabeled GMN background patches are used only to set each detector's operating threshold.
- The real M2026-A1 / 87 Virginids concentration is conservatively masked from all training and calibration backgrounds and retained only as a final real transfer check.
- Exact source-file MD5 values are verified before use.

## Tasks

The model receives an unordered set of 48 nearby meteors represented by local solar longitude, radiant right ascension, radiant declination, and geocentric speed.

It jointly predicts:

1. whether the event set contains a stream; and
2. which individual meteors belong to that stream.

The architecture uses self-attention without positional indices, a global set token, and an event-level segmentation head. Event-order permutation must not change the prediction except for the corresponding permutation of membership outputs.

## Training and transfer tests

Synthetic stream members are injected into real CAMS, EDMOND, and SonotaCo background patches.

- Training morphology: linear radiant/velocity drift with symmetric or uniform activity.
- Held-out same-morphology test: GMN background with the training morphology.
- Held-out unseen-morphology test: GMN background with skewed activity, nonlinear radiant drift, and broader dispersion.
- Real transfer test: the published ESV concentration in the untouched GMN data.

Synthetic stream strengths are 6, 8, 12, and 16 members in a 48-event patch.

## Baseline

The baseline is a HistGradientBoosting classifier trained on handcrafted features that include:

- the best score from a bank of linear radiant/velocity tracks;
- local-neighbor density;
- covariance linearity;
- compactness; and
- multidimensional histogram occupancy.

This baseline is intentionally strong and closely matched to conventional density/track-search reasoning. The neural detector must beat it; beating a weak generic classifier is not sufficient.

## Calibration

- Global neural probabilities are Platt-calibrated on held-out training-network validation data.
- Event-membership threshold is selected on the same validation split by maximum membership F1.
- Each detector's global operating threshold is independently set from unlabeled held-out GMN background at nominal 1% false-positive rate.

## Frozen continuation gates

All gates must pass on the held-out unseen-morphology GMN test and real ESV check:

1. Neural false-positive rate is at most 0.03.
2. Neural true-positive-rate gain over the engineered baseline is at least 0.10.
3. Neural true-positive rate is at least 0.50.
4. Event-membership F1 is at least 0.60.
5. Expected calibration error is at most 0.10.
6. The real ESV patch score exceeds the 99th percentile of held-out GMN background scores.
7. Real ESV event-membership F1 is at least 0.50 under the conservative published-region mask.

Failure of any gate gives `KILL_OR_REDESIGN_INVARIANT_STREAMNET`. Passing every gate permits a larger shower-family-disjoint benchmark and a full catalog-scan false-discovery evaluation; it does not establish novelty or justify applying the detector to GhostStream.
