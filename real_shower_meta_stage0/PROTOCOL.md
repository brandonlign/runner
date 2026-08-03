# Complex-held-out real-shower meta-learning: frozen Stage-0

Status: candidate methodology. GhostStream is excluded from all data, training, tuning, thresholds, architecture choices, and continuation decisions.

## Scientific gap

Meteor shower searches usually use fixed similarity rules, clustering, or manually specified radiant/velocity tracks. Neural meteor work primarily classifies video detections or physical meteoroid types. The candidate contribution is not attention, Deep Sets, episodic learning, or noisy-label training by themselves.

The narrow contribution under test is whether episodic learning from **real established shower member sets embedded in real local sporadic backgrounds** transfers to entirely unseen shower complexes and weak real streams better than the association rule that generated the teacher labels.

## Fundamental label limitation

GMN shower labels are noisy teacher labels produced by an existing association system. They are not independent discovery truth. A model fails methodologically if it merely learns:

- absolute solar-longitude windows;
- shower identity;
- the existing lookup-table association radius;
- only high-member strong-shower morphology.

## Fixed source data

Use official GMN monthly trajectory summaries for all 12 months in 2019, 2021, 2023, and 2025.

Use the IAU Meteor Data Center `streamfulldata.json` release obtained during execution to define related-shower holdout complexes from its `Group` and `Parent body` fields. Record the version and file hash.

Quality-screened event fields:

- solar longitude;
- geocentric right ascension and declination;
- geocentric speed;
- their reported uncertainties;
- orbit and basic fit-quality diagnostics for audit only.

Primary model inputs may not contain shower code, IAU number, calendar year, absolute UTC, or absolute solar longitude.

## Data gate

The candidate advances to model training only if all hold:

1. at least 30 showers have at least 200 quality events across at least three frozen years, with at least 20 events in each of three years;
2. at least 12 showers have at least 1,000 quality events and representation in all four years;
3. at least 20 related-complex holdout units contain an eligible shower;
4. at least six holdout units contain two or more eligible showers;
5. at least 200,000 quality sporadic events exist across the frozen year-month strata;
6. at least 95% of sampled labeled and sporadic events have complete geocentric coordinates and finite reported uncertainties.

Solar-longitude leakage is measured but is not a data-gate failure. It becomes a mandatory baseline and ablation.

## Frozen episode construction

Each episode contains 128 events from one year and a solar-longitude window centered on a real shower member.

Positive episodes:

- choose one eligible shower;
- choose a year with at least 20 members;
- draw `k` real members, where `k` is uniformly selected from `4, 6, 8, 12`;
- draw the remaining events from IAU `-1` meteors in the same year and within a fixed ±10 degree solar-longitude window;
- express solar longitude relative to the episode center;
- convert radiant to Sun-centered ecliptic coordinates;
- robustly standardize speed and angular coordinates using training-complex data only.

Negative episodes use 128 real sporadic events from one year and the same window construction.

No synthetic stream members are permitted in the primary training or primary evaluation.

## Fixed holdouts

Hold out entire MDC complex/parent units. Every IAU shower code belonging to a held-out unit is absent from training, validation, architecture decisions, and threshold selection.

Use five deterministic complex-disjoint folds. Complex assignment is frozen from a hash of the complex key, with balancing performed only by a fixed greedy event-count rule before any model result exists.

A shower lacking an MDC group or parent is its own holdout unit.

## Candidate model

A small permutation-equivariant set model:

- event encoder: two hidden layers, width 64, GELU;
- global context: mean and max pooling;
- event membership head using local plus global features;
- episode-presence head using pooled features;
- no positional embeddings, shower identifiers, or absolute solar longitude;
- fixed architecture and optimizer across all folds.

The model is trained jointly on event membership and episode presence. Class weighting is fixed from the training episode generator, not tuned per fold.

## Frozen baselines

1. solar-longitude-only episode classifier;
2. labeler-proxy track score using the known training-shower radiant/velocity drift templates but no held-out shower identity;
3. fixed local-density score in relative solar longitude, Sun-centered radiant, and speed;
4. HDBSCAN or DBSCAN episode clustering with thresholds calibrated on training complexes;
5. a non-episodic event classifier with the same event encoder capacity;
6. candidate model with relative solar longitude removed.

## Evaluation

Primary endpoint: episode-presence AUROC averaged across five complex-held-out folds on weak positive episodes with `k = 4, 6, 8`.

Secondary endpoints:

- event-membership F1 at a threshold frozen on validation complexes;
- catalog-level false-positive rate on negative real-sporadic episodes;
- performance by member count and shower strength;
- calibration error;
- solar-longitude ablation;
- labeler-proxy agreement and disagreement analysis.

External transfer gate: without retraining, score an untouched real weak-stream control not used in GMN teacher labels, preferably M2026-A1/ESV or an equivalent independently defined removed/weak stream. This external control cannot select the model or threshold.

## Frozen continuation gates

All must pass:

1. mean weak-episode AUROC at least `0.80`;
2. AUROC gain at least `0.10` over every baseline, including the labeler proxy;
3. mean membership F1 at least `0.55` for `k = 6` and `k = 8` episodes;
4. negative-episode false-positive rate at most `0.10`, with upper 95% bootstrap bound at most `0.15`;
5. expected calibration error at most `0.10`;
6. removing relative solar longitude reduces AUROC by no more than `0.10`;
7. no fold contributes more than half the aggregate AUROC gain;
8. at least four of five folds individually improve over the best baseline;
9. the untouched real weak-stream control scores above the 99th percentile of matched negative controls and obtains membership F1 at least `0.40` when an independent membership mask exists.

## Kill rules

Kill the formulation if any gate fails. Do not rescue it by:

- random event splits within the same shower;
- dropping difficult shower complexes;
- adding absolute solar longitude or shower identifiers;
- selecting the best architecture after seeing held-out complexes;
- training on synthetic streams after the primary real-shower model fails;
- applying it to GhostStream before all gates pass.

A pass authorizes a broader independent-network benchmark. It does not by itself prove a first-ever method or authorize a GhostStream discovery claim.
