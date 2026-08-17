# Recurrent-EOM CV survival rank v1 — one-shot SonotaCo protocol

## Authorization

The immutable label-free development gate passed in run `31995565227` before any SonotaCo access by this successor. This protocol therefore activates the **single** matched SonotaCo comparison authorized by `PRE_RESULT_AMENDMENT.md`. SonotaCo 2013/2014 is already exposed development/validation data, not pristine external validation.

No SonotaCo outcome has been used to choose the score, fold rule, number of folds, overlap metric, ranking rule, K values, panel budgets, or promotion gate.

## Immutable method

Parent detector/extractor is exact recurrent-EOM HDBSCAN v1:

- pooled GEO6 representation;
- HDBSCAN `min_cluster_size=10`, `min_samples=10`, Euclidean metric, EOM selection;
- recurrent node stability `min(E_year1, E_year2)` using year-normalized annual EOM;
- exact parent family memberships unchanged.

CV-survival ranking is exactly the already-passed rule:

1. assign each event to one of ten deterministic folds by `uint64_be(sha256(utf8(event_id))[0:8]) mod 10`;
2. for each fold, delete that fold and rerun exact recurrent-EOM on the retained rows;
3. for every immutable full parent family `C`, remove its held-out event IDs and compute its maximum Jaccard against the retained-fold recurrent-EOM families;
4. `survival(C) = mean_f J_f(C)`;
5. `S_cv(C) = recurrent_stability(C) * survival(C)`;
6. order by `S_cv` descending, recurrent stability descending, survival descending, member count descending, family ID ascending.

There is no threshold, fitted coefficient, exponent, fold weighting, alternate overlap metric, route/year rule, membership change, rank fusion, or diversity rule.

## Exact SonotaCo inputs

Use only the previously frozen label-free route rows from run `31354363306`, artifact `orbittrace-final-sonotaco-label-free-preparation-v2`:

- preparation manifest SHA-256 `0a24077f352ddba91c5fea2a102f996d6bea154b1bc769235a4dd916850dba2b`;
- Sugar 2013 rows SHA-256 `47fb0b700fbf710c7b061eead343016bd8d182756eb0c7f406507c5739e4c4f8`, n=`18,638`;
- Sugar 2014 rows SHA-256 `bc83c113e9a14b1c6e1ef460ca9a40e05df77f3a449fec6064f8910add04c912`, n=`15,400`;
- HDBSCAN 2013 rows SHA-256 `2433b556d4a859580ef5431d2307ef34c8fa4c15d42841a2ec7b0c11e5f1f158`, n=`16,028`;
- HDBSCAN 2014 rows SHA-256 `206692292b2ca252777e40c13c367880740d8e2576d27615f7ea94b7790e3f55`, n=`13,283`.

The exact immutable recurrent-EOM full-route parent is the already-binding pretruth from run `31829200215`, artifact `9230008341`, pretruth SHA-256 `c6afbc0c3443b6c34e3f90b0f63453a0a35bfae3f3c84ffe8a479f8f50cffeef`:

- Sugar candidates: `144`;
- HDBSCAN candidates: `123`.

The full parent is not regenerated for scientific comparison; its existing memberships/ranks are the control. Only the ten label-free deletion-fold recurrent-EOM catalogues are newly generated.

## Pretruth barrier

For both routes, all ten deletion-fold catalogues, every full-parent survival value, and the complete successor order must be persisted and hash-frozen before SonotaCo shower truth is available to the evaluation step.

The pretruth stage cannot accept a truth file.

## Evaluation

After pretruth freeze, restore the same immutable exposed truth artifact used by recurrent-EOM's binding benchmark: run `31405109267`, artifact `orbittrace-v15-exposed-matched-sonotaco-literature-result-v1`.

Use the exact existing one-to-one Hungarian F1 evaluator and exact matched budgets:

- Sugar 2013: `34`;
- Sugar 2014: `46`;
- catalogue-HDBSCAN 2013: `11`;
- catalogue-HDBSCAN 2014: `9`.

Exact recurrent-EOM parent controls must reproduce:

- Sugar 2013: macro-F1 `0.3752906816276458`, recovered `23`;
- Sugar 2014: macro-F1 `0.43773122295664196`, recovered `24`;
- HDBSCAN 2013: macro-F1 `0.1914598192215768`, recovered `11`;
- HDBSCAN 2014: macro-F1 `0.1685878550176112`, recovered `9`.

## Promotion gate

`PASS_RECURRENT_EOM_CV_SURVIVAL_RANK_V1_SONOTACO_DEVELOPMENT` requires all of:

1. exact parent family IDs and event memberships remain unchanged on both routes;
2. CV-survival changes the complete order on at least one route;
3. successor macro-F1 is >= recurrent-EOM parent macro-F1 on all four panels;
4. successor recovered count is >= parent recovered count on all four panels;
5. at least one panel has a strict macro-F1 increase or strict recovered-count increase.

Otherwise the exact method fails the SonotaCo portability gate and is closed. No post-result change to the score, folds, rank rule, panel/route handling, membership, or gate is authorized.

A PASS would make CV-survival the stronger **exposed-development catalogue-scale ranking candidate**, but still would not constitute pristine external validation and would not automatically authorize or alter AMOS.

## Firewall

Protected `[20°,55°]`, OrbitTrace target information/events, AMOS, MAARSY and DMS remain inaccessible. No pristine endpoint is opened by this protocol.