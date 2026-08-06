# OrbitTrace literature-comparator coverage completion

## Final coverage judgment

The comparison program now covers the major method families that can be evaluated fairly with the available public SonotaCo data. No major comparable family is silently omitted.

The implemented system intentionally separates two different scientific tasks:

1. **Sparse-episode recognition:** identical 128-event windows, identical negatives, empirical false-positive calibration, and k=4/6/8/12 positive episodes.
2. **Catalogue-scale discovery or classification:** complete annual catalogues or preregistered multiyear survey inputs, using the published method's natural unit of analysis.

Results from one track are not substituted for the other. A catalogue method is not declared inferior because it cannot operate as a four-member episode detector, and fixed4 is not declared superior on a catalogue task it was not tested on.

## Implemented episode-track methods

| Method | Scientific role | 2025 weak AUROC | 2023 weak AUROC | Status |
|---|---|---:|---:|---|
| fixed-4° coverage-normalized anchored four-clique | frozen candidate | 0.813250 | 0.811631 | complete |
| internal split statistic | internal baseline | 0.756654 | 0.772837 | complete |
| internal local-density statistic | internal baseline | 0.753978 | 0.758780 | complete |
| internal four-dimensional DBSCAN | internal baseline; not Sugar et al. | 0.749487 | 0.748877 | complete |
| Sugar et al. deterministic published core | literature DBSCAN core | 0.508578 | 0.524927 | complete |
| Southworth–Hawkins D_SH, six-member single linkage | classical orbital-element comparator | 0.604533 | 0.579954 | complete |
| D_SH four-member sparse adaptation | predeclared adaptation | 0.640364 | 0.637606 | complete |
| Valsecchi–Jopek–Froeschlé D_N, M=6 | geocentric-observable classical comparator | 0.731316 | 0.714395 | complete |
| D_N, M=4 sparse benchmark transfer | predeclared sparse transfer | 0.759251 | 0.746209 | complete |

D_N M=4 is the strongest implemented classical sparse comparator, but fixed4 retains the higher overall weak-stream AUROC in both years. No uniformly-best claim is allowed: D_N M=6 slightly exceeds fixed4 at k=12 and alpha .05 in both years.

The episode system therefore includes:

- internal noncluster and density baselines;
- a conventional DBSCAN baseline;
- the deterministic core of a published uncertainty-aware DBSCAN method;
- an orbital-element D-criterion;
- a directly observed geocentric-variable D-criterion;
- published minimum-member formulations and separately labelled sparse adaptations.

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

The uncertainty stages materially improved the catalogue result in both years. Their stable size boundary remained important: mean retained-master F1 for annual 4–9-member showers was approximately 0.03 in both catalogues, while large-shower performance was strong.

This is a faithful published-stage survey transfer using SonotaCo marginal errors and a preregistered deterministic interpretation of an unpublished merge order. It is not represented as an exact reproduction of unpublished ASGARD software or covariance.

## Wavelet survey status

The Brown et al. CMOR-style 3D wavelet family was not quietly omitted and was not scored with weakened rules.

A frozen one-year support audit found only five one-degree bins with at least 300 total retained radiants and only one eligible three-point temporal chain. A subsequent seven-year SonotaCo virtual-year input audit used 178,188 retained events from 2019–2025 and passed multiyear continuity, single-year-dominance, and temporal-chain gates. It failed the preregistered global support-breadth gate:

- bins with at least 300 total events: **199/324 = 61.4%**;
- frozen requirement: **at least 80%**.

Because 300 total events in a time bin is only a necessary condition for 300 events to contribute near a particular radiant-speed test point, the unsupported bins cannot satisfy the published coefficient floor anywhere. A selective-season run, larger bins, lower floor, shorter chain, or known-coordinate search would change the survey task after seeing the data.

The wavelet comparator is therefore **formally deferred for incompatible optical input**, not failed and not beaten. A full implementation would require a denser, exposure-controlled multiyear survey comparable to the radar catalogue used by the original method.

## Other D-criteria and classical variants

The literature contains additional orbit dissimilarity functions, including Drummond- and Jopek-family variants, as well as different linkage, iterative, index, and density-map operators. They are not individually added to the leaderboard for three reasons:

1. D_SH and D_N already span the principal scientific distinction between orbital-element similarity and geocentric quantities directly tied to observations.
2. Additional D-functions often require database- and membership-specific chance thresholds; the modern comparative literature reports uneven validation and cautions that orbital similarity alone is insufficient to establish a shower.
3. Adding a large set of closely related variants after seeing the results would create method shopping rather than test a new method family.

This is not a claim that every D-function is equivalent. It is a decision that further variants would provide diminishing, highly correlated evidence on this benchmark. A future preregistered D-criterion study could compare the complete family as its own project, with sample-specific null thresholds frozen before evaluation.

## KDE false-positive estimation

Recent KDE work estimates the false-positive rate of known shower or parent-body associations across several D-criteria. It is a statistical significance and contamination framework, not a blind stream-discovery algorithm. It is therefore not an omitted detector comparator.

Its scientific function is already represented in the OrbitTrace study by empirical negative calibration, pooled and sector-level false-positive reporting, shifted/null tests, and independent-year transfer. A direct KDE replication could be a useful ancillary calibration paper, but it would not answer whether fixed4 detects sparse streams better than another discovery algorithm.

## Methods intentionally excluded from the leaderboard

- **Known-shower lookup or direct-template matching:** association/classification against predefined means, not blind discovery.
- **Parent-body association tests:** test a proposed relationship after a candidate exists.
- **Pure dynamical integrations:** physical validation and provenance analysis, not an observational clustering baseline.
- **Supervised neural classifiers:** require a labelled training task and architecture not supplied by a comparable published stream-discovery benchmark.
- **Radar-specific wavelet execution on unsupported optical seasons:** changes the data regime and published support conditions.

## Completion decision

The literature-comparator development phase is complete for the current data.

A new baseline should be added only if it satisfies all of the following before result access:

1. it represents a genuinely different method family or task-relevant capability;
2. a primary source specifies enough detail for a fixed implementation;
3. the required public inputs exist in SonotaCo or another preregistered survey;
4. its natural evaluation unit can be compared without relabelling episode and catalogue tasks;
5. parameters and reporting rules can be frozen before the independent corpus is opened.

No presently identified method meets those conditions while adding substantial evidence beyond D_SH, D_N, full Sugar, HDBSCAN, and the formally audited wavelet family. Further progress now requires a new external survey or exposure-controlled radar-scale input, not more post-result variants.

## Final independent judgment

**Retain fixed4 as a major second OrbitTrace contribution, narrowly framed as sparse weak-stream recognition under controlled false-positive evaluation.**

The conclusion is stronger than it was before the literature program because:

- fixed4 transferred almost unchanged from 2025 to 2023;
- it exceeded both orbital and geocentric classical sparse comparators in overall weak-stream AUROC;
- complete HDBSCAN and Sugar catalogue implementations showed reproducible strength for larger populations and a stable weakness in the smallest annual strata;
- the wavelet family was handled through frozen feasibility gates rather than an unfair reduced imitation.

The conclusion is not unlimited. Fixed4 is not uniformly best at every k and operating point, did not historically discover OrbitTrace, did not blindly rediscover it from a full catalogue, and did not fully pass every preregistered robustness gate. The frozen general-method conclusion remains:

> **Promising strong transfer, but not fully robustly replicated under the complete preregistered standard.**
