# OrbitTrace v29 canonical SonotaCo exposed-development application v1

## Status and purpose

This is a separately frozen, no-retuning application of the GMN-selected v29 purity-diversity architecture to already-exposed SonotaCo 2013/2014.

SonotaCo is **development-only**. A PASS here cannot become external validation and cannot authorize MAARSY, DMS, OrbitTrace target access, or any historical discovery claim.

## Immutable v29 model

Use only model-freeze run `31436385652`, artifact `9081192169`, digest `sha256:a26d2446ff653c8627448a8cd8418b1da67316ce34924366acdb3b21274e2f00`.

Required manifest verdict: `PASS_V29_GMN_PURITY_DIVERSITY_MODEL_FREEZE`.

Required model SHA-256:

`b10f8e307f1ef632e41b16f02997a8bd3d01ecc2fa84ea018974eef98b390978`

Required architecture:

- exact #840 28-feature HGB-31 purity probability;
- no quality or consensus fusion;
- no event-Jaccard suppression;
- no source quota;
- no thresholding or family deletion;
- exact #839 geometric diversity lambda `0.8`, scale `1.0`, complete backfill.

## Detector input: canonical SonotaCo rows only

Reuse the immutable label-free preparation artifact:

- run `31354363306`;
- artifact `9050107352`;
- digest `sha256:1296d757b5ea1dd94f9c9077fd769fdc8f00ec06d0881d8548fd1df4608344cc`;
- preparation verdict `PASS_FINAL_SONOTACO_LABEL_FREE_PREPARATION`.

Detector input is **exactly**:

- `base_2013.json`, SHA-256 `f84e6db4166be065a73c7d030d66fdf796c1c6c2b5ee692f1e3299e8ae7c05ce`, 24,899 rows;
- `base_2014.json`, SHA-256 `1fab29c7368b63cc9c9d172dcadec5918d6514bfbb09f0f71e54eebb9bf32f00`, 20,575 rows.

The Sugar-matched and HDBSCAN-matched row subsets are **forbidden detector input**. They may not affect proposal generation, components, families, features, purity probabilities, diversity, rank, or membership expansion.

The canonical detector catalogue must be completely generated, serialized, and SHA-frozen before any known-shower truth/comparator artifact is downloaded.

## Frozen candidate and membership pipeline

On canonical base rows use exactly the already-frozen broad v17 proposal/membership pipeline, changing only the rank signal to v29:

1. exact label-free v8 within-year fixed4 proposal/component science;
2. exact 1.5-radius cross-year hard-family graph and pooled same-year centroid repair;
3. hard-family ordering by the promoted density-safe v15 `(128,96,64)` adaptive consensus, with `K=min(cap,N_local)`;
4. exact pair-portable P19 proposal layer;
5. exact pair-portable P20 recurrent isolated 4+4 layer;
6. union = hard + P19 + P20, no family deleted;
7. exact #840 28 features computed on this seed family universe;
8. score by the immutable v29 GMN HGB-31 purity model;
9. exact #839 centroid diversity at lambda `0.8`, scale `1.0`, exact hard-rank tie semantics, complete backfill;
10. exact pre-SonotaCo #461 joint-conformal membership expansion on ranks 1-100 only, exactly as v17; source-year seed requirement remains >=4 and no estimator threshold is weakened.

No SonotaCo-specific parameter is introduced.

## Pretruth freeze

Before truth access emit:

- canonical input hashes/counts;
- hard/P19/P20/union family counts;
- complete seed-order SHA-256;
- purity probability vector SHA-256;
- final diversity-order SHA-256;
- expanded top-100 membership SHA-256;
- complete ranked family catalogue with final memberships;
- proof flags that matched comparator rows/truth/MAARSY/DMS/target information were not accessed.

The same single canonical v29 order is used for every subsequent literature panel.

## Exposed literature evaluation

Only after the canonical catalogue is frozen, download the immutable exposed SonotaCo truth/comparator artifact from run `31405109267`, artifact `9069505548`, digest `sha256:cdea3297c234b0b3a8f09c2208649c8607bb3e9a9004d299f6dcc18536ebb797`.

Evaluate the same fixed ranked catalogue against each panel:

- Sugar 2013;
- Sugar 2014;
- HDBSCAN 2013;
- HDBSCAN 2014.

For a panel, candidate membership is intersected with that panel's immutable truth-ID universe before F1 calculation. Rank is never recomputed. Use the exact frozen comparator budget from `evaluation_<route>_<year>.json` and exact one-to-one Hungarian maximum-F1 assignment semantics used by #854/v15.

A panel superiority PASS requires both:

- candidate macro-F1 > frozen comparator macro-F1;
- candidate recovered showers with F1 > 0.5 >= frozen comparator recovered count.

Overall v29 exposed-development PASS requires all four panels to pass. No secondary selector, alternative rank, budget change, panel-specific route, model refit, threshold, or post-result search is permitted.

## Interpretation

- PASS: `PASS_V29_CANONICAL_SONOTACO_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT`
- FAIL: `FAIL_V29_CANONICAL_SONOTACO_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT`

Either verdict is exposed development only.

## Explicit prohibitions

- no Sugar/HDBSCAN matched subset as detector input;
- no panel-specific candidate generation or ranking;
- no SonotaCo labels in features/model/rank;
- no model retraining on SonotaCo;
- no quality-head fusion;
- no Jaccard suppression/family deletion;
- no source quotas;
- no parameter or threshold search;
- no MAARSY/DMS access;
- no OrbitTrace target information or 20°–55° target-region event access;
- no rewriting v29 after the result.