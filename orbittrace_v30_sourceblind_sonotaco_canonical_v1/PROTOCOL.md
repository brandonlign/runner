# OrbitTrace v30 source-blind canonical SonotaCo exposed development v1

## Purpose

Apply the exact source-blind GMN model frozen by PR #977 to the exact canonical label-free SonotaCo 2013/2014 catalogue pipeline already validated in PR #973, with no SonotaCo retraining, feature selection, source quota, panel-specific ranking, or parameter search.

SonotaCo 2013/2014 is exposed development-only. This is not protected validation.

## Authorization

PR #977 authoritative run `31438526674` returned `PASS_GMN_SOURCEBLIND_PURITY_DIVERSITY_V1` and froze the full 21-feature HGB-31 model before any SonotaCo access.

Frozen identities:

- model SHA-256 `e44d0853646114c6a4e77852527ce2e9d15933e26631bf68abb172a1fd7e609a`;
- feature dimension 21;
- feature-name SHA-256 `e8507fbb8a2160485e7496bce9ec8d825cfeb248eac4533f5ce526e81e3cd861`;
- target SHA-256 `3018f152e96e3de605905d9d4108eccf077dad1ddb0d17365a0028c538da21c4`;
- weights SHA-256 `124cc8a7f5a881bd69a046feebaa26576450a4d7cdf06da1d84942eb00aefb7c`;
- deployment diversity lambda `0.8`, scale `1.0`, complete backfill, no family deletion.

The 21 features are exactly the generic #840 prefix: 14 structural + 7 membership-cohesion features. All seven generator/source-specific fields are absent: no hard/P19/P20 one-hot and no P20-native ranking fields.

## Canonical detector input and candidate generation

Reproduce PR #973 exactly before ranking:

- canonical label-free SonotaCo base 2013 SHA-256 `f84e6db4166be065a73c7d030d66fdf796c1c6c2b5ee692f1e3299e8ae7c05ce`, 24,899 rows;
- canonical label-free SonotaCo base 2014 SHA-256 `1fab29c7368b63cc9c9d172dcadec5918d6514bfbb09f0f71e54eebb9bf32f00`, 20,575 rows;
- exact hard, P19, and P20 portable generators;
- exact v15 hard-family consensus ordering used only as the pre-existing generic hard-rank percentile feature and diversity tie key;
- exact schema-portable generic feature formulas already fixed in PR #973: canonical row `year` replaces GMN event-ID year parsing, and application-pair centroid keys are 2013/2014;
- exact #839 geometric diversity lambda 0.8 / scale 1.0 with complete backfill;
- exact #461/v17 top-100 joint-conformal membership expansion.

Candidate generation and membership are label-free and independent of Sugar/HDBSCAN matched subsets.

## Pretruth lock

The complete ranked canonical catalogue and expanded memberships must be written and SHA-256 locked before the exposed truth/comparator artifact is downloaded. At that point:

- `truth_accessed = false`;
- matched comparator rows are not detector input;
- no panel-specific candidate generation or ranking has occurred;
- no SonotaCo model fitting has occurred.

## Evaluation

After the pretruth lock, evaluate the same frozen catalogue on the exact four immutable literature panels and budgets used by PR #973 under the exact Hungarian equal-budget F1 semantics:

- Sugar 2013;
- Sugar 2014;
- HDBSCAN 2013;
- HDBSCAN 2014.

A panel passes only if candidate macro-F1 is strictly greater than the literature comparator and recovered F1>0.5 count is at least equal. Overall PASS requires all four panels.

No post-result search, reranking, source quota, feature restoration, threshold, calibration, model change, or second attempt is authorized from the scientific result.

## Firewall

No MAARSY, DMS, OrbitTrace target information, protected 20°–55° target-region events, or protected validation data may be accessed. SonotaCo remains exposed development-only.
