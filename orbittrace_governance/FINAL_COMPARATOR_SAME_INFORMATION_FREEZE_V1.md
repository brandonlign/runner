# OrbitTrace final same-information comparator freeze — v1

## Status

This protocol freezes the candidate-independent **detector-input interface** for the permanent SonotaCo 2013/2014 literature test before either year's scientific archive values, known-shower truth, comparator outputs, or final OrbitTrace-candidate scores are opened.

It implements the information-parity requirement in `FINAL_LITERATURE_TEST_POLICY_V1.md`. It does not select the final OrbitTrace method and does not authorize SonotaCo access. The final candidate-specific test runner must still be frozen after one method is declared `FINAL_FOR_LITERATURE_TEST` and before any final-test value is opened.

## Why a new same-information freeze is necessary

Historical SonotaCo literature-transfer pipelines were scientifically useful but are not automatically eligible for the final same-information claim:

- the historical catalogue-HDBSCAN primary transfer used a reference-label filter that removed labeled showers below a known annual-count threshold;
- the historical Sugar benchmark-universe definition excluded native shower codes that could not be mapped through a truth catalogue;
- those truth-dependent row-selection operations violate the final policy's rule that no known-shower label, native shower/background designation, catalogue mapping truth, or equivalent supervision may enter detector input for one method but not the other.

The final test therefore reuses the **frozen published clustering algorithms and physical quality filters** while removing truth-dependent row selection from detector construction. Known-shower truth remains completely sealed until candidate and comparator outputs are frozen.

No historical Sugar/HDBSCAN outcome value is used by this protocol.

## Pairwise row-universe construction

The final benchmark remains pairwise.

For each year independently and for each comparator independently:

1. start from the exact SonotaCo meteor rows for that year after the universal solar-longitude 20°–55° exclusion;
2. apply only deterministic, label-free structural/quality requirements needed by the comparator and the frozen final candidate;
3. take the exact intersection of stable meteor IDs surviving both methods' structural requirements;
4. freeze and hash that common-row manifest before either method is run;
5. give **both** methods the same common rows and the same raw observable fields present on those rows;
6. permit each algorithm to use only its already-frozen transformations of those observables;
7. freeze all candidate/comparator outputs on that common-row universe before known-shower truth is opened.

No row may be included or excluded because of native shower code, MDC mapping success, known-shower size, target identity, or post-clustering behavior.

Sugar and HDBSCAN may still have different pairwise universes because their label-free physical/uncertainty requirements differ. Cross-comparator denominator mixing remains forbidden.

## Sugar — final same-information configuration

The scientific algorithm is the frozen full uncertainty-aware Sugar et al. catalogue reconstruction already source-audited in the repository, with **label-dependent row filtering removed** and the paper's unsupervised epsilon rule applied natively to each final-year common-row universe.

### Frozen source lineage

- reference: Sugar, Moorhead, Brown, and Cooke (2017), DOI `10.1111/maps.12856`;
- frozen uncertainty-core SHA-256: `5b7699a2cf07b9b9ac6dee006c66a9b509af73ee3763093fa333d13e1deca0cb`;
- historical source-audit workflow Git blob: `ddd6586d10b8b87f5766d733653c5dea607a5bfe`;
- historical protocol Git blob: `24a8dcdf56bd8316676780406a31caaec82e248f`.

The final implementation may wrap/adapt the frozen core to the 2013/2014 parser and common-row manifests, but the core clustering, cloning, overlap, recurrence, and hard-assignment semantics may not change.

### Label-free physical/structural eligibility

Require, without truth access:

- universal 20°–55° solar-longitude exclusion;
- frozen SonotaCo multi-camera structural validity used by the parser;
- convergence angle strictly greater than 15°;
- geocentric speed <=75 km/s;
- geocentric-speed uncertainty <= `0.1 * vg + 1.0` km/s;
- finite raw radiant and speed observables required by the six-dimensional feature vector;
- finite marginal RA, Dec, and geocentric-speed uncertainties required for cloning.

Do **not** remove a row because of native shower/background designation, inability to map a native shower code to a truth catalogue, shower size, or any label-derived property.

### Frozen algorithm

- six-dimensional Sun-centered GEO vector:
  `[cos(sol), sin(sol), sin(lambda_g-sol)cos(beta_g), cos(lambda_g-sol)cos(beta_g), sin(beta_g), vg/72]`;
- Euclidean metric;
- DBSCAN `min_samples=5`;
- scikit-learn `1.5.2`;
- `algorithm='ball_tree'`, `leaf_size=40`, `n_jobs=1`;
- **epsilon is the 23rd percentile of fourth-nearest-neighbor distances on the exact final-year pairwise common-row universe**, computed before labels and frozen before clone clustering;
- 1,000 Gaussian uncertainty-clone catalogues;
- solar-longitude uncertainty 0;
- independent Gaussian draws in reported RA/Dec marginal uncertainties followed by the frozen equatorial-to-ecliptic transform;
- independent Gaussian speed draws using reported geocentric-speed uncertainty, with the frozen positive-speed redraw rule;
- seed root `20170209`;
- deterministic iteration seed = stable SHA-256 of seed root, final corpus identifier, year, comparator-pair identifier, and iteration index;
- cluster-instance overlap edge when intersection is at least 50% of either cluster;
- master clusters = deterministic connected components of the overlap graph;
- retain recurrence >=100/1000; classify strong recurrence >=500/1000;
- hard assignment by highest event membership probability, tie-broken by larger recurrence then stable component ID; otherwise noise.

