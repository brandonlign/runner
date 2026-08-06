# OrbitTrace literature-comparator coverage completion

## Final coverage judgment

The comparison program now covers the major method families that can be evaluated fairly with the available public SonotaCo data. No major comparable family is silently omitted.

Two scientific tasks remain separated:

1. **Sparse-episode recognition:** identical 128-event windows, empirical null calibration, held-out negatives, and k=4/6/8/12 positive episodes.
2. **Catalogue-scale discovery or classification:** complete annual catalogues or preregistered multiyear survey inputs using each published method’s natural unit.

Catalogue results are not substituted for episode results, and episode results are not described as blind catalogue rediscovery.

## Episode-track methods

| Method | Role | 2025 AUROC | 2023 AUROC | Prospective 2022 AUROC |
|---|---|---:|---:|---:|
| fixed-4° anchored four-clique | novel frozen topology-based candidate | 0.813250 | 0.811631 | 0.791405 |
| Brown-family 3D wavelet episode core | literature-inspired episode adaptation | **0.828506** | **0.831972** | **0.820936** |
| fixed4-wavelet Tippett hybrid | post-comparison ensemble | 0.835878* | — | 0.815525 |
| internal split statistic | internal baseline | 0.756654 | 0.772837 | — |
| internal local-density statistic | internal baseline | 0.753978 | 0.758780 | — |
| internal four-dimensional DBSCAN | internal baseline; not Sugar et al. | 0.749487 | 0.748877 | — |
| Sugar deterministic published core | literature DBSCAN core | 0.508578 | 0.524927 | — |
| Southworth–Hawkins D_SH, M=6 | classical orbital comparator | 0.604533 | 0.579954 | — |
| D_SH sparse adaptation, M=4 | predeclared adaptation | 0.640364 | 0.637606 | — |
| Valsecchi–Jopek–Froeschlé D_N, M=6 | classical geocentric comparator | 0.731316 | 0.714395 | — |
| D_N sparse transfer, M=4 | predeclared sparse transfer | 0.759251 | 0.746209 | — |

`*` The hybrid’s 2025 result is retrospective development evidence. Its scientific decision was based only on the prospectively frozen SonotaCo 2022 test.

### Revised ordering

The wavelet episode adaptation exceeded fixed4 in overall weak-stream AUROC in all three years:

- 2025: 0.828506 versus 0.813250;
- one-shot 2023: 0.831972 versus 0.811631;
- prospective 2022: 0.820936 versus 0.791405.

This ordering is reproducible. fixed4 is therefore not the best overall episode discriminator tested.

The methods are complementary rather than redundant. At alpha .05, fixed4 retained the highest four-member recall in all three years. The wavelet was stronger for moderate-member episodes. On prospective 2022, recall for k=4/6/8/12 was:

- fixed4: 0.171053 / 0.401316 / 0.585526 / 0.815789;
- wavelet: 0.092105 / 0.421053 / 0.703947 / 0.921053;
- hybrid: 0.131579 / 0.447368 / 0.723684 / 0.947368.

## Frozen hybrid decision

One unweighted Tippett union was specified before any hybrid score was calculated. It combines bin-calibrated component p-values and is itself recalibrated using leave-one-out hybrid null statistics. No alternative combiner or learned weight was tested.

On prospective SonotaCo 2022:

| Method | Weak AUROC | Balanced alpha-.05 recall | FPR alpha .05 |
|---|---:|---:|---:|
| fixed4 | 0.791405 | 0.493421 | 0.040246 |
| wavelet | **0.820936** | 0.534539 | **0.039299** |
| hybrid | 0.815525 | **0.562500** | 0.040720 |

The hybrid failed its promotion gate because it did not exceed the wavelet’s AUROC. It received the frozen decision **`RETAIN_AS_OPTIONAL_ENSEMBLE`** because it delivered the highest balanced recall, the highest k=6/8/12 recall, and recall no lower than both components at any tested k.

## Catalogue-track methods

### Published HDBSCAN configuration

The Peña-Asensio–Ferrari GEO-vector HDBSCAN configuration was transferred unchanged across SonotaCo 2025 and 2023. It remained strong for large catalogue populations and showed zero or nearly zero recovery below 50 annual members.

### Full uncertainty-aware Sugar reconstruction

The complete published-stage Sugar reconstruction used 1,000 uncertainty-clone catalogues, the six-dimensional GEO vector, frozen epsilon, stated overlap rule, and recurrence thresholds. Uncertainty handling improved catalogue assignment in both 2025 and 2023, while mean retained-master F1 for 4–9 annual members remained about 0.03.

### Full CMOR-style wavelet survey

The full catalogue-survey implementation remains formally deferred, not beaten. A seven-year SonotaCo stack contained 178,188 retained events, but only 199/324 available one-degree bins—61.4%—reached the published 300-radiant necessary floor, below the frozen 80% support requirement. No full-survey coefficient or detection endpoint was computed.

The successful wavelet **episode adaptation** is a separate benchmark method and must not be represented as a faithful reproduction of the global CMOR survey.

## Other method families

Additional Drummond-, Jopek-, and related D-functions were not individually added after results because D_SH and D_N already span the principal orbital-element versus geocentric-observable distinction, while many variants require database-specific chance thresholds. Adding correlated variants after observing the leaderboard would create method shopping.

KDE false-positive estimation is an ancillary association-significance framework rather than a blind detector. Known-shower lookup, parent-body association, and supervised classifiers without a comparable frozen training protocol are likewise not omitted discovery algorithms.

## Completion decision

The literature-comparator development phase is complete for the current data.

The repository now records:

- **14 registered methods**;
- **11 episode methods**;
- **3 catalogue-family outcomes**;
- a prospectively validated wavelet ordering;
- a prospectively evaluated hybrid with a frozen optional-ensemble decision.

Further progress requires new independent survey data or a denser exposure-controlled catalogue, not post-result scale, weight, threshold, or D-criterion changes.

## Final independent judgment

The methodological claim must be revised rather than discarded.

- **Wavelet episode adaptation:** strongest overall sparse-episode discriminator tested by reproducible AUROC.
- **fixed4:** novel ultra-sparse topology-based component with consistently superior four-member recall, independent targeted OrbitTrace recovery, and value inside a complementary framework.
- **Tippett hybrid:** optional high-recall ensemble, not the primary discriminator.

fixed4 remains a meaningful methodological contribution, but it should no longer be presented as outperforming every implemented method. The stronger framing is a **multi-regime sparse-stream analysis**: a novel four-clique detector for the hardest ultra-sparse regime, benchmarked against a stronger literature-inspired wavelet method for moderate-member episodes.

The fixed4-specific conclusion remains:

> **Promising strong transfer and useful ultra-sparse complement, but not fully robustly replicated under the complete preregistered standard.**
