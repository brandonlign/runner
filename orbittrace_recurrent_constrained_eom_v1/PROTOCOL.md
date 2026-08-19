# OrbitTrace recurrent-constrained EOM v1 — frozen protocol

## Status

**FROZEN BEFORE THE FIRST RC-EOM PAPER-BENCHMARK TRUTH OUTCOME.**

This successor is motivated by the symmetric tuned SonotaCo result in PR #1361: ordinary EOM and recurrent-EOM independently selected the same `20/20` support in both cross-year folds, yet ordinary EOM had the stronger early-budget ranking. The density-synchronous successor in PR #1362 changed the recurrent quality functional but reproduced essentially the same deficit. Earlier residual diagnostics also show that continued scalar recurrence-score changes are not the productive lane.

RC-EOM therefore changes the role of recurrence. It does **not** replace ordinary EOM stability with another recurrence score. Recurrence is a feasibility constraint on the ordinary EOM optimization.

## 1. Scientific method

Fit exactly one pooled two-year HDBSCAN hierarchy in the existing OrbitTrace GEO6 representation:

- `min_cluster_size = 10`;
- `min_samples = 10`;
- Euclidean metric;
- zero cluster-selection epsilon;
- no single root cluster.

Let `S(C)` be ordinary HDBSCAN excess-of-mass stability for condensed-tree cluster node `C`.

Let `n_y(C)` be the number of point descendants of `C` from observing year `y`.

A node is **feasible** iff

`n_2013(C) >= 4 and n_2014(C) >= 4`

on SonotaCo, with the corresponding two observing years used on any development transfer.

The annual support value `4` is inherited from the project's already-established meteor-stream reporting/support semantics. It is fixed and must not be swept, tuned, made rank-dependent, or changed after any outcome.

RC-EOM returns the maximum-ordinary-EOM antichain subject to feasibility. The dynamic program is exactly ordinary EOM except that an infeasible node cannot be selected; the best already-computed feasible descendant stability mass is propagated upward instead.

Final candidates are ranked by **ordinary EOM stability**. Annual balance, recurrent stability, candidate size, truth, literature budget, and route identity do not enter the primary rank.

There is no blend coefficient, recurrence weight, percentile, soft minimum, score exponent, parent preference, top-K exception, or result-informed fallback.

## 2. Why this is distinct from closed lanes

RC-EOM is not:

- promoted recurrent-EOM's `min(annual EOM)` score;
- density-synchronous recurrent-EOM;
- an annual mean/harmonic/soft-min rescue;
- a recurrence-efficiency reranker;
- CV-survival reranking;
- low-support local-BIC HDBSCAN;
- TopoModal/Pareto/DAG refinement;
- membership erosion/trimming;
- FLASC branch substitution.

It preserves ordinary HDBSCAN's density objective and changes only the admissible set of reportable hierarchy nodes.

## 3. Label-free activity audit

Before any new shower-truth access for RC-EOM, execute `build_pretruth.py` on the exact row artifacts used by the paper's equal-temporal benchmark.

For both paper routes (`sugar`, `hdbscan`):

1. verify the exact frozen 2013/2014 row hashes and counts;
2. fit pooled GEO6 HDBSCAN `10/10`;
3. prove the local ordinary-EOM dynamic program reproduces the installed HDBSCAN flat partition exactly;
4. compute the complete RC-EOM catalogue;
5. prove all selected RC-EOM nodes satisfy annual support `>=4+4`;
6. prove selected memberships are pairwise disjoint;
7. persist complete RC-EOM memberships and ranks before truth;
8. record candidate counts, ordinary ineligible-node counts, node differences, assigned-event counts, and exact top-K membership overlap;
9. record `truth_accessed=false` and `shower_label_fields_accessed=false`.

The method itself may not change after this audit. The audit only determines whether the frozen mechanism is active and technically valid. If it is inactive or violates an invariant, the method is closed without truth scoring.

## 4. Primary benchmark — exactly the current paper benchmark

If the pretruth audit passes, the sole primary scientific evaluation is the paper's existing equal-temporal pooled SonotaCo benchmark. Do not substitute the later symmetric-tuning benchmark as the primary paper endpoint.

Use exactly the same four panels and scoring semantics already in the manuscript/evidence ledger:

- Sugar 2013;
- Sugar 2014;
- published-configuration HDBSCAN 2013;
- published-configuration HDBSCAN 2014.

For every panel:

- all methods receive pooled 2013+2014 label-free observations before truth;
- evaluate the indicated year only after the RC-EOM catalogue is frozen;
- use the same eligible-shower definition;
- use the same one-to-one Hungarian F1 assignment;
- use the same comparator-complete candidate budget as the current paper benchmark.

Frozen literature budgets from the current paper result are not inputs to RC-EOM construction or ranking; they enter only evaluation.

## 5. Successor promotion gate

RC-EOM is promoted over the current paper recurrent-EOM method only if all of the following hold on the exact four paper panels:

1. RC-EOM still beats the corresponding literature comparator in macro-F1 on all 4/4 panels;
2. RC-EOM recovers at least as many `F1 > 0.5` showers as the literature comparator on all 4/4 panels;
3. versus current recurrent-EOM, RC-EOM has no macro-F1 regression on any panel;
4. versus current recurrent-EOM, RC-EOM has no recovered-shower regression on any panel;
5. RC-EOM has strict macro-F1 improvement over current recurrent-EOM on at least one panel;
6. mean macro-F1 across the four panels is strictly higher than current recurrent-EOM.

A tie does not satisfy a strict gate. Any valid failure closes exact RC-EOM v1. No annual-support sweep, support-parameter change, route exception, rank exception, score blend, or second SonotaCo rescue is authorized from the result.

The later tuned-HDBSCAN symmetric benchmark may be used only as a separately frozen harder secondary characterization after a primary PASS. It cannot rescue a primary FAIL or change the paper benchmark definition.

## 6. Claim boundary

A primary PASS would support replacing recurrent-EOM with RC-EOM in the paper only after the manuscript/evidence ledger is updated to the new immutable result. It would not by itself establish universal algorithmic state of the art or pristine external generalization.
