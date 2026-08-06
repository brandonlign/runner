# OrbitTrace novel-methodology evaluation

## Frozen evidence

The fixed-4° coverage-normalized Mondrian anchored four-clique detector was developed and frozen without OrbitTrace access. The literature-comparison system reused the exact frozen SonotaCo episode generators, folds, calibration-negative panels, held-out negatives, positive weak-stream episodes, seeds, and metrics.

### SonotaCo 2025 episode comparison

Workflow run: `31068866741`  
Artifact: `8954882633`

| Method | Classification | Weak-stream AUROC | FPR at .05 | FPR at .01 |
|---|---|---:|---:|---:|
| fixed-4° detector | frozen candidate | 0.813250 | 0.047852 | 0.006836 |
| split statistic | internal baseline | 0.756654 | 0.044922 | 0.007324 |
| local density | internal baseline | 0.753978 | 0.018555 | 0.001465 |
| internal DBSCAN | internal baseline | 0.749487 | 0.021973 | 0.003906 |
| Sugar et al. deterministic core | literature published-core transfer | 0.508578 | 0.000000 | 0.000000 |
| Rudawska–Jenniskens D_SH, six members | literature implementation | 0.604533 | 0.040039 | 0.004883 |
| D_SH, four-member sparse adaptation | predeclared adaptation | 0.640364 | 0.048340 | 0.011719 |

### SonotaCo 2023 one-shot episode transfer

Workflow run: `31070015674`  
Artifact: `8955293144`  
Artifact digest: `sha256:e283f7baff4512161708be66b765be3ccd95e65e089fd9f13e1ec0536a31f85f`

| Method | Classification | Weak-stream AUROC | FPR at .05 | FPR at .01 |
|---|---|---:|---:|---:|
| fixed-4° detector | frozen candidate | 0.811631 | 0.050663 | 0.006629 |
| split statistic | internal baseline | 0.772837 | 0.046402 | 0.006629 |
| local density | internal baseline | 0.758780 | 0.026989 | 0.003788 |
| internal DBSCAN | internal baseline | 0.748877 | 0.023674 | 0.004261 |
| Sugar et al. deterministic core | literature published-core transfer | 0.524927 | 0.000947 | 0.000473 |
| Rudawska–Jenniskens D_SH, six members | literature implementation | 0.579954 | 0.048295 | 0.007576 |
| D_SH, four-member sparse adaptation | predeclared adaptation | 0.637606 | 0.050189 | 0.009470 |

All 15 transfer-integrity gates passed. They include exact reproduction of the previously frozen 2023 fixed-4° and internal-baseline AUROCs, unchanged transferred parameters, exact episode counts, and nonempty fold units. One retained 2023 sporadic event lacked a complete orbital solution; it remained in every episode for the fixed-4°, Sugar, and internal methods, while D_SH used a preregistered complete-case rule with at least 127 valid orbits per episode.

## Catalogue-scale HDBSCAN track

The published Peña-Asensio–Ferrari catalogue configuration was implemented separately from the episode leaderboard. It uses the unstandardized six-component GEO vector, `hdbscan==0.8.44`, `min_cluster_size=100`, package-default `min_samples`, Euclidean distance, and `eom` cluster selection. The quality filters and all clustering rules were frozen before the SonotaCo 2025 execution; the complete configuration and 2025 result were then frozen before the one-shot SonotaCo 2023 transfer.

| Corpus | Evaluation set | Events | Reference showers | Clusters | Noise fraction | NMI | ARI | Mean F1 | F1 > .5 | F1 > .8 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| SonotaCo 2025 | published-style ≥100-member reference set | 18,939 | 13 | 11 | 0.622208 | 0.747578 | 0.763809 | 0.704556 | 11 | 6 |
| SonotaCo 2023 | one-shot ≥100-member reference set | 24,991 | 13 | 13 | 0.583490 | 0.747418 | 0.745176 | 0.722911 | 11 | 9 |
| SonotaCo 2025 | all-shower coverage audit | 19,658 | 66 | 13 | 0.632821 | 0.705993 | 0.725476 | 0.151643 | 12 | 7 |
| SonotaCo 2023 | all-shower coverage audit | 25,889 | 63 | 14 | 0.593688 | 0.700714 | 0.697359 | — | 11 | 9 |

The primary HDBSCAN result transferred strongly: NMI changed from `0.747578` to `0.747418`, and 11 of 13 large reference showers exceeded F1 0.5 in both years. Under the unchanged parameters, performance was strongly size-dependent. Mean matched F1 for 100+-member showers was `0.707397` in 2025 and `0.720594` in 2023, while recovery below 50 members was zero or nearly zero in both catalogues. The 50–99-member stratum remained weak (`0.267677` and `0.174501`).

