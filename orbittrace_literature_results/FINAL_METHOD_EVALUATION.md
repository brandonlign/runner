# OrbitTrace novel-methodology evaluation

## Frozen evidence

The fixed-4° coverage-normalized Mondrian anchored four-clique detector was developed and frozen without OrbitTrace access. The comparison system reused the exact frozen SonotaCo episode generators, folds, calibration-negative panels, held-out negatives, positive weak-stream episodes, seeds, and metrics. Methods designed for full survey catalogues were evaluated separately on a catalogue track rather than forced into the 128-event sparse-episode leaderboard.

## Episode-track results

### SonotaCo 2025 development comparison

Primary workflow: `31068866741`, artifact `8954882633`  
D_N extension: workflow `31073086886`, artifact `8956382792`

| Method | Classification | Weak-stream AUROC | FPR at .05 | FPR at .01 |
|---|---|---:|---:|---:|
| fixed-4° detector | frozen candidate | 0.813250 | 0.047852 | 0.006836 |
| split statistic | internal baseline | 0.756654 | 0.044922 | 0.007324 |
| local density | internal baseline | 0.753978 | 0.018555 | 0.001465 |
| internal DBSCAN | internal baseline | 0.749487 | 0.021973 | 0.003906 |
| Sugar et al. deterministic core | literature published-core transfer | 0.508578 | 0.000000 | 0.000000 |
| Rudawska–Jenniskens D_SH, six members | literature implementation | 0.604533 | 0.040039 | 0.004883 |
| D_SH, four-member sparse adaptation | predeclared adaptation | 0.640364 | 0.048340 | 0.011719 |
| Valsecchi–Jopek–Froeschlé D_N, six members | published distance/linkage evaluated at M=6 | 0.731316 | 0.046875 | 0.005371 |
| D_N, four-member sparse transfer | predeclared sparse transfer | 0.759251 | 0.045898 | 0.007324 |

### SonotaCo 2023 one-shot transfer

Primary workflow: `31070015674`, artifact `8955293144`  
D_N extension: workflow `31074254968`, artifact `8956855273`  
D_N artifact digest: `sha256:fb9f5e37c5efed148c21dd49f0f44be00385f27182043dac3317ec5a520617b9`

| Method | Classification | Weak-stream AUROC | FPR at .05 | FPR at .01 |
|---|---|---:|---:|---:|
| fixed-4° detector | frozen candidate | 0.811631 | 0.050663 | 0.006629 |
| split statistic | internal baseline | 0.772837 | 0.046402 | 0.006629 |
| local density | internal baseline | 0.758780 | 0.026989 | 0.003788 |
| internal DBSCAN | internal baseline | 0.748877 | 0.023674 | 0.004261 |
| Sugar et al. deterministic core | literature published-core transfer | 0.524927 | 0.000947 | 0.000473 |
| Rudawska–Jenniskens D_SH, six members | literature implementation | 0.579954 | 0.048295 | 0.007576 |
| D_SH, four-member sparse adaptation | predeclared adaptation | 0.637606 | 0.050189 | 0.009470 |
| Valsecchi–Jopek–Froeschlé D_N, six members | published distance/linkage evaluated at M=6 | 0.714395 | 0.040720 | 0.007102 |
| D_N, four-member sparse transfer | predeclared sparse transfer | 0.746209 | 0.047822 | 0.008523 |

The independent ordering is stable. Fixed4 changed from 0.813250 to 0.811631; D_N at M=6 changed from 0.731316 to 0.714395; and the sparse D_N transfer changed from 0.759251 to 0.746209. D_N at M=4 is the strongest classical sparse comparator tested, while fixed4 retains an AUROC advantage of approximately 0.054 in 2025 and 0.065 in 2023.

The advantage is not uniform at every operating point. D_N at M=6 slightly exceeds fixed4 for k=12 recall at alpha .05 in both years, and some internal baselines also exceed fixed4 at selected high-k or strict-alpha points. The defensible claim is stronger overall weak-stream discrimination, not universal dominance.

## Catalogue-track HDBSCAN reproduction

The published Peña-Asensio–Ferrari GEO-vector HDBSCAN configuration was reproduced separately with the unstandardized six-component GEO vector, Euclidean distance, `min_cluster_size=100`, default `min_samples`, and `eom` selection. The existing 20°–55° blind interval remained removed before label access, so neither catalogue run inspected or scored OrbitTrace.

### SonotaCo 2025

Workflow `31071589912`, artifact `8955917326`, digest `sha256:82e95052eb75349031341ea600aebf8f74d6842f03c0e47edf7cdea6de471a89`.

- 18,939 quality-filtered events and 13 reference showers retaining at least 100 events;
- 11 HDBSCAN clusters;
- NMI 0.747578 and ARI 0.763809;
- 11/13 showers with matched F1 above 0.5 and 6/13 above 0.8;
- mean matched shower F1 0.704556.

In the identical-parameter all-label coverage audit, mean F1 by annual shower size was 0.000000 for 4–9, 0.000000 for 10–24, 0.030769 for 25–49, 0.267677 for 50–99, and 0.707397 for 100+ members.

### SonotaCo 2023 one-shot transfer

Workflow `31072548443`, artifact `8956177186`, digest `sha256:230319166d2de757fbe709eecb0d904f258f0e45a93c8dcdd31c104f05c38169`.

