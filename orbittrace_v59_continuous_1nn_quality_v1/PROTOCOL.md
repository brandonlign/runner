# OrbitTrace v59 continuous 1-NN quality v1

## Scientific role

Separately frozen **SonotaCo exposed-development successor** after binding v57 failure. Exact v31 remains the parent.

v59 changes one scientific quantity: the target mapping carried by v31's local nearest-neighbor geometry. Instead of binarizing fold-training annual membership quality at `F1 > 0.5` and comparing nearest positive versus nearest nonpositive distances, v59 uses the same strict-OOF standardized Euclidean geometry to find the single nearest fold-training family and transfers that family's two continuous annual fixed-label F1 values.

SonotaCo 2013/2014 remains `EXPOSED_DEVELOPMENT_ONLY`, not external validation.

## Motivation fixed before outcome

The v24 two-head random-forest regression line established that continuous annual membership quality contains useful information but that squared-error tree regression can strongly shrink rare excellent held-out families toward the bulk. Exact v31 later improved HDB by replacing fitted regression with local geometry, but v31 discards most continuous target information by reducing each annual training target to the event `F1 > 0.5`.

v59 tests one parameter-free bridge between those findings: preserve exact v31 local geometry and k=1, but let the nearest training exemplar carry its observed continuous annual quality directly. No fitted regressor, interpolation coefficient, distance weighting, or target threshold is introduced.

No prior repository successor evaluates this exact strict-OOF continuous 1-nearest-neighbor annual-quality transfer.

## Immutable parent and representation

v59 must first reproduce exact v31 unchanged:

- Sugar 2013 `0.2719801488280529 / 16`;
- Sugar 2014 `0.31529041952487225 / 17`;
- HDB 2013 `0.14888037368183737 / 9`;
- HDB 2014 `0.15198123772301594 / 9`.

Exact v31 parent source blob: `917e3cd6f9310ca1282e0efa58ed0924d03ed4da`.

Keep unchanged:

- immutable #950 candidates, memberships, 71D features and centroids;
- stacked Sugar+HDB development table;
- exact deterministic strict whole-shower five-fold OOF grouping;
- exact fold-training mean / population-standard-deviation z-score, with zero std -> `1.0`;
- ordinary Euclidean distance across all 71 standardized dimensions;
- `k=1`;
- exact fixed-label annual F1 semantics already used by v24/v31;
- exact #839 diversity `lambda=0.8`, `scale=1.0` and tie semantics;
- immutable exact-v19 order;
- one equal rank-sum with exact v19;
- fixed candidate budgets and literature evaluator;
- same rule on Sugar and HDB.

## Sole v59 scientific change

Construct each fold-training family's two continuous annual targets exactly as in v31/v24:

- determine the same fixed best label using existing `family_truth` semantics;
- if the family is nonpositive or has no fixed label, set both annual targets to `0.0` exactly as the parent development code does;
- otherwise compute exact `annual_f1_for_fixed_label` for 2013 and 2014.

For each OOF fold:

1. fit the exact v31 fold-training z-score;
2. for each held-out family, compute ordinary 71D Euclidean distance to **every** fold-training family;
3. select exactly one nearest training family; deterministic ties use the first occurrence in the immutable stacked training-row order, i.e. NumPy `argmin` semantics;
4. set `pred_2013` equal to that same nearest family's continuous 2013 F1 target;
5. set `pred_2014` equal to that same nearest family's continuous 2014 F1 target;
6. define the sole local-quality score `min(pred_2013, pred_2014)`.

Thus the same nearest geometric exemplar supplies both annual quality values. There is no separate annual neighbor selection, no nearest-positive/nonpositive partition, and no fitted model.

After all strict-OOF scores are fixed, apply exact #839 diversity and one equal rank-sum with immutable v19 exactly as v31.

## Evaluation gate

Exactly one v59 order per route is evaluated. The first technically valid result is binding.

PASS requires all four frozen literature pair gates: candidate macro-F1 strictly exceeds the matched literature comparator and recovered-family count is at least the literature count in Sugar 2013, Sugar 2014, HDB 2013, and HDB 2014.

## No rescue

If v59 fails, permanently close this exact continuous 1-NN quality architecture. Do not retry with:

- k > 1;
- averaging multiple neighbors;
- inverse-distance or kernel weighting;
- separate annual nearest neighbors;
- positive-only or joint-positive-only neighbors;
- clipping, transforming, calibrating, ranking, binarizing, or thresholding the neighbor F1 values;
- blending v59 with v31 margins or v24 predictions;
- route/year-specific rules;
- metric/scaling/feature/block changes;
- diversity/fusion changes;
- top-k/rank-window/budget exceptions;
- identity corrections;
- post-result second searches.

Any future successor must have a distinct independently motivated mechanism.

## Explicit prohibitions

No model fitting beyond fold-local z-scaling, no target/threshold grid, no k search, no metric search, no feature search, no block-weight search, no distance weighting, no interpolation, no annual-neighbor split, no classifier/regressor, no component/cross-route/quality rescue, no v19/local fusion rescue, no oracle identity, and no post-result tuning.

## Firewall

Protected OrbitTrace solar longitude `20°–55°` remains inaccessible. Do not access OrbitTrace target information or target-region events. Do not access MAARSY or DMS scientifically. Every result must assert `SonotaCo = EXPOSED_DEVELOPMENT_ONLY` and the full protected-data firewall.