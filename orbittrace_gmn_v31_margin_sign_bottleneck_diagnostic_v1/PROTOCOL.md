# OrbitTrace GMN v31 margin-sign bottleneck diagnostic v1 — frozen protocol

## Scientific role

This is a **GMN 2022+2023 target-excluded diagnostic only** for the exact v31 local-geometry parent. It evaluates no successor, creates no alternative scoring rule, and authorizes no SonotaCo access.

The already-frozen constituent-bottleneck diagnostic established that v31's remaining misses are predominantly a **constituent** problem rather than an equal-fusion problem: at top 100, 21 of the 29 qualified labels missed by the fused v31 order are outside the top 100 of both the immutable hard constituent and diversified local constituent.

Before proposing another constituent architecture, this diagnostic asks one narrower mechanism question using the exact raw v31 local score already defined by the parent:

> For qualified labels that exact v31 still misses at a fixed budget, does at least one positive family for that label lie on the **positive side** of the parent nearest-positive-versus-nearest-nonpositive decision boundary (`margin > 0`), or are **all** positive families for that label on the nonpositive side (`margin <= 0`)?

This distinguishes labels for which the existing local geometry has the correct class-side evidence somewhere but ranks it too weakly from labels for which the parent local geometry fails even at the natural zero-margin class boundary.

The protocol is frozen before its first result.

## Authoritative offline package

Use only the verified target-excluded v31 package:

- package workflow run `31663453082`;
- artifact `9167087908`;
- artifact digest `sha256:e8b019d84002e182d31399eb96cccbd96d47c3e4411ba7053b93ee2954f259e6`;
- package manifest SHA-256 `16fb5ef3cd8dbbb3873e9bc23874fe7da3db68498772a5e992fbceed6cb980d7`;
- exact 226x23 feature matrix SHA-256 `fea3b063772c75b675e37a227b53a4aa3c5b86fdcbfcef1487b1e1448689cdf5`;
- exact 226x8 centroid matrix SHA-256 `a53b9862f1ec3d751745f80aec2625d7904128474c9263c55ea953cf60d0621f`;
- parent prelabel SHA-256 `b45c4ce1a45bff515e411e211bc51dee879229ee97f7fcb7d8e7e05bfc106d09`;
- parent raw OOF margin SHA-256 `f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`.

No raw events, event IDs, hidden event-label mapping, SonotaCo, protected target-region, MAARSY, or DMS data may be accessed.

## Required exact v31 reproduction before diagnosis

Recompute the exact v31 strict-whole-shower OOF margin in the frozen 23D representation:

`m_i = d_nonpositive_i - d_positive_i`.

Require the complete 226-vector SHA-256 exactly:

`f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`.

Reconstruct the exact diversified local order (`lambda=0.8`, `scale=1.0`) and exact equal 1-based hard/local fused order.

Require exact controls:

Hard order:
- recovered@25 = 21;
- recovered@50 = 38;
- recovered@100 = 59;
- top-100 dominant precision = 0.6884631112636006;
- MRR = 0.046734076055452344;
- qualified = 95.

Fused v31:
- recovered@25 = 23;
- recovered@50 = 41;
- recovered@100 = 66;
- top-100 dominant precision = 0.7229521515453452;
- MRR = 0.050244164168646674;
- qualified = 95.

The exact eligible-label universe remains 355 labels and the exact qualified set remains 95 labels.

Any package/hash/fold/truth/evaluator/firewall mismatch fails before the diagnostic.

## Natural zero-margin interpretation

The parent score has a fixed, non-tuned decision meaning:

- `m_i > 0`: the held-out family is closer to its nearest positive training reference than to its nearest nonpositive training reference;
- `m_i = 0`: exact tie;
- `m_i < 0`: nearest nonpositive reference is closer.

This diagnostic uses **zero only** because it is the algebraic class boundary already inherent in v31. No alternative margin threshold or quantile is evaluated.

## Exact label-level construction

A family represents a qualified label only when its frozen truth summary has:

- `positive == true`;
- `best_label` equal to that qualified eligible label.

For each qualified label `L`, let `F_L` be all such positive families. Require `|F_L| >= 1`.

Record without changing any rank:

