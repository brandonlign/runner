# OrbitTrace dual-cut recurrent rank v1 — frozen protocol

## Status

**FROZEN BEFORE THE FIRST DCRR PAPER-BENCHMARK TRUTH OUTCOME.**

This successor follows two binding observations on the exact current paper benchmark:

1. RC-EOM v1 showed that ordinary-EOM evidence can improve macro-F1 on the Sugar panels but loses current recurrent-EOM's small-budget HDB advantage.
2. The zero-label selection/ranking diagnostic showed that current recurrent-EOM differs from ordinary EOM through both ranking and candidate selection: at HDB B=14, recurrent and ordinary share 13/14 memberships, but one recurrent top-14 membership is absent from the entire ordinary flat catalogue; on Sugar B=40, two recurrent top-40 memberships are absent from the entire ordinary catalogue.

DCRR therefore preserves every current recurrent-EOM proposal and its exact ranking signal, while adding the alternative ordinary-EOM proposals from the same fixed hierarchy.

## 1. Scientific method

For each pooled two-year catalogue route:

1. fit exactly one HDBSCAN hierarchy in the existing GEO6 representation with `min_cluster_size=10`, `min_samples=10`, Euclidean metric, EOM, zero epsilon, and no single root cluster;
2. compute ordinary HDBSCAN EOM stability `S_ord(C)` and its ordinary-EOM flat selected node set `O`;
3. compute exact recurrent-EOM stability `S_rec(C)` using frozen kernel Git blob `30ac3fa3bc47910370df528fcf3ae8ecb6277b47` and its recurrent-EOM flat selected node set `R`;
4. construct the candidate node universe `U = O union R` with exact duplicate memberships removed;
5. rank all candidates in `U` by the **unchanged current recurrent-EOM order**:
   - descending `S_rec(C)`;
   - descending `S_ord(C)`;
   - descending member count;
   - deterministic membership hash.

No candidate is removed merely because it overlaps another candidate from the alternate cut. The output is explicitly a ranked **candidate-hypothesis catalogue**, not a single partition. This is deliberate: ordinary and recurrent EOM are two pre-existing, parameter-free selections of the same hierarchy, and the benchmark already evaluates ranked candidate hypotheses with one-to-one assignment and fixed capacity.

There is no new score weight, fusion coefficient, cutoff, support threshold, route-specific rule, budget-aware rule, truth-based suppression, or post-result fallback.

## 2. Label-free activity audit

Before any DCRR truth access, execute the frozen pretruth builder on the exact row artifacts used by the current paper equal-temporal benchmark.

For both `sugar` and `hdbscan` routes:

- verify exact 2013/2014 row hashes/counts;
- verify ordinary EOM reconstructed through the custom path matches installed HDBSCAN exactly;
- verify exact recurrent kernel identity;
- persist complete ordinary, recurrent, and DCRR candidate memberships and ranks;
- record exact top-K membership overlap between DCRR and current recurrent-EOM for K=10,14,20,40,43,50,100;
- record how many DCRR top-K candidates are ordinary-only additions;
- record whether each ordinary-only addition overlaps/contains/is-contained-by a recurrent candidate;
- record `truth_accessed=false` and `shower_label_fields_accessed=false`.

The scientific method may not change after this activity audit. The audit can only determine whether the mechanism is active and quantify its label-free catalogue perturbation.

DCRR earns one paper-benchmark truth test only if it is technically valid and mechanism-active. No truth-blind overlap threshold is used to tune or reject it after seeing the audit; the audit is characterization, not parameter selection.

## 3. Primary benchmark — exact current paper benchmark

The sole primary scientific evaluation is the current paper's equal-temporal pooled SonotaCo benchmark:

- Sugar 2013, comparator-complete B=40;
- Sugar 2014, B=43;
- published-configuration HDBSCAN 2013, B=14;
- published-configuration HDBSCAN 2014, B=14.

Use exactly the current paper's eligible-shower definition, one-to-one Hungarian F1 assignment, pooled 2013+2014 label-free temporal information, and literature comparator outputs.

The later symmetric tuned-HDBSCAN benchmark is secondary characterization only after a primary PASS. It cannot redefine or rescue the paper endpoint.

## 4. Promotion gate versus current recurrent-EOM

DCRR replaces current recurrent-EOM only if all conditions hold:

1. DCRR strictly beats the corresponding literature comparator in macro-F1 on all 4/4 paper panels;
2. DCRR recovery (`F1 > 0.5`) is at least the literature comparator on all 4/4 panels;
3. DCRR macro-F1 is no lower than current recurrent-EOM on every panel;
4. DCRR recovery is no lower than current recurrent-EOM on every panel;
5. DCRR has strict macro-F1 improvement over current recurrent-EOM on at least one panel;
6. mean macro-F1 across all four panels is strictly higher than current recurrent-EOM.

Any valid failure closes exact DCRR v1. No overlap suppression, alternate union rule, score fusion, ordinary-score rerank, rank cutoff, route exception, or second SonotaCo rescue is authorized from the result.

## 5. Claim boundary

A PASS would support replacing the paper's recurrent-EOM candidate catalogue with DCRR only after the manuscript/evidence ledger is updated to the immutable result. It would not by itself establish universal state of the art or pristine cross-survey generalization.
