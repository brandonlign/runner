# OrbitTrace literature-comparator coverage completion

## Final coverage judgment

The comparison program covers the major method families that can be evaluated fairly with the available public SonotaCo data. No major comparable family is silently omitted.

Two scientific tasks remain explicitly separate:

1. **Sparse-episode recognition:** identical 128-event windows, identical negatives, empirical false-positive calibration, and k=4/6/8/12 positive episodes.
2. **Catalogue-scale discovery or classification:** complete annual catalogues or preregistered multiyear survey inputs, using each published method's natural unit of analysis.

Results from one track are not substituted for the other.

## Implemented episode-track methods

| Method | Scientific role | 2025 weak AUROC | 2023 weak AUROC | Status |
|---|---|---:|---:|---|
| Brown-family 3D wavelet episode core | literature-inspired episode adaptation | **0.828506** | **0.831972** | complete |
| fixed-4° coverage-normalized anchored four-clique | frozen candidate | 0.813250 | 0.811631 | complete |
| D_N, M=4 sparse benchmark transfer | predeclared sparse transfer | 0.759251 | 0.746209 | complete |
| internal split statistic | internal baseline | 0.756654 | 0.772837 | complete |
| internal local-density statistic | internal baseline | 0.753978 | 0.758780 | complete |
| internal four-dimensional DBSCAN | internal baseline; not Sugar et al. | 0.749487 | 0.748877 | complete |
| Valsecchi–Jopek–Froeschlé D_N, M=6 | geocentric-observable classical comparator | 0.731316 | 0.714395 | complete |
| D_SH four-member sparse adaptation | predeclared adaptation | 0.640364 | 0.637606 | complete |
| Southworth–Hawkins D_SH, six-member single linkage | classical orbital-element comparator | 0.604533 | 0.579954 | complete |
| Sugar et al. deterministic published core | literature DBSCAN core | 0.508578 | 0.524927 | complete |

The wavelet episode core now has the highest overall weak-stream AUROC in both years. Fixed4 is not the overall benchmark leader, but it retains the stronger four-member recall and generally tighter false-positive control. The two methods are complementary rather than one uniformly dominating the other.

A paired cluster bootstrap used 20,000 replicates, resampling positive episodes by shower-complex unit and negatives by Mondrian bin. Wavelet-minus-fixed4 AUROC was +0.0153 in 2025 and +0.0203 in 2023. The equal-weight combined estimate was +0.0178 with 95% interval [−0.0043, +0.0406] and P(difference > 0)=0.9399. The direction replicated, but the interval crossed zero, so the advantage is consistent rather than statistically decisive.

At α=.05, fixed4 versus wavelet k=4 recall was 0.154 versus 0.081 in 2025 and 0.189 versus 0.134 in 2023. For k=6–12, the wavelet core was generally stronger, especially at α=.01.

The wavelet episode result is separately labelled. It uses the published Brown-family three-dimensional Mexican-hat kernel, a 4° angular probe, a 10% speed probe, leave-one-out coefficients at observed events, and the maximum coefficient as the episode score. It is not the full CMOR catalogue survey.

## Implemented catalogue-track methods

### Published HDBSCAN configuration

The Peña-Asensio–Ferrari GEO-vector HDBSCAN configuration was implemented with `hdbscan==0.8.44`, `min_cluster_size=100`, package-default `min_samples`, Euclidean distance, and `eom` selection. It transferred from SonotaCo 2025 to a one-shot SonotaCo 2023 catalogue.

| Corpus | Primary NMI | Primary ARI | Mean matched F1 | Reference showers F1>.5 |
|---|---:|---:|---:|---:|
| 2025 | 0.747578 | 0.763809 | 0.704556 | 11/13 |
| 2023 | 0.747418 | 0.745176 | 0.722911 | 11/13 |

HDBSCAN was reproducibly effective for large catalogue populations and showed zero or nearly zero recovery below 50 annual members under unchanged parameters.

### Full uncertainty-aware Sugar reconstruction

The complete published-stage Sugar pipeline was reconstructed with the six-dimensional GEO vector, transferred 2025 epsilon, `min_samples=5`, 1,000 uncertainty-clone catalogues, the stated 50% overlap rule, deterministic connected-component merge operationalization, and recurrence thresholds of 100/1,000 and 500/1,000. The same successful core and frozen 2025 epsilon were transferred once to 2023.

| Corpus | Assignment | NMI | ARI | Reference showers F1>.5 | Macro F1 |
|---|---|---:|---:|---:|---:|
| 2025 | deterministic observed DBSCAN | 0.708278 | 0.758080 | 19 | 0.222874 |
| 2025 | retained uncertainty masters | 0.751013 | 0.822827 | 23 | 0.272161 |
| 2023 | deterministic observed DBSCAN | 0.741348 | 0.789165 | 20 | 0.274484 |
| 2023 | retained uncertainty masters | 0.784491 | 0.840575 | 26 | 0.335589 |

The uncertainty stages materially improved the catalogue result in both years. Mean retained-master F1 for annual 4–9-member showers remained approximately 0.03, while large-shower performance was strong.

## Full CMOR wavelet survey status

The full Brown et al. CMOR-style catalogue survey remains formally deferred rather than beaten.

A seven-year SonotaCo virtual-year input audit used 178,188 retained events from 2019–2025 and passed multiyear continuity, single-year-dominance, and temporal-chain gates. Only **199/324 = 61.4%** of usable one-degree bins met the published 300-radiant necessary floor, below the frozen 80% breadth requirement.

Running only supported seasons, enlarging bins, lowering the floor, shortening chains, or using known coordinates would change the published survey task after seeing the data. The full optical survey transfer therefore remains deferred for incompatible input. This does not conflict with the successful sparse-episode wavelet adaptation because the two evaluations use different natural units and claims.

## Other D-criteria and noncomparators

Additional Drummond-, Jopek-, and related D-functions were not individually added after results. D_SH and D_N already represent the principal orbital-element versus geocentric-observable distinction, while further correlated variants require database-specific thresholds and would risk method shopping.

KDE false-positive estimation remains an ancillary significance framework rather than a blind detector. Known-shower lookup, parent-body association, pure dynamical integration, and supervised classifiers without a comparable fixed training protocol are also excluded from the discovery leaderboard.

## Current completion state

All comparator executions and the paired uncertainty analysis are complete for the current public inputs.

Further independent method development requires a new survey or exposure-controlled external catalogue, not additional post-result variants.

## Revised independent judgment

Fixed4 should remain a major OrbitTrace methodological contribution, but its role must be stated more narrowly than before:

- it is an independently developed extreme-sparse recognition method;
- it has the best four-member recall of the two leading methods;
- it generally provides tighter false-positive control;
- it performed a frozen targeted OrbitTrace recovery;
- it is **not** the strongest overall sparse-episode benchmark method.

The Brown-family wavelet adaptation has the strongest overall episode point estimates currently implemented, but paired uncertainty does not establish a decisive difference from fixed4. This does not change the historical structure of the project:

`exploratory HDBSCAN candidate discovery → independent methodological recognition tests → observational validation`.

Fixed4 did not historically discover OrbitTrace, did not robustly rediscover it under every blind catalogue wrapper, and did not fully pass every preregistered robustness gate. Its general conclusion remains:

> **Promising strong transfer, but not fully robustly replicated under the complete preregistered standard.**
