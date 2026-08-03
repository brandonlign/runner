# Hard-negative relation-clique detector: frozen Stage-1

Status: candidate methodology. GhostStream is excluded from training, validation, architecture choices, thresholds, continuation decisions, and all internal evaluation.

## Why this redesign exists

The complex-held-out set model localized some real shower members but failed the episode-level discovery decision. The frozen local-density baseline remained substantially stronger. This Stage-1 candidate tests one narrow hypothesis: a relation kernel learned from real same-shower pairs and deliberately hard local negatives can add transferable physical-coherence information beyond fixed isotropic density.

This is not a generic neural-network retry. It removes the failed global set representation and learns only pairwise relative geometry. The final episode classifier is forced to include the exact frozen local-density baseline so the scientific question is incremental value, not whether a learned model can rediscover density.

## Frozen inputs and splits

- exact real-shower data-audit artifact `8871850235`;
- exact baseline-ceiling artifact `8871912750`;
- the same five complete MDC complex/parent holdout folds as the baseline audit;
- the same 128-event episodes, weak member counts, negative episodes, and broad M2026-A1/ESV exclusion mask;
- no random event split within a shower or related complex.

## Pair relation model

For each fold, the model sees only training-complex events. It is a fixed histogram-gradient-boosting classifier trained on relative pair features:

- signed and absolute solar-longitude separation;
- signed and absolute Sun-centered ecliptic longitude separation, with the longitude metric corrected by mean latitude;
- signed and absolute ecliptic-latitude separation;
- signed and absolute geocentric-speed separation;
- generic drift slopes relative to solar-longitude separation;
- the corresponding isotropic distance and largest standardized component.

No absolute solar longitude, radiant location, speed level, shower code, parent body, complex key, year identity, UTC, or GhostStream information enters the relation model.

The fixed training set contains:

- 18,000 same-shower, same-year positive pairs;
- 6,000 locally hard shower-sporadic negatives;
- 6,000 locally hard sporadic-sporadic negatives;
- 6,000 locally hard cross-shower negatives from different holdout complexes.

Hard partners are chosen from a deterministic local candidate pool and one of the five closest candidates is sampled with a frozen seed. This prevents the relation model from succeeding only on trivial far-apart negatives.

## Episode relation-clique scan

The trained relation model scores every event pair in an episode. For subset sizes `4`, `6`, and `8`:

1. rank anchors by their mean relation to their strongest `k-1` neighbors;
2. inspect the top 16 anchors;
3. form each anchor's deterministic `k`-event candidate;
4. score the candidate as `0.70 × pair-score 25th percentile + 0.30 × pair-score mean`;
5. retain the best candidate for that size.

Membership support is calculated only from coherence with the winning candidate subsets. Generic high-degree stars do not become member predictions.

## Frozen hybrid episode score

A logistic calibrator is fit only on the next validation fold. Its six fixed inputs are:

- relation-clique scores for `k=4`, `k=6`, and `k=8`;
- their maximum and mean;
- the exact frozen local-density score at the radius already selected by the baseline audit.

This is the candidate under test. The relation-only score is not substituted post hoc, and the density radius is not reselected.

## Evaluation

Primary endpoint: mean weak-episode AUROC across five unseen-complex test folds, using positives with `k in {4,6,8}` and all matched negative episodes.

Secondary endpoints:

- membership F1 on `k=6` and `k=8` positives, with threshold selected only on the validation fold;
- negative-episode false-positive rate at the validation-fold 90th-percentile threshold;
- bootstrap upper 95% bound for that false-positive rate;
- expected calibration error;
- fold-level gains over every frozen baseline.

The untouched M2026-A1/ESV control is evaluated only if every internal gate passes. It cannot rescue an internal failure or select any model, threshold, feature, or architecture.

## Frozen continuation gates

All must pass:

1. mean weak-episode AUROC at least `0.80`;
2. mean AUROC gain at least `0.10` over every frozen baseline, including local density;
3. mean membership F1 at least `0.55` for `k=6` and `k=8`;
4. negative-episode false-positive rate at most `0.10`;
5. upper 95% bootstrap false-positive bound at most `0.15`;
6. expected calibration error at most `0.10`;
7. no fold contributes more than half of total positive AUROC gain;
8. at least four of five folds improve over the best frozen baseline;
9. untouched ESV median presence score exceeds the 99th percentile of matched negatives;
10. untouched ESV membership F1 is at least `0.40`.

## Kill rules

Kill the formulation if any gate fails. Do not rescue it by changing pair counts, hard-negative mix, candidate-pool size, tree depth, clique sizes, anchor count, score quantile, hybrid inputs, folds, thresholds, or external-control construction after the authoritative result.

Do not apply the candidate to GhostStream unless every gate passes. A pass would authorize independent-network confirmation, not a discovery claim by itself.
