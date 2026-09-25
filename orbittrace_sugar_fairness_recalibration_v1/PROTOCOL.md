# Recurrent-EOM versus Sugar fairness recalibration v1

## Status and role

This is a **corrective, exposed fairness adjudication**, not a pristine preregistered validation. The SonotaCo 2013/2014 truth has already been opened elsewhere in the project and a diagnostic audit has already shown that the previously frozen Sugar `23%` epsilon-percentile transfer is materially dataset-sensitive. This protocol therefore cannot create new pristine evidence. Its purpose is narrower: determine whether the paper-facing statement that recurrent-EOM is better than the tested Sugar reconstruction survives after removing a known comparator handicap.

The earlier `PASS_TEMPORAL_FAIR_LITERATURE_4_OF_4` result is **not sufficient by itself** for a Sugar-superiority claim because Sugar et al. describe the expected shower fraction used to choose epsilon as dataset/instrument specific. Carrying the original NASA/SOMN 23% value unchanged to SonotaCo can therefore disadvantage Sugar.

No OrbitTrace target information is used by this correction.

## Immutable recurrent-EOM side

Recurrent-EOM is not retuned or rerun scientifically. The benchmark consumes the exact already-frozen pretruth candidate catalogue from run `31829200215`, artifact `orbittrace-recurrent-eom-sonotaco-v31-benchmark-v1`, with the same pooled 2013+2014 label-free SonotaCo rows and frozen ranking.

The correction may not alter recurrent-EOM memberships, ranks, features, hierarchy, recurrence rule, or candidate budget.

## Sugar implementation

Use the exact exported uncertainty-aware Sugar reconstruction source with SHA-256
`5b7699a2cf07b9b9ac6dee006c66a9b509af73ee3763093fa333d13e1deca0cb`.

Unchanged published/reconstruction stages:

- six-dimensional Sun-centered GEO feature vector;
- Euclidean DBSCAN;
- `min_samples = 5`;
- epsilon defined from a percentile of the fourth-nearest-neighbour distances;
- 1,000 Gaussian uncertainty-clone catalogues;
- zero solar-longitude uncertainty;
- SonotaCo RA/Dec/Vg marginal uncertainties, with no invented covariance;
- 50% member-overlap merge rule using the already-frozen deterministic connected-component interpretation;
- retain master components represented in at least 100/1,000 clone iterations;
- the already-frozen hard-assignment rule for event-level catalogue scoring.

The exact merge ordering/source code of Sugar et al. is not published. Accordingly, every conclusion from the uncertainty-aware pipeline is explicitly scoped to **the frozen Sugar reconstruction**, not claimed as a byte-exact reproduction of the authors' unpublished implementation.

## Dataset-specific epsilon calibration

To avoid using the NASA/SOMN-specific 23% value on SonotaCo, Sugar receives a deliberately conservative cross-year calibration advantage:

- evaluation on **2013** uses the shower-member fraction measured only in the other year, **2014**: `5950 / 15400 = 38.63636363636363%`;
- evaluation on **2014** uses the shower-member fraction measured only in the other year, **2013**: `7523 / 18638 = 40.36377293701041%`.

The evaluation year's labels do not select its Sugar epsilon percentile. These two percentages are fixed in this protocol before the 1,000-clone correction run.

This is intentionally favorable to Sugar: recurrent-EOM receives no label-derived calibration. If recurrent-EOM still wins under matched catalogue capacity, the result cannot be explained by the original 23% transfer handicap.

For both panels, Sugar and recurrent-EOM receive the same pooled label-free 2013+2014 event rows before evaluation-year truth is used for scoring.

## Sugar catalogue ordering for matched-capacity evaluation

Sugar does not publish a discovery-catalogue ranking intended for a top-K review budget. For this comparison only, retained master families are ordered by native uncertainty evidence without using shower truth:

1. recurrence across the 1,000 uncertainty realizations, descending;
2. mean hard-assigned membership probability of family members, descending;
3. assigned member count, descending;
4. deterministic hash of the assigned member-ID set, ascending.

This ordering is an evaluation adapter, not attributed to Sugar et al.

## Evaluation

Evaluation uses the same eligible shower definition and one-to-one Hungarian assigned F1 semantics as the corrected pooled SonotaCo benchmark.

Primary matched-capacity budgets are fixed at `K = 20, 40, 60, 80, 100`. At every K report:

- macro F1 over eligible showers, with unmatched showers scored zero;
- number of showers with assigned F1 > 0.5;
- recovered-showers-per-reported-candidate as a catalogue-efficiency diagnostic.

Also report, but do not use as the sole winner criterion:

- every retained uncertainty-aware Sugar family versus every recurrent-EOM family;
- a single observed-catalogue deterministic Sugar DBSCAN diagnostic at the same cross-year-calibrated epsilon percentile, because it separates the base DBSCAN clustering quality from uncertainty-merge behavior;
- number of reported candidate families.

The full-output metric is not by itself a fair discovery comparison because emitting many extra candidates is weakly penalized by Hungarian macro F1. Fixed-capacity results are therefore primary for the actual catalogue-discovery objective.

## Adjudication

For each year separately:

- `RECURRENT_EOM_MATCHED_CAPACITY_WIN` requires recurrent-EOM macro F1 >= Sugar at all five fixed K values and recovered-shower count >= Sugar at all five K values, with at least one strict macro-F1 improvement.
- `SUGAR_MATCHED_CAPACITY_WIN` is the symmetric condition for Sugar.
- otherwise the year is `MIXED`.

Overall:

- `RECURRENT_EOM_BETTER_FOR_RANKED_DISCOVERY` requires recurrent-EOM to win both years;
- `SUGAR_BETTER_FOR_RANKED_DISCOVERY` requires Sugar to win both years;
- otherwise `NO_UNAMBIGUOUS_WINNER`.

Because diagnostic 100- and 260-clone audits preceded this full run, this adjudication is **exposed corrective evidence**. It may correct or narrow a manuscript claim, but must not be presented as a pristine preregistered superiority test.

## Claim firewall

Allowed if supported:

> Under an exposed corrective SonotaCo audit that gives the Sugar reconstruction cross-year dataset-specific epsilon calibration, recurrent-EOM [outperformed / did not outperform] the frozen Sugar reconstruction at matched catalogue capacities.

Not allowed:

- “recurrent-EOM universally beats Sugar”;
- “the original Sugar authors' exact implementation was inferior”;
- “pristine external validation”;
- hiding a full-output Sugar advantage if one occurs;
- using this correction to retune recurrent-EOM or the OrbitTrace target search.
