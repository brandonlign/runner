# OrbitTrace P2 — frozen matched Sugar/HDBSCAN literature adjudication

## Status and activation

Protocol-only freeze created before any P2 scientific execution or result. This branch opens no SonotaCo archive, reads no comparator assignment or known-shower truth value, accesses no event from solar longitude 20°–55°, and accesses no OrbitTrace target information.

P2 may reach this comparison only after the succession already frozen in the P2 development protocol: the stronger preceding v6/P1 path must fail to satisfy the project goal, exact P1 must be scientifically rejected under its frozen gates, and exact P2 must then pass its one-shot target-excluded GMN 2022/2023 development gates. A P2 development no-go leaves this protocol permanently dormant.

## Compared method

P2 is a membership architecture layered on exact promoted-v8 target-free recurrent cores and exact promoted-v8 multiplicity order. On every matched panel:

1. run the exact promoted-v8 core/family/ranking architecture, unmodified, on the panel-specific paired-year exact-row universe;
2. freeze the recurrent family universe and exact multiplicity order before truth/comparator access;
3. apply the exact frozen P2 cross-year two-view membership architecture to those immutable panel-specific v8 cores;
4. keep the v8 family order unchanged.

GMN development family IDs, centroids, members, classifier coefficients, or fitted P2 model are not transported into SonotaCo. P2 architecture transfers; panel-specific self-supervised fitting is repeated from the immutable v8 cores of that panel under the exact frozen P2 rule.

## Exact P2 transfer rule

For each panel-specific v8 family and each paired-year direction:

- source-year immutable v8 seeds define the predictive observation template;
- observation centroid uses the frozen circular solar-longitude/Sun-centered-longitude means and median latitude/speed;
- source-seed 4D residual covariance uses OAS, with Moore–Penrose pseudoinverse only if exact inversion is singular at machine precision;
- `d_obs` is the square-root Mahalanobis distance in the inherited v8 geometry units;
- `d_orb` is minimum exact Southworth–Hawkins D_SH to any opposite-year immutable source seed, using the exact SHA-pinned R1-preserved comparator implementation;
- positives are target-year immutable seeds of the same family;
- negatives are all target-year nonseed events within ±5° of that family's target-year immutable seed centroid, excluding every original v8 seed;
- every family-direction must contain at least 128 negatives or P2 is input-ineligible on that panel; this threshold is not relaxed;
- each direction contributes exactly 0.5 total positive and 0.5 total negative weight;
- fit exactly one StandardScaler(sample weights) + L2 LogisticRegression with C=1.0, lbfgs, max_iter=1000, tol=1e-10, intercept enabled, no class weight;
- candidate family probability is converted to odds; all compatible family odds compete jointly with one unit background weight;
- assign only the maximum-responsibility family when responsibility is strictly >0.5; ties use exact v8 rank then family ID;
- seeds never move and additions never refit, recenter, retrain, change the candidate universe, or seed growth;
- serialize/hash-freeze the fitted model and full memberships before known-shower/comparator truth is opened.

No feature, orbit formula, OAS rule, negative window, minimum negative count, weighting, logistic setting, background weight, responsibility threshold, or tie rule may change on SonotaCo.

## Exact-v8 support boundary

P2 inherits v8 cores and therefore inherits every hard support limitation of promoted v8. Prior exact-row v8 literature work established that at least one HDBSCAN-matched SonotaCo configuration can leave only 64 local-window rows where promoted v8 requires an exact 128-event episode.

No padding, event duplication, window widening, borrowing rows outside the exact comparator universe, lowering the 128-event requirement, alternate core detector, or quality-cut change is permitted. Missing v8 cores count as part of P2 performance. If the complete promoted-v8 paired-year detector cannot run under unchanged requirements on a comparator universe, classify that panel `P2_MATCHED_INPUT_INELIGIBLE_EXACT_V8_SUPPORT`; it cannot satisfy a literature-superiority claim.

P2 has a second immutable eligibility requirement: every constructed family-direction must have at least 128 frozen-rule negative events. Failure is `P2_MATCHED_INPUT_INELIGIBLE_DIRECTION_BACKGROUND`; it is not repaired by widening the ±5° window, sampling another background, changing the family universe, or lowering the count.

## Matched comparator universes

Reuse exactly the already-frozen pairwise SonotaCo universes and input identities from the v6 matched-literature adjudication.

### HDBSCAN exact-row universe

- 2023: 26,460 event rows.
- 2025: 19,658 event rows.

Use the exact frozen HDBSCAN assignments, archive identities, parser/transport identities, IAU mapping, and ID manifest. No replacement catalogue revision or P2-specific filtering is allowed.

### Sugar exact-row universe

- 2023: 30,414 event rows.
- 2025: 23,200 event rows.

