# OrbitTrace v29 purity-diversity GMN model freeze v1

## Selection provenance

v29 is a separately named successor selected only after the target-excluded GMN result of PR #971.

PR #971 itself remains a frozen scientific FAIL because its authorized promotion candidates were quality/purity rank-sum and rank-product fusions. However, #971 also preregistered and evaluated a required diagnostic `purity_diversity` order consisting of:

1. exact #840 strict-group HGB-31 purity probability;
2. no event-Jaccard suppression and no family deletion;
3. exact #839 geometric diversity, lambda `0.8`, scale `1.0`, with complete backfill.

That diagnostic substantially and strictly improved the exact #839 GMN catalogue key:

- #839: r25/r50/r100/r500 = 22/40/75/159; top100 precision = 0.7645689180574315; MRR = 0.019037817654898162;
- purity+diversity: **24/47/81/166**; top100 precision = **0.8534939929790234**; MRR = **0.02094738537699626**; qualified labels = 256.

The immutable #971 result is run `31435769113`, artifact `9080977251`, digest `sha256:992c3bfcd90248c13b07b61a3f0311e657b355228bf35c0885d0517ac50fa24d`.

v29 therefore freezes **exactly that already-computed architecture**. There is no further GMN model, feature, target, diversity, threshold, quota, suppression, or fusion search.

## Frozen architecture

Candidate universe and proposal science remain exact #839:

- 226 hard v8 families;
- 1,075 P19 prelabel families;
- 3,203 P20 prelabel families;
- union = 4,504 families.

The full deployable purity model is exactly the #840 selected classifier:

- target: exact #839 positive predicate (dominant precision >= 0.5 and overlap >= 4);
- features: exact #840 feature vector = pre-existing structural/cohesion features plus source one-hot and the four P20-native fields;
- model: `HistGradientBoostingClassifier`;
- learning rate = 0.05;
- max iterations = 250;
- max leaf nodes = 31;
- L2 regularization = 1.0;
- random state = 20260809;
- training weights: exact #840 diversity weights;
- full target-excluded GMN 2022/2023 training table.

Deployment ranking is:

1. score every family by full-model purity probability;
2. apply exact #839 geometric diversity with lambda `0.8`, scale `1.0`, exact tie semantics;
3. preserve every family by complete backfill.

No quality-head fusion, consensus fusion, event-Jaccard suppression, family deletion, source quota, threshold, or membership change is part of v29.

## Model-freeze run

The model-freeze workflow must:

1. verify the immutable #971 result and exact diagnostic metrics above;
2. reconstruct the exact target-excluded GMN 4,504-family table behind the 20°–55° firewall;
3. verify exact #840 source blob `976ae788ec76a2da7035735ea62118c7289adc5e`;
4. construct the exact #840 features, target, strict-group weights, and full HGB-31 model;
5. serialize the model with `n_jobs`/parallel nondeterminism absent by model definition;
6. emit hashes for model, feature matrix, target vector, weights, family order, and feature names.

No in-sample score is used for model selection or scientific promotion.

## Claim boundary

A successful v29 freeze establishes only a deterministic GMN-trained model artifact for the already-selected architecture. SonotaCo 2013/2014 remains exposed development evidence and is not accessed in this freeze. No MAARSY, DMS, OrbitTrace target information, target-region events, or matched Sugar/HDBSCAN row subset may be accessed.

A later v29 SonotaCo application must be frozen separately before its result is inspected and must use canonical label-free survey input rather than comparator-specific matched rows as detector input.