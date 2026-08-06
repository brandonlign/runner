# Sugar uncertainty-aware catalogue reconstruction: final evaluation

## Scope and status

The full catalogue stages described by Sugar et al. (2017) are now implemented and transferred across two SonotaCo years. This is no longer an unimplemented comparator.

The implementation retains the published six-component Sun-centered geocentric vector, `min_samples=5`, the fourth-nearest-neighbor / 23rd-percentile epsilon rule, 1,000 uncertainty-clone catalogues, the stated 50%-of-one-cluster overlap criterion, and the stated 100/1,000 and 500/1,000 recurrence levels. SonotaCo supplies marginal RA, Dec, and geocentric-speed uncertainties rather than the original ASGARD covariance model. Because the paper did not publish software or a merge order, overlap merging is a preregistered deterministic connected-component reconstruction. It must be described as a faithful published-stage survey transfer, not an exact software reproduction.

SonotaCo 2025 was the sole development catalogue. The complete source, epsilon, clone rules, merge implementation, recurrence rules, package version, and result were frozen before SonotaCo 2023 access. The 2023 run reused the numeric 2025 epsilon rather than recalculating or tuning it on the target year.

## Frozen executions

### SonotaCo 2025 development catalogue

- Workflow: `31075178517`
- Artifact: `8957263372`
- Artifact digest: `sha256:9df4a48f4808180d534086e560e68ae56486f60171510207acd7bd6fedeebbc9`
- Result SHA-256: `e65f09c453f30c64649314554ab44fc878ac8da4b4c726c6c79254b9717d909a`
- Verdict: `PASS_SONOTACO_2025_SUGAR_UNCERTAINTY_CATALOGUE_TRANSFER`

### SonotaCo 2023 one-shot transfer

- Workflow: `31076789635`
- Artifact: `8957940764`
- Artifact digest: `sha256:ea77c5111a7be51ff2bb45b16df934f7c808c695d08ac12003025de971df4fdf`
- Result SHA-256: `16b14829d0611adcbf76154e37b673b47cda8568eee76fb02351c1de77c6d2ed`
- Exact transfer-runner SHA-256: `2013ffc91cc299da1635ddd0cc728b460aebf030671ea0a83b7ddce4632a39a8`
- Exact reused core SHA-256: `5b7699a2cf07b9b9ac6dee006c66a9b509af73ee3763093fa333d13e1deca0cb`
- Verdict: `PASS_SONOTACO_2023_SUGAR_UNCERTAINTY_TRANSFER`

Every frozen parser, archive, source, epsilon, package-version, clone-count, merge, recurrence, assignment, and finite-metric gate passed.

## Catalogue-level results

| Corpus | Assignment | Events | Clusters | Noise fraction | NMI | ARI | Showers F1>.5 | Showers F1>.8 | Macro F1 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2025 | observed deterministic DBSCAN | 23,200 | 64 | 0.743017 | 0.708278 | 0.758080 | 19 | 8 | 0.222874 |
| 2025 | retained masters, >=100/1000 | 23,200 | 49 | 0.693707 | 0.751013 | 0.822827 | 23 | 13 | 0.272161 |
| 2025 | strong masters, >=500/1000 | 23,200 | 42 | 0.696767 | 0.746935 | 0.818488 | 20 | 10 | 0.229026 |
| 2023 | observed deterministic DBSCAN | 30,414 | 76 | 0.716578 | 0.741348 | 0.789165 | 20 | 10 | 0.274484 |
| 2023 | retained masters, >=100/1000 | 30,414 | 64 | 0.666930 | 0.784491 | 0.840575 | 26 | 15 | 0.335589 |
| 2023 | strong masters, >=500/1000 | 30,414 | 51 | 0.671664 | 0.779777 | 0.833580 | 23 | 15 | 0.290143 |

The uncertainty-aware retained-master assignment improved on one deterministic DBSCAN catalogue in both years. Relative to deterministic DBSCAN, NMI increased by `0.042735` in 2025 and `0.043143` in 2023; ARI increased by `0.064747` and `0.051410`; and the number of reference showers above matched F1 0.5 increased by four and six, respectively. This shows that the uncertainty-clone, overlap, and recurrence stages materially matter.

The transfer was not merely qualitative. The retained-master reconstruction remained strong on the one-shot year despite using the 2025 epsilon `0.028705145052265017`, while the target-year 23rd-percentile diagnostic would have been `0.024028623902096407`. No target-year substitution was made.

## Size-regime results

### Retained master clusters, >=100/1000 recurrence

| Annual reference size | 2025 showers | 2025 mean F1 | 2025 F1>.5 | 2023 showers | 2023 mean F1 | 2023 F1>.5 |
|---|---:|---:|---:|---:|---:|---:|
| 4–9 | 27 | 0.030864 | 1 | 25 | 0.030000 | 1 |
| 10–24 | 14 | 0.239926 | 4 | 18 | 0.400187 | 8 |
| 25–49 | 11 | 0.258805 | 3 | 7 | 0.147353 | 1 |
| 50–99 | 4 | 0.406617 | 2 | 6 | 0.619602 | 4 |
| 100+ | 13 | 0.777964 | 13 | 15 | 0.741625 | 12 |

The central boundary is stable. At 4–9 annual members, only one shower exceeded F1 0.5 in each catalogue and mean F1 was approximately `0.03`. At 100+ members, mean F1 was `0.777964` and `0.741625`, with 25 of 28 combined large-shower populations above F1 0.5.

This does not prove that fixed4 beats the full Sugar pipeline on the same task. The catalogue reconstruction and sparse-episode benchmark have different units, labels, and metrics. It does show independently that the complete Sugar uncertainty stages remain optimized for catalogue populations rather than reliable four-to-nine-member recognition, which is the regime targeted by fixed4.

## Scientific effect on the OrbitTrace methodology claim

The full Sugar implementation removes the largest previously unfinished literature comparator. It strengthens, rather than overturns, the current judgment:

- Sugar's uncertainty-aware stages are genuinely useful and should not be dismissed based on the weak deterministic episode-core result.
- The reconstructed pipeline transfers well at catalogue scale and performs strongly for large showers.
- Its recovery remains extremely weak in the 4–9-member annual stratum across both years.
- Fixed4 therefore remains defensible as a complementary sparse-stream recognition contribution, not as a universal replacement for Sugar, HDBSCAN, or survey discovery methods.

The independent judgment remains: **retain fixed4 as a major second OrbitTrace contribution, narrowly claimed as sparse weak-stream recognition under controlled false-positive evaluation.**

The general-method conclusion also remains unchanged: **promising strong transfer, but not fully robustly replicated under the complete preregistered standard.** The completed literature track does not erase fixed4's frozen k=4 alpha=.01 replication failure or calibration-seed robustness failure.

## Updated allowed claim

> An independently developed and frozen detector showed reproducible discrimination of sparse SonotaCo stream episodes and recovered the OrbitTrace structure under a separate targeted protocol. On the identical sparse-episode benchmark, it exceeded internal split, density, and DBSCAN baselines; classical D_SH and D_N linkage variants; and the deterministic published core of Sugar et al. in overall weak-stream AUROC. Separately reconstructed catalogue-scale HDBSCAN and uncertainty-aware Sugar pipelines transferred effectively for large and moderate shower populations but showed little reliable recovery in the smallest annual size strata under unchanged frozen rules. These results support fixed4 as a complementary sparse-stream recognition method, not as the historical OrbitTrace discovery procedure or a universal replacement for established catalogue pipelines.

## Prohibited claims

- The detector discovered OrbitTrace historically.
- The targeted OrbitTrace recovery was a blind full-catalogue rediscovery.
- Fixed4 beat the complete Sugar pipeline on Sugar's catalogue task.
- Fixed4 beat HDBSCAN on HDBSCAN's catalogue task.
- Fixed4 is the best general meteor-stream method.
- The Sugar reconstruction is an exact reproduction of unpublished ASGARD software or covariance.
- Fixed4 fully passed every preregistered independent-validation gate.
