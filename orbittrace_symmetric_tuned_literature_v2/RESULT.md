# Symmetric tuned literature benchmark v2 — binding result

## Verdict

**Tuned ordinary HDBSCAN wins the prespecified primary benchmark. Recurrent-EOM does not establish superiority under symmetric method-native tuning.**

Binding scientific run: `32220399133`

Pre-result benchmark head: `33787b7733efa7e52483e59af183966b846e50f7`

Immutable result commit: `0705cc7` (`Record symmetric tuned literature benchmark v2 result`)

Result artifact: `9354450101`

## Fairness design

All three methods received the exact same pooled common SonotaCo 2013+2014 event universe: 15,988 events from 2013 and 13,258 from 2014, 29,246 total. Hyperparameters were selected only from one year's shower truth and scored on the opposite year; the roles were then reversed. Every method used the same Hungarian one-to-one F1 evaluator at K=10,20,30,40.

Recurrent-EOM and ordinary HDBSCAN searched the same finite-support grid through `(100,100)`; ordinary HDBSCAN additionally searched EOM versus leaf selection. Sugar used its exact frozen uncertainty-aware primitives with a broad 5–50% fourth-neighbour epsilon-percentile grid, 100 clones for development selection and 1000 clones for the selected test configuration.

Exact frozen recurrent-EOM kernel Git blob: `30ac3fa3bc47910370df528fcf3ae8ecb6277b47`.

Exact frozen literature-comparator dependency Git blob: `ab17e1205d72d8ab8361d8ba6cdad2e4c31fdcb2`.

## Aggregate held-out results

| Method | Mean test K10/20/30/40 macro-F1 | Mean test macro-F1 @40 | Total recovered @40 | Mean native macro-F1 |
|---|---:|---:|---:|---:|
| tuned ordinary HDBSCAN | **0.345476** | **0.460867** | **52** | **0.476289** |
| recurrent-EOM | 0.331642 | 0.431951 | 48 | 0.471306 |
| tuned Sugar | 0.252483 | 0.351218 | 39 | 0.436240 |

HDBSCAN exceeds recurrent-EOM by 0.013834 absolute / 4.17% relative on the prespecified primary metric and by 0.028916 absolute / 6.69% relative at K=40. The native complete-catalogue gap is much smaller: 0.004984 absolute / 1.06% relative.

## Fold stability

Both development folds independently selected the same structural settings:

- ordinary HDBSCAN: `min_cluster_size=20`, `min_samples=20`, EOM selection;
- recurrent-EOM: `min_cluster_size=20`, `min_samples=20`.

2013 development -> 2014 test:

- HDBSCAN mean budget macro-F1: **0.357099**; K40 `0.481521`, 26 recovered;
- recurrent-EOM: `0.339699`; K40 `0.443662`, 24 recovered;
- Sugar: `0.247983`; K40 `0.350336`, 18 recovered.

2014 development -> 2013 test:

- HDBSCAN mean budget macro-F1: **0.333852**; K40 `0.440213`, 26 recovered;
- recurrent-EOM: `0.323585`; K40 `0.420241`, 24 recovered;
- Sugar: `0.256983`; K40 `0.352100`, 21 recovered.

Thus the HDBSCAN advantage is present in both held-out directions and is not caused by a fold-specific parameter choice.

## Claim consequence

The prior equal-temporal SonotaCo result remains a valid comparison against **frozen published-configuration implementations**, but it must not be used as evidence that recurrent-EOM is superior to the HDBSCAN method family. When ordinary HDBSCAN is granted the same development labels, temporal information, event universe, candidate budgets, evaluator, and method-native hyperparameter search, it wins this benchmark.

Allowed interpretation: recurrent-EOM is a recurrence-aware variant with earlier GMN development gains and competitive catalogue performance, and it remains stronger than tuned Sugar on this benchmark.

Not supported: `recurrent-EOM is state of the art`, `recurrent-EOM beats HDBSCAN`, or any general algorithm-superiority claim based on the earlier frozen-configuration SonotaCo table.

This benchmark remains an **exposed two-year SonotaCo benchmark**, not pristine cross-survey external validation. It changes the algorithm-comparison claim, not the independent evidence for the OrbitTrace meteor-stream candidate itself.

## Engineering provenance

Runs `32220123672` and `32220234536` are pre-scientific engineering no-results: the first stopped on Python dynamic-import/dataclass registration; the second stopped because the frozen HDBSCAN runner could not locate its separately supplied exact comparator dependency. No clustering result was produced by either. The binding run `32220399133` passed the exact branch/kernel/comparator guards, installed the pinned numerical runtime, verified/downloaded the frozen row/source/truth artifacts, completed the full scientific benchmark, committed `RESULT.json`, and uploaded the result artifact successfully.