- `representative_family_count(L)`;
- `max_margin(L) = max_{i in F_L} m_i`;
- `min_margin(L) = min_{i in F_L} m_i`;
- `median_margin(L)`;
- count of representatives with `m_i > 0`, `m_i == 0`, and `m_i < 0`;
- exact first rank of `L` in the already-frozen hard, diversified-local, and fused parent orders.

Classify the label's raw local sign support exactly as:

- `ALL_POSITIVE`: every representative has `m_i > 0`;
- `MIXED`: at least one representative has `m_i > 0` and at least one has `m_i <= 0`;
- `ALL_NONPOSITIVE`: every representative has `m_i <= 0`.

Define:

- `ANY_POSITIVE_SUPPORT = ALL_POSITIVE + MIXED`;
- `NO_POSITIVE_SUPPORT = ALL_NONPOSITIVE`.

No label is selected or discarded based on these categories.

## Sole predeclared statistics

For each frozen budget `B in {25,50,100}`, restrict the descriptive summary to qualified labels missed by the exact fused v31 order (`fused_first_rank > B`). Report:

1. fused-missed label count;
2. counts and fractions of `ALL_POSITIVE`, `MIXED`, and `ALL_NONPOSITIVE`;
3. counts and fractions of `ANY_POSITIVE_SUPPORT` and `NO_POSITIVE_SUPPORT`;
4. median and interquartile range of `max_margin(L)` across those missed labels;
5. counts whose diversified-local first rank is `<= B` versus `> B`;
6. the exact 2x2 cross-tabulation among fused misses:
   - diversified local inside budget / any positive raw support;
   - diversified local inside budget / no positive raw support;
   - diversified local outside budget / any positive raw support;
   - diversified local outside budget / no positive raw support.

At **B=100 only**, also reproduce the prior constituent availability classification from the frozen hard and diversified-local first ranks:

- `CONSTITUENT_AVAILABLE`: hard or diversified local first rank `<=100`;
- `CONSTITUENT_ABSENT`: both first ranks `>100`.

Within the **21-label constituent-absent subset if and only if exact reproduction yields 21**, report the same sign categories and the 2-way split `ANY_POSITIVE_SUPPORT` versus `NO_POSITIVE_SUPPORT`.

This cross-tab is predeclared because it directly distinguishes the two mechanisms left open by the previous diagnostic:

- raw v31 geometry has positive-side evidence but budgeted local ranking still fails to surface it;
- raw v31 geometry itself puts all representatives on the wrong/nonpositive side.

## Predeclared descriptive outcome

At top 100, among the exact `CONSTITUENT_ABSENT` fused-missed labels:

- `SIGN_REJECTION_DOMINANT` if strictly more than half are `NO_POSITIVE_SUPPORT`;
- `SIGN_SUPPORT_DOMINANT` if strictly more than half are `ANY_POSITIVE_SUPPORT`;
- `MIXED_SIGN_BOTTLENECK` if exactly half fall in each class.

This outcome **does not authorize a successor**. It only identifies whether future mechanism research should primarily seek broader positive class support/representation (`SIGN_REJECTION_DOMINANT`) or better use/ranking of already-positive local evidence (`SIGN_SUPPORT_DOMINANT`).

## Explicit no-search rules

There is:

- no new score;
- no new scientific rank;
- no alternative margin threshold;
- no alternate budget;
- no fusion or diversity variant;
- no feature/metric/scaling/k/reference modification;
- no class calibration;
- no family/label/representative search;
- no subgroup/source/year search;
- no successor selected;
- no post-result second diagnostic chosen from this outcome.

## Firewall

Every execution must assert:

- `scientific_role = GMN_TARGET_EXCLUDED_PARENT_DIAGNOSTIC_ONLY`;
- `blind_exclusion = [20.0,55.0]`;
- `target_information_access = false`;
- `target_region_events_accessed = false`;
- `sonotaco_2013_2014_access = false`;
- `maarsy_scientific_access = false`;
- `dms_scientific_access = false`;
- `raw_event_rows_accessed = false`;
- `raw_event_ids_accessed = false`;
- `raw_hidden_label_mapping_accessed = false`;
- `new_rank_evaluated = false`;
- `successor_selected = false`.
