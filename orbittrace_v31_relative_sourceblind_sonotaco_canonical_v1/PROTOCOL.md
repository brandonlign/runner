# OrbitTrace v31 catalogue-relative source-blind canonical SonotaCo exposed development v1

## Purpose

Apply the exact catalogue-relative source-blind GMN purity model frozen by PR #984 to the exact canonical label-free SonotaCo 2013/2014 detector/membership pipeline already used by PR #980, without any SonotaCo fitting, feature/transform selection, source quota, panel-specific ranking, or parameter search.

SonotaCo 2013/2014 remains exposed development-only. This is not protected validation.

## Authorization

PR #984 authoritative GMN run `31439902823` returned `PASS_GMN_RELATIVE_SOURCEBLIND_PURITY_V1` before any SonotaCo access and froze:

- model SHA-256 `c23c626ecd415573f9a51344634ba50e8778963fee8ef03508902ac77c5342b0`;
- exact 21 generic #840 features;
- feature-name SHA-256 `e8507fbb8a2160485e7496bce9ec8d825cfeb248eac4533f5ce526e81e3cd861`;
- categorical columns `[0]` (`is_soft` only);
- exact label-free transform: for columns 1..20, within-catalogue average-tie empirical percentile `(rank - 1)/(N - 1)`;
- target SHA-256 `3018f152e96e3de605905d9d4108eccf077dad1ddb0d17365a0028c538da21c4`;
- weights SHA-256 `124cc8a7f5a881bd69a046feebaa26576450a4d7cdf06da1d84942eb00aefb7c`;
- exact #839 geometric diversity lambda `0.8`, scale `1.0`, complete backfill, no family deletion.

No alternate transform is allowed.

## Canonical detector and membership pipeline

Reproduce the exact PR #980 canonical pipeline before ranking:

- canonical label-free SonotaCo 2013 base SHA-256 `f84e6db4166be065a73c7d030d66fdf796c1c6c2b5ee692f1e3299e8ae7c05ce`, 24,899 rows;
- canonical label-free SonotaCo 2014 base SHA-256 `1fab29c7368b63cc9c9d172dcadec5918d6514bfbb09f0f71e54eebb9bf32f00`, 20,575 rows;
- exact hard, P19, and P20 portable generators;
- exact v15 hard-family consensus order only for the pre-existing generic hard-rank-percentile feature and diversity tie key;
- exact schema-portable 21 generic feature formulas from PR #973/#980;
- no hard/P19/P20 source one-hot and no P20-native ranking fields;
- exact #461/v17 top-100 joint-conformal membership expansion after ranking.

## Relative representation and ranking

After the complete unlabeled canonical candidate catalogue has been generated:

1. compute the exact 21 raw generic features for every family;
2. keep column 0 (`is_soft`) unchanged;
3. for each column 1..20 independently, replace values with average-tie empirical percentiles `(rank - 1)/(N - 1)` computed over the complete unlabeled canonical family catalogue;
4. apply the frozen PR #984 HGB-31 model to those 21 transformed values;
5. apply exact #839 diversity lambda `0.8`, scale `1.0`, complete backfill;
6. apply exact #461/v17 membership expansion to ranks 1–100 only.

The target catalogue itself supplies only its unlabeled feature distribution to the transform. No SonotaCo labels, comparator rows, fitted scale/offset, threshold, calibration, source quota, or model refit enters.

## Pretruth lock

The complete v31 ranking and expanded memberships must be written and SHA-256 locked before the exposed truth/comparator package is downloaded. At lock time:

- truth access = false;
- matched comparator rows are not detector input;
- model retrained on SonotaCo = false;
- panel-specific candidate generation = false;
- panel-specific ranking = false;
- source-specific ranking features = false.

## Exposed evaluation

After the pretruth lock, evaluate the exact same single catalogue on the immutable four literature panels and exact comparator budgets using the same Hungarian equal-budget F1 semantics as PR #973/#980:

- Sugar 2013;
- Sugar 2014;
- HDBSCAN 2013;
- HDBSCAN 2014.

A panel passes only if candidate macro-F1 is strictly greater than the literature comparator and recovered F1>0.5 count is at least equal. Overall PASS requires all four panels.

No post-result second search, alternate transform, source quota, partial source-feature restoration, threshold, calibration, model change, or reranking is authorized.

## Firewall

No MAARSY, DMS, OrbitTrace target information, protected 20°–55° target-region events, or protected validation data may be accessed. SonotaCo is exposed development-only.
