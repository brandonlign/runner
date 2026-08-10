# OrbitTrace target-overlap canonical SonotaCo application v1

## Role

This is one exposed-development application of the already-frozen target-overlap model from PR #993. SonotaCo 2013/2014 remains an exposed matched literature benchmark, not pristine external validation.

No method development, target-overlap tuning, feature search, source quota, or comparator-specific ranking is authorized here.

## Frozen model

Use exactly the PR #993 full purity model produced by authoritative run `31442315024`:

- purity model SHA-256: `c886e6c9466130910fa918c168ea5a8b8ac05a4bf01cb9a5b570fef3cbe292cb`;
- feature dimension: `21`;
- feature-name SHA-256: `e8507fbb8a2160485e7496bce9ec8d825cfeb248eac4533f5ce526e81e3cd861`;
- training rule: exact #977 source-blind HGB-31 purity architecture with the single bounded target-overlap weighting rule frozen in #993;
- diversity: exact #839 lambda `0.8`, scale `1.0`, complete backfill, no family deletion.

The model was trained using GMN shower labels plus **label-free SonotaCo covariates/survey identity only**. No SonotaCo shower truth or literature-comparator result entered training.

## Frozen application pipeline

Use exactly the canonical label-free SonotaCo 2013/2014 inputs and the same portable application pipeline as v30:

1. exact v15 hard-family construction/order;
2. exact P19 and P20 portable generators;
3. one union catalogue of hard + P19 + P20 families;
4. exact 21 generic source-blind features using the already-frozen portable year/schema adapter;
5. score every family with the frozen #993 purity model;
6. apply exact #839 diversity lambda `0.8`, scale `1.0`, complete backfill;
7. apply exact #461/v17 top-100 membership expansion;
8. freeze the **single complete ranked catalogue** before any shower truth or comparator artifact is downloaded.

No panel-specific candidate generation, ranking, membership, feature transform, source handling, or budget-dependent reranking is allowed.

## Pretruth lock

Before exposed truth is downloaded, require:

- canonical base hashes/counts unchanged;
- exactly 21 features and no source-specific ranking features;
- model SHA exactly matches #993;
- no model refit on SonotaCo shower truth;
- one canonical catalogue only;
- catalogue SHA-256 written and verified against its summary;
- `truth_accessed=false` and `matched_comparator_rows_accessed=false`.

Only after that lock may the immutable exposed literature package be downloaded.

## Exposed literature evaluation

Evaluate the same frozen catalogue unchanged on exactly four previously frozen panels:

- Sugar 2013;
- Sugar 2014;
- HDBSCAN 2013;
- HDBSCAN 2014.

Use the exact existing comparator budgets and Hungarian macro-F1/recovery semantics. A panel is a win only when candidate macro-F1 is strictly greater than the comparator and recovered showers with F1 > 0.5 are at least the comparator count. The all-panel development criterion is 4/4 wins.

Whatever result occurs is final for this exact target-overlap weighting rule. No alternate overlap probability transform, clipping, exponent, calibration, feature subset, source quota, source routing, diversity value, or second post-result search is authorized from this run.

## Firewall

- SonotaCo role: exposed development only.
- SonotaCo shower truth used for training: false.
- Matched comparator rows used as detector input: false.
- Panel-specific candidate generation/ranking: false.
- MAARSY scientific access: false.
- DMS scientific access: false.
- OrbitTrace target-information access: false.
- Protected 20°–55° target-region data access: false.