Use the exact frozen Sugar uncertainty-transfer assignments, archive identities, parser/transport identities, IAU mapping, and ID manifest. No replacement catalogue revision or P2-specific filtering is allowed.

HDBSCAN and Sugar denominators are different. Never mix their absolute F1, support, recovery, or shower counts. All claims are pairwise inside each comparator's exact universe.

## Pre-truth ordering

For each comparator panel:

1. materialize only frozen exact-row geometry/IDs and target-excluded background representation;
2. keep known-shower truth and competitor assignments inaccessible;
3. run exact promoted v8 and freeze families/order;
4. run exact P2 self-supervised feature construction and model fit using only immutable v8 family identity and nonseed background;
5. freeze P2 model SHA-256;
6. perform joint P2 assignment and freeze full membership SHA-256;
7. only then open known-shower mapping and comparator assignments;
8. evaluate P2 and its paired comparator on the exact common event/label universe.

The classifier may never see known-shower labels or competitor labels. The fitted coefficients are panel-specific consequences of the frozen self-supervised rule, not tuned parameters.

## Evaluation

Use the same frozen known-shower eligibility, matching, F1, macro-F1, and size-stratum definitions as the v6 matched literature adjudication.

For every comparator/year report:

- event-row count and integrity hashes;
- exact-v8 support diagnostics;
- P2 direction-background eligibility diagnostics;
- recurrent v8 family count and unchanged v8 order hash;
- P2 model and membership pre-truth hashes;
- assigned nonseed count and conflicted-candidate count;
- eligible known-shower count;
- qualified matches;
- macro F1 and per-shower F1;
- mean F1 for 4–9, 10–24, 25–49, 50–99, and 100+ where nonempty;
- combined 4–24 mean F1;
- number of eligible showers with F1 > 0.5;
- exact paired comparator endpoints and P2-minus-comparator differences;
- panel-specific v8 baseline diagnostics for membership gain/non-regression.

P2 inherits the v8 rank; do not attribute a rank/core-discovery improvement to P2 itself.

## Frozen superiority bars

P2 receives exactly the same literature standard as v6 and P1.

### `BROAD_CATALOGUE_SUPERIORITY`

Required independently versus HDBSCAN and versus Sugar in both 2023 and 2025:

1. P2 macro F1 >= comparator macro F1 + 0.05;
2. no nonempty size stratum is worse than comparator by >0.05;
3. at least two nonempty size strata/year improve by >=0.10 mean F1;
4. count of eligible showers with F1 > 0.5 is not lower than comparator;
5. all common-universe, exact-v8 support, P2 direction eligibility, source/provenance, blind, pre-truth, and model-integrity gates pass.

### `SPARSE_STREAM_SUPERIORITY`

If broad superiority is not met, required independently versus both comparators in both years:

1. 4–9-event mean F1 >= comparator +0.10;
2. combined 4–24-event mean F1 >= comparator +0.10;
3. macro F1 no more than 0.10 below comparator;
4. retain >=80% of comparator's eligible-shower count with F1 >0.5;
5. all integrity/eligibility gates pass.

### `NO_LITERATURE_SUPERIORITY`

Any eligible result satisfying neither full standard is `NO_LITERATURE_SUPERIORITY`. A one-year win, one-comparator win, selected-bin win, or GMN development gain is insufficient.

Input-ineligibility classifications are reported separately but cannot count as superiority.

## Internal v8 comparison

On every eligible panel, report P2 versus the exact panel-specific v8 membership baseline: macro F1, qualified matches, top-ranked dominant precision where defined, per-size F1, and member counts. This diagnoses whether P2 improves membership on transfer data; it does not substitute for Sugar/HDBSCAN superiority.

## Outcome semantics

- P2 development failure: no literature run.
- P2 development pass + broad superiority: advance to separately frozen no-retuning validation/generalization.
- P2 development pass + sparse superiority: advance only with sparse/weak-stream claim boundary.
- P2 development pass + no superiority: permanent no-go for the project superiority objective; do not retune P2 from the comparison.
- exact-v8 or P2-background input ineligibility: report honestly; no adaptation from outcome and no superiority claim.

No matched-literature result alone authorizes target access.

## Firewall

The 20°–55° solar-longitude interval remains removed before label storage, core generation, orbit decoding for P2, self-supervised training, candidate assignment, and truth evaluation.

Forbidden inputs include OrbitTrace coordinates, identity, canonical members, previous target rank, target-containing result, or excluded-interval event. Comparator/known-shower labels remain inaccessible until the model and memberships are frozen.

A final blind OrbitTrace deployment requires the selected method to satisfy the project's preregistered comparison and no-retuning generalization requirements, followed by a separately frozen target success threshold, complete-ranking output, reveal procedure, and claim boundary.
