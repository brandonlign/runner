# OrbitTrace novel-methodology evaluation

## Frozen evidence

The fixed-4° coverage-normalized Mondrian anchored four-clique detector was developed and frozen without OrbitTrace access. The literature-comparison system reused the exact frozen SonotaCo episode generators, folds, calibration-negative panels, held-out negatives, positive weak-stream episodes, seeds, and metrics.

### SonotaCo 2025 development comparison

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

### SonotaCo 2023 one-shot transfer

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

## Comparator audit

The old internal DBSCAN comparator is not Sugar et al. It uses the project's internal four-dimensional distance, `eps=2.5`, and `min_samples=4`.

The Sugar comparison implemented the published six-dimensional Sun-centered geocentric vector, `min_samples=5`, and the published fourth-nearest-neighbor / 23rd-percentile epsilon rule. It is explicitly the deterministic published core. The paper's 1,000 uncertainty-clone recurrence and catalogue-level cluster-merging stages remain a separate catalogue-track implementation target.

The classical orbital comparator implemented the exact Southworth–Hawkins criterion with single linkage, the published `D_SH < 0.05` threshold, and the published six-member minimum. The four-member variant was registered before scores and remains labelled an adaptation.

Published HDBSCAN and CMOR-style 3D wavelet methods remain on the separate catalogue track. Their published unit of analysis is a large catalogue or multi-year activity map, not a 128-event k=4–12 episode. Forcing their catalogue hyperparameters into the episode leaderboard would not be a faithful comparison.

## Independent judgment

**Retain the methodology as a major second OrbitTrace contribution, with a narrow and explicit claim.**

The strongest defensible result is that the frozen detector has a reproducible advantage for sparse, weak-stream episode recognition under controlled false-positive evaluation. It transferred from SonotaCo 2025 to the one-shot SonotaCo 2023 panel with almost unchanged AUROC and remained clearly above the internal baselines, a faithful classical D_SH linkage implementation, a predeclared sparse D_SH adaptation, and the deterministic core of Sugar et al.

This comparison does not erase the frozen k=4 alpha=.01 replication failure or the calibration-seed robustness failure. The general-method conclusion therefore remains: **promising strong transfer, but not fully robustly replicated under the complete preregistered standard.**

The frozen OrbitTrace application remains an independent targeted recovery. It is strong evidence that the detector recognizes the OrbitTrace structure, but it is not the original discovery method and not a blind catalogue rediscovery.

The methodology is not yet ready for a separate technical paper. That would require a completed catalogue-scale track, especially the uncertainty-aware Sugar pipeline, the published HDBSCAN catalogue configurations, and a CMOR-style wavelet implementation, followed by a fresh independent catalogue. Those tasks are not required to justify the methodology as a major second contribution in the OrbitTrace paper, because the present contribution is explicitly sparse-episode detection rather than universal catalogue discovery.

## Allowed manuscript claim

> An independently developed and frozen sparse-stream detector recovered the OrbitTrace structure under a targeted protocol and showed reproducible discrimination of weak SonotaCo stream episodes across development and one-shot transfer benchmarks. On the identical episode benchmark, it outperformed the project's internal split, density, and DBSCAN baselines, a classical Southworth–Hawkins single-linkage implementation, and the deterministic published core of the Sugar et al. DBSCAN pipeline. These results support the detector as a complementary sparse-stream recognition method, not as the original OrbitTrace discovery procedure or a demonstrated blind catalogue-wide replacement for existing survey pipelines.

## Prohibited claims

- “OrbitTrace was discovered by the novel detector.”
- “The detector blindly rediscovered OrbitTrace from the full catalogue.”
- “The detector beat the complete Sugar et al. pipeline.”
- “The detector beat published HDBSCAN or CMOR wavelet discovery methods.”
- “The detector is the best general meteor-stream discovery method.”
- “The detector fully passed its complete independent-validation standard.”
