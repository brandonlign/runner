# Recurrent-EOM CV survival rank v1 — frozen protocol

## Scientific role

Owner-authorized reopening of exposed-development method work after PRs #1290/#1291. This does **not** restore the old pre-AMOS method-selection freeze: any positive result here is new exposed-development evidence only. SonotaCo, AMOS, protected target data, ASFN/EFN labels, MAARSY and DMS are inaccessible during selection.

## Motivation

PR #1290 decomposed recurrent-EOM residual misses and found ranking/selection to be the largest class (67/135 pooled misses, 49.63%). PR #1291 showed that ranking alone can improve one matched panel but that a direct pooled-stability penalty is not portable. The next successor therefore measures **candidate resampling survival** using only the already-frozen target-excluded GMN 2022/2023 perturbation folds from PR #1265.

## Immutable parent and perturbations

- Parent method: exact recurrent-EOM HDBSCAN v1 (`min_cluster_size=10`, `min_samples=10`, pooled GEO6 hierarchy, annual normalized EOM, recurrent score `min(E_2022,E_2023)`).
- Parent source blobs are inherited from PR #1265: `recurrent_eom.py` blob `30ac3fa3bc47910370df528fcf3ae8ecb6277b47`, `run_development.py` blob `fdc4f3f6e037014aadfcc3ce41b7344aa0a80b2c`.
- Perturbations are exactly the ten deterministic event-ID deletion folds already executed in PR #1265 / run `31859724335`: `uint64_be(sha256(utf8(event_id))[0:8]) mod 10`. No new folds, salts, deletion fractions or bootstrap choices are permitted.
- Only the **parent recurrent-EOM candidates** from each fold's prelabel artifact may be used. Density-synchronous successor outputs and all fold truth metrics are forbidden inputs to the ranking rule.

## Sole scientific change

Fit the exact recurrent-EOM parent once on the complete target-excluded GMN 2022+2023 development corpus, producing the immutable full-data candidate set and parent order.

For each full-data candidate `C` and each frozen fold `f`:

1. deterministically remove from `C` the event IDs assigned to fold `f`, yielding `C_f`;
2. compare `C_f` to every recurrent-EOM **parent** candidate generated on that same retained fold;
3. define `J_f(C)` as the maximum Jaccard overlap. If `C_f` is empty, fail closed.

Define

`survival(C) = mean_f J_f(C)`

and the sole successor score

`S_cv(C) = recurrent_stability(C) * survival(C)`.

Complete deterministic successor order:

1. `S_cv` descending;
2. `recurrent_stability` descending;
3. `survival` descending;
4. member count descending;
5. family ID ascending.

All full-data candidate memberships remain exact parent memberships. No threshold, learned coefficient, exponent, quantile choice, alternate overlap metric, fold weighting, route/year rule, rank fusion, diversity change, membership cleanup or post-result rescue is permitted.

## Development evaluation

Evaluation uses only the already-exposed target-excluded GMN 2022/2023 shower truth after the complete successor order is persisted and hash-frozen.

Exact parent controls must reproduce:

- 2022: recovered @25/@50/@100 = `22/45/89`, top-100 dominant precision `0.7856486012780942`, MRR `0.022498269587309373`, qualified `236`, median top-500 fragmentation `1.0`;
- 2023: recovered @25/@50/@100 = `23/46/89`, top-100 dominant precision `0.7867680236864514`, MRR `0.0220239288966045`, qualified `244`, median top-500 fragmentation `1.0`.

`PASS_RECURRENT_EOM_CV_SURVIVAL_RANK_V1_GMN_DEVELOPMENT` requires:

1. exact parent candidate membership universe preserved;
2. successor order differs from parent;
3. recovered@25, @50 and @100 are not lower in either year;
4. top-100 dominant precision is not lower in either year;
5. MRR is not lower in either year;
6. median top-500 fragmentation is not higher in either year;
7. at least one year has a strict improvement in recovered@100, top-100 precision, or MRR.

Otherwise the exact rule fails and is closed. A PASS authorizes only one separately frozen matched SonotaCo comparison; it does not authorize AMOS or any pristine endpoint.

## Firewall

Protected `[20°,55°]` remains excluded inclusively. `target_information_access=false`, `target_region_events_accessed=false`, `sonotaco_2013_2014_access=false`, `amos_2023_2024_access=false`, `asfn_access=false`, `efn_access=false`, `maarsy_scientific_access=false`, `dms_scientific_access=false` throughout selection.