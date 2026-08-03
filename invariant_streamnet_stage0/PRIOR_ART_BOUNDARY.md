# InvariantStreamNet prior-art and novelty boundary

## Established ingredients

None of the following is individually novel:

- DBSCAN, HDBSCAN, wavelet, or orbital-distance meteor-stream searches;
- neural networks, self-attention, Deep Sets, or event segmentation;
- synthetic signal injection into real background data;
- transfer evaluation on a held-out survey;
- Platt calibration;
- matched-track and local-density features.

Meteor science already uses machine learning for classification tasks, and uncertainty-aware clustering has been used for shower searches. General set neural networks and attention-based point-cloud segmentation also predate this project.

## Narrow hypothesis under test

The potential domain contribution is an end-to-end meteor-stream detector that jointly:

1. consumes an unordered local set of meteor trajectories;
2. learns relational radiant, activity, and speed structure through permutation-equivariant self-attention;
3. predicts both candidate presence and event membership;
4. is trained on physically generated stream morphologies embedded into several real survey backgrounds;
5. transfers to a completely unseen meteor network and an unseen curved/skewed morphology; and
6. is benchmarked against a strong handcrafted matched-track detector at a separately calibrated held-out-network operating point.

This is methodologically meaningful only if the learned representation materially beats the engineered baseline and succeeds on the untouched real ESV stream.

## Claims prohibited at Stage 0

Do not claim that:

- neural meteor classification is new;
- attention or permutation invariance is new;
- synthetic injection is new;
- this is the first neural meteor-stream detector;
- the detector can perform a blind catalog search;
- the detector outperforms clustering, wavelets, or orbital-distance searches;
- the detector has been validated on GhostStream.

No priority claim is permitted without a literature-complete review.

## Kill boundary

The current formulation is rejected if it fails any frozen gate, especially if:

- it does not beat the handcrafted baseline by at least 0.10 TPR on unseen morphology;
- membership segmentation does not transfer;
- calibration fails on the unseen network; or
- the real ESV stream is not detected and segmented.

A Stage-0 pass would only permit a larger shower-family-disjoint test, ablation studies, comparisons with HDBSCAN/DBSCAN/wavelets, full-sky scan calibration, and additional real weak streams.
