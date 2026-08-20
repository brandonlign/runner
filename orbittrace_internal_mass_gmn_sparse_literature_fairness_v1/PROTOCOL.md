# OrbitTrace internal-mass GMN sparse literature fairness v1

## Scientific role
This is a frozen, target-excluded GMN **paper-facing fairness benchmark** for the already-frozen support-resolved TopoModal + annual-density internal two-dimensional persistence mass (`M_2D`) catalogue. GMN 2022/2023 has already been used for method development, so this benchmark is **not** independent external validation. Its purpose is narrower: compare the frozen method against two literature comparators on exactly the same deterministic sparse event universes and under a common truth evaluator.

No method formula, candidate membership, candidate order, panel definition, literature configuration, evaluator, capacity rule, aggregation rule, or pass gate may change after activation.

## Frozen proposed method
Consume only `SUPPORT_CUT_BIFILTRATION_INTERNAL_MASS_V1_PRELABEL.json` from binding structural run `32041661731`, SHA-256 `7b1ddfcd32cd0b52321e3b3dfc614a88dd9b973f947c1d4d0de74fddf26b59cd`.

The proposed candidate extraction and order are inherited unchanged:
1. complete support-resolved TopoModal candidate set;
2. `M_2D` descending;
3. inherited `modal_contrast` descending for exact `M_2D` ties;
4. `family_hash` ascending.

The benchmark uses all eight already-frozen target-excluded sparse GMN universes:
- denominator 128, buckets 0..3;
- denominator 1024, buckets 0..3.
For each universe, 2022 and 2023 are evaluated separately, giving 16 annual panels.

## Literature comparators
Use the exact two comparator definitions already frozen in the prior direct GMN literature benchmark, with no retuning for this successor.

### Sugar 2017 central-value core
On the exact annual panel geometry in the same frozen six-dimensional GEO embedding:
- Euclidean DBSCAN;
- `min_samples = 5`;
- epsilon is the exact 23rd percentile (linear quantile) of the fourth-nearest-neighbor distance, excluding self by querying `k=5` and taking index 4.

### Peña-Asensio/Ferrari 2025 HDBSCAN
On the same annual panel geometry:
- HDBSCAN EOM;
- `min_cluster_size = 100`;
- `min_samples = 100`;
- Euclidean metric;
- `cluster_selection_epsilon = 0`;
- no single cluster.

These are published/frozen configurations, not a claim that they are optimally retuned for every sparse subsample. That limitation must be stated with any paper claim from this benchmark.

## Label-free pretruth stage
Before shower truth is loaded:
1. export the same target-excluded GMN 2022/2023 geometry used by the prior direct literature benchmark;
2. verify every stored annual panel event ID is present in that geometry and no protected event is present;
3. run both literature comparators independently on each exact annual panel;
4. serialize every comparator cluster membership and the unchanged proposed candidate order;
5. hash and upload the complete pretruth artifact.

No shower labels, target information, target-region events, SonotaCo outcome, or protected external-survey outcome may enter this stage.

## Comparator-capacity fairness rule
For each annual panel and comparator, let `K` equal that comparator's complete cluster count on that panel.

- Comparator catalogue: all `K` comparator clusters.
- Proposed catalogue: the first `K` candidates in the immutable `M_2D` ordering; if the proposed generator has fewer than `K` candidates, use its complete catalogue and record the capacity shortfall.

Thus the proposed method is never allowed more candidate slots than the comparator. Literature catalogues are unordered, so they are never post-hoc truncated by quality or truth.

If `K = 0`, both methods receive zero candidate slots for that comparator-panel comparison. This is retained transparently rather than treating a zero-output comparator as an automatic win.

## Common truth evaluator
For each annual panel, eligible shower labels are non-sporadic labels with at least four events in that exact panel universe.

For every candidate/label pair compute precision, recall, and F1 from event membership restricted to that annual universe. Use Hungarian one-to-one assignment maximizing F1. Unmatched eligible showers receive F1, precision, and recall zero.

Report per comparison:
- eligible-shower count;
- candidate count;
- macro F1;
- macro precision;
- macro recall;
- recovered showers with assigned F1 > 0.5;
- recovered showers with assigned F1 > 0.8.

This is the same annual Hungarian-F1 evaluator used by the prior direct GMN literature benchmark.

## Frozen aggregate endpoint
For each comparator separately, aggregate over all 16 annual panels using:
1. **primary:** unweighted mean panel macro F1;
2. total number of recovered showers with assigned F1 > 0.5.

The proposed method passes a comparator if and only if:
- its mean panel macro F1 is strictly greater than the comparator's; and
- its total F1>0.5 recoveries are not lower.

The overall verdict is `PASS_INTERNAL_MASS_GMN_SPARSE_LITERATURE_FAIRNESS_V1` only if both Sugar and HDBSCAN comparator gates pass. Otherwise the binding verdict is `NO_INTERNAL_MASS_GMN_SPARSE_LITERATURE_SUPERIORITY_V1`.

Also report, descriptively and without affecting the gate:
- d=128 and d=1024 scale-specific aggregates;
- strict/tied/lost panel counts by macro F1;
- candidate-capacity shortfalls;
- F1>0.8 recovery totals.

## Interpretation boundary
A pass supports only this statement: on the frozen target-excluded GMN sparse-panel benchmark, the frozen internal-mass catalogue outperformed the two frozen published-config literature comparators under comparator-capacity-matched annual Hungarian-F1 evaluation.

It does **not** establish untouched generalization, does not convert GMN 2022/2023 back into independent validation, and does not establish superiority to a newly tuned HDBSCAN family. CAMSv3 2017/2018 is not used as a substitute validation source because the official CAMSv3 archive ends at 2016 and repo history shows the remaining published CAMSv3 years are already scientifically spent.

## No-rescue rule
The first technically valid activated result is binding. After result access, do not alter the method, literature parameters, panel set, capacity rule, eligible-label floor, Hungarian assignment, macro aggregation, recovery threshold, or pass gate. Engineering-only failures before a scientifically valid result may be repaired without changing these scientific choices.