- 24,923 quality-filtered events and 14 reference showers retaining at least 100 events;
- 13 HDBSCAN clusters;
- NMI 0.743023 and ARI 0.745363;
- 11/14 showers with matched F1 above 0.5 and 8/14 above 0.8;
- mean matched shower F1 0.651696.

The identical-parameter all-label audit produced mean F1 of 0.000000 for 4–9, 0.005310 for 10–24, 0.000000 for 25–49, 0.174118 for 50–99, and 0.649272 for 100+ members.

These results validate HDBSCAN as a strong large-shower catalogue method and independently demonstrate the structural consequence of transferring its published 100-member minimum to sparse annual showers. This is evidence of task complementarity, not evidence that fixed4 beat HDBSCAN on HDBSCAN's intended catalogue task.

## Comparator audit

The internal DBSCAN comparator is not Sugar et al. It uses the project's internal four-dimensional distance, `eps=2.5`, and `min_samples=4`.

The Sugar episode comparison implemented the published six-dimensional Sun-centered geocentric vector, `min_samples=5`, and the published fourth-nearest-neighbor / 23rd-percentile epsilon rule. It remains explicitly the deterministic published core. The paper's 1,000 uncertainty-clone recurrence and catalogue-level cluster-merging stages remain unimplemented.

The classical orbital comparator implemented the exact Southworth–Hawkins criterion with single linkage, the published `D_SH < 0.05` threshold, and the published six-member minimum. Its four-member variant was registered before scores and remains labelled an adaptation.

The D_N comparator implemented the published geocentric variables derived from right ascension, declination, geocentric speed, and solar longitude; Earth-speed normalization at 29.7 km/s; unit weights; the direct-versus-180° twin-node angular branch; and single-neighbour linkage. The original application used sample- and membership-specific chance-threshold simulations. Those simulations were not claimed as reproduced: the episode benchmark instead evaluated continuous single-link birth thresholds under the same empirical negative calibration used for every comparator. The M=4 result remains a predeclared sparse transfer, not a published four-member pipeline.

The HDBSCAN catalogue comparison is now complete across 2025 development and one-shot 2023 transfer. A CMOR-style 3D wavelet survey remains on the catalogue track because its published unit is a multi-year activity map, not isolated 128-event episodes.

## Independent judgment

**Retain the methodology as a major second OrbitTrace contribution, with a narrow and explicit claim.**

The strongest defensible result is that the frozen detector has a reproducible advantage for sparse, weak-stream episode recognition under controlled false-positive evaluation. It transferred from SonotaCo 2025 to the one-shot SonotaCo 2023 panel with almost unchanged AUROC and remained above all implemented internal baselines, classical D_SH variants, both D_N episode variants, and the deterministic published core of Sugar et al.

The completed HDBSCAN track strengthens the framing rather than creating a head-to-head victory claim. Published HDBSCAN performed well for large showers and poorly for sub-50-member annual showers under unchanged parameters, confirming that fixed4 targets a different sparse-recognition regime.

This evidence does not erase the frozen k=4 alpha=.01 replication failure or the calibration-seed robustness failure. The general-method conclusion therefore remains: **promising strong transfer, but not fully robustly replicated under the complete preregistered standard.**

The frozen OrbitTrace application remains an independent targeted recovery. It is strong evidence that the detector recognizes the OrbitTrace structure, but it is not the original discovery method and not a blind catalogue rediscovery.

The methodology is still not ready for a separate technical paper. The most important unfinished literature implementation is the full uncertainty-aware Sugar pipeline. A CMOR-style wavelet catalogue comparison and a fresh independent survey catalogue would further strengthen a standalone methods paper. Those additions are not required to justify the method as a major second contribution in the OrbitTrace paper, because the present contribution is explicitly sparse-episode recognition rather than universal catalogue discovery.

## Allowed manuscript claim

> An independently developed and frozen sparse-stream detector recovered the OrbitTrace structure under a targeted protocol and showed reproducible discrimination of weak SonotaCo stream episodes across development and one-shot transfer benchmarks. On the identical episode benchmark, it outperformed the project's internal split, density, and DBSCAN baselines; classical Southworth–Hawkins linkage; Valsecchi–Jopek–Froeschlé D_N linkage; and the deterministic published core of the Sugar et al. DBSCAN pipeline in overall weak-stream AUROC. A separate reproduction of published catalogue-scale HDBSCAN showed strong recovery of large showers but little recovery of sparse annual showers under unchanged parameters, supporting the detector as a complementary sparse-stream recognition method rather than a universal catalogue replacement. The detector was not the historical OrbitTrace discovery procedure, and its targeted OrbitTrace recovery is not a blind catalogue rediscovery.

## Prohibited claims

- “OrbitTrace was discovered by the novel detector.”
- “The detector blindly rediscovered OrbitTrace from the full catalogue.”
- “The detector beat the complete uncertainty-aware Sugar et al. pipeline.”
- “The detector beat HDBSCAN on HDBSCAN's intended catalogue task.”
- “The detector beat CMOR wavelet discovery.”
- “The detector is the best general meteor-stream discovery method.”
- “The detector was uniformly superior at every stream strength and operating point.”
- “The detector fully passed its complete independent-validation standard.”