This is not evidence that the fixed-4° detector globally beats HDBSCAN. It shows that the methods address different regimes: the published HDBSCAN configuration is reproducibly effective for large catalogue populations, whereas the fixed-4° contribution is evaluated for sparse k=4–12 episodes under controlled false-positive rates. The stable HDBSCAN failure in the sparse strata strengthens the case that sparse-stream recognition is a real methodological gap rather than an artificial weakness of one comparison year.

HDBSCAN 2025 workflow: `31071589912`; artifact `8955917326`; digest `sha256:82e95052eb75349031341ea600aebf8f74d6842f03c0e47edf7cdea6de471a89`.  
HDBSCAN 2023 workflow: `31074645262`; artifact `8957004084`; digest `sha256:d6e3c2b72be25ae0ba101e977b4bbea723edb1c2dd6866e4b3540397a907ff02`.

## Comparator audit

The old internal DBSCAN comparator is not Sugar et al. It uses the project's internal four-dimensional distance, `eps=2.5`, and `min_samples=4`.

The Sugar episode comparison implemented the published six-dimensional Sun-centered geocentric vector, `min_samples=5`, and the published fourth-nearest-neighbor / 23rd-percentile epsilon rule. It is explicitly the deterministic published core. The paper's uncertainty-clone recurrence and catalogue-level cluster-merging stages remain a separate catalogue-track implementation target.

The classical orbital comparator implemented the exact Southworth–Hawkins criterion with single linkage, the published `D_SH < 0.05` threshold, and the published six-member minimum. The four-member variant was registered before scores and remains labelled an adaptation.

The published HDBSCAN catalogue configuration is now implemented and independently transferred. It remains outside the episode leaderboard because its unit of analysis, minimum cluster size, and evaluation target differ. The CMOR-style 3D wavelet method remains a separate catalogue/activity-map target whose radar-specific multi-year construction cannot be represented faithfully as a 128-event episode comparator.

## Independent judgment

**Retain the methodology as a major second OrbitTrace contribution, with a narrow and explicit claim.**

The strongest defensible result is that the frozen detector has a reproducible advantage for sparse, weak-stream episode recognition under controlled false-positive evaluation. It transferred from SonotaCo 2025 to the one-shot SonotaCo 2023 panel with almost unchanged AUROC and remained clearly above the internal baselines, a faithful classical D_SH linkage implementation, a predeclared sparse D_SH adaptation, and the deterministic core of Sugar et al.

The completed HDBSCAN track adds an important boundary rather than a direct victory claim. HDBSCAN transferred robustly for large catalogue showers but recovered almost nothing in the sub-50-member strata under its unchanged published configuration. This supports the fixed-4° detector as a complementary sparse-regime contribution while preserving HDBSCAN's demonstrated strength for large catalogue populations.

This comparison does not erase the frozen k=4 alpha=.01 replication failure or the calibration-seed robustness failure. The general-method conclusion therefore remains: **promising strong transfer, but not fully robustly replicated under the complete preregistered standard.**

The frozen OrbitTrace application remains an independent targeted recovery. It is strong evidence that the detector recognizes the OrbitTrace structure, but it is not the original discovery method and not a blind catalogue rediscovery.

The methodology is not yet ready for a separate technical paper. The most important remaining comparator is the complete uncertainty-aware Sugar catalogue pipeline. A CMOR-style wavelet transfer would also broaden the catalogue track, but its radar-specific multi-year activity-map design makes a faithful optical-catalogue transfer less direct. A fresh independent survey catalogue would still be required for a standalone methods paper.

## Allowed manuscript claim

> An independently developed and frozen sparse-stream detector recovered the OrbitTrace structure under a targeted protocol and showed reproducible discrimination of weak SonotaCo stream episodes across development and one-shot transfer benchmarks. On the identical episode benchmark, it outperformed the project's internal split, density, and DBSCAN baselines, a classical Southworth–Hawkins single-linkage implementation, and the deterministic published core of the Sugar et al. DBSCAN pipeline. A separately implemented published HDBSCAN configuration transferred robustly for large catalogue showers but showed negligible recovery in sub-50-member reference strata under unchanged parameters, supporting the detector as a complementary sparse-stream recognition method rather than a replacement for established catalogue-scale clustering.

## Prohibited claims

- “OrbitTrace was discovered by the novel detector.”
- “The detector blindly rediscovered OrbitTrace from the full catalogue.”
- “The detector beat the complete Sugar et al. pipeline.”
- “The detector beat HDBSCAN globally.”
- “The detector beat CMOR wavelet discovery.”
- “The detector is the best general meteor-stream discovery method.”
- “The detector fully passed its complete independent-validation standard.”