### Why epsilon is recomputed rather than imported from an old SonotaCo year

The published Sugar rule is a label-free catalogue-scale statistic, not a supervised tuned constant. Recomputing the frozen 23rd-percentile rule on each exact final common-row universe gives Sugar its native unsupervised calibration under the same unseen rows and avoids handicapping it with a density scale imported from a different survey year. The percentile and neighbor order are frozen now and cannot change after 2013/2014 access.

The older numeric epsilon frozen for a historical 2025→2023 transfer is not used as the final-test epsilon because the permanent final test is a new pairwise common-row benchmark with a stricter same-information objective.

## Catalogue HDBSCAN — final same-information configuration

Use the frozen faithful catalogue-scale HDBSCAN algorithm from Peña-Asensio and Ferrari (2025), but **do not use the historical reference-label filter**. The final same-information configuration corresponds to applying the exact published clustering configuration to all label-free quality-filtered common rows.

### Frozen source lineage

- reference: Peña-Asensio and Ferrari (2025), DOI `10.3847/1538-3881/adec8c`;
- frozen HDBSCAN runner source SHA-256: `a8b638f56dad2597973178523e8ad15e177a4f57e7fe6159fedc84d754afd3d2`;
- historical protocol Git blob: `21f88d30fe73c371619323d3dabd1dbbb67735d7`;
- `hdbscan==0.8.44`.

The final implementation may adapt parser/year/common-row I/O only. Feature construction, quality cuts, clustering hyperparameters, cluster-selection semantics, and noise handling may not change.

### Label-free physical/structural eligibility

Require, without truth access:

- universal 20°–55° solar-longitude exclusion;
- frozen SonotaCo multi-camera structural validity used by the parser;
- convergence angle >=15°;
- velocity uncertainty fraction <=0.10;
- eccentricity <=1.0;
- perihelion distance <=1.0 AU;
- finite observables required by the six-dimensional GEO vector and these physical quality filters.

Do **not** remove or retain a row because of native shower/background designation, known annual shower count, MDC mapping success, or any other truth-derived property.

### Frozen algorithm

- published unstandardized six-component GEO vector:
  `[cos(sol), sin(sol), sin(lambda_g-sol)cos(beta_g), cos(lambda_g-sol)cos(beta_g), sin(beta_g), vg/72]`;
- Euclidean metric;
- `min_cluster_size=100`;
- package-default `min_samples`, therefore 100 for the pinned implementation;
- cluster selection method `eom`;
- `allow_single_cluster=False`;
- `prediction_data=False`;
- all non-noise clusters are retained exactly as returned; no truth-based cluster suppression, remapping, split, merge, or minimum shower-size filter is permitted.

The historical protocol's reference-label-filtered primary analysis is ineligible for the final same-information claim. Its predeclared full-catalogue coverage configuration used the same clustering parameters without the label-size filter; that label-free algorithmic path is the relevant frozen lineage for the final test.

## Candidate parity requirements

At final-candidate freeze time, the candidate-specific runner must prove separately for Sugar and HDBSCAN that:

- the candidate receives exactly the same common-row IDs as that comparator;
- any raw field made available to the comparator is also available to the candidate runner, even if the candidate ignores it;
- the candidate receives no native shower/background bit, MDC identity, known-shower label, target bit, or equivalent supervision;
- any candidate-internal empirical calibration is derived only from label-free observables on the already-authorized development method and is transferred exactly as frozen; it may not use final-year truth;
- comparator-native unsupervised operations frozen above may use the final common-row observables because those operations are part of the comparator algorithm and contain no truth.

## Truth opening and evaluation

For each comparator-year pair:

1. common-row manifest frozen and hashed;
2. candidate output families/members/rank frozen and hashed;
3. comparator cluster assignments frozen and hashed;
4. only then reveal the known-shower truth for those exact row IDs;
5. compute the pairwise metrics and frozen superiority gates in `FINAL_LITERATURE_TEST_POLICY_V1.md`;
6. preserve complete per-shower/year records needed for the preregistered 10,000-replicate stratified bootstrap.

Truth may not feed back into row selection, epsilon, HDBSCAN parameters, candidate parameters, family filtering, or comparator postprocessing.

## Implementation boundary

This file freezes comparator scientific configuration, not executable 2013/2014 access. Before final test access, an audited implementation must:

- reconstruct or import the exact frozen Sugar core SHA above;
- reconstruct or import the exact frozen HDBSCAN source SHA above;
- isolate parser/year transport from scientific algorithm logic;
- include synthetic tests proving label fields cannot affect row eligibility or clustering;
- prove exact pairwise common-row identity for candidate and comparator before execution;
- freeze bootstrap seed/unit construction/missing-stratum formulas and the candidate-specific configuration;
- contain no OrbitTrace target information.

Any scientific change to the comparator algorithms after final-test access invalidates the final literature test.

## Firewall

This protocol accesses no SonotaCo 2013/2014 scientific value, no comparator result from those years, no MAARSY scientific value, no target-region event, and no OrbitTrace target information. The target remains inaccessible until the final literature and external-generalization requirements both pass.
