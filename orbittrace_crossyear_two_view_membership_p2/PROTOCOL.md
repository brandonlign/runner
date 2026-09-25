# OrbitTrace cross-year two-view membership P2 — frozen successor protocol

## Status and activation

P2 is a dormant, one-shot successor architecture frozen before any P1 scientific result exists and before the current repaired v3-primary catalogue-v6 development/literature outcome is known. It may not execute while a stronger already-frozen path remains scientifically live.

The intended succession order is:

1. finish the exact repaired v3-primary catalogue-v6 development result;
2. if v6 passes, execute its frozen matched Sugar/HDBSCAN adjudication;
3. if v6 fails development, or passes development but fails to establish the required literature superiority, execute the already-frozen P1 membership architecture first;
4. execute P2 only if exact P1 is scientifically rejected under its frozen gates.

This succession rule is fixed now so no P2 choice can be made from a P1 outcome. P2 is not an R1 or P1 parameter variant.

## Motivation fixed from allowed target-excluded evidence

Exact promoted v8 recurrent cores are high-purity but incomplete. R1 demonstrated that physical-orbit expansion contains real recall signal but its fixed broad acceptance rule is unusable as a final architecture: 105,847 non-seed events were assigned, 101,231 of them were contested by multiple families, and a small number of families absorbed tens of thousands of events. R1 nevertheless improved macro F1 from 0.173666 to 0.351308 and large-shower mean recall from 0.067384 to 0.246210 at mean precision 0.916404, showing that the missing signal is not merely noise.

P1 addresses this with a family-local observation-space Gaussian/background mixture. P2 is deliberately different: it learns one global, target-free cross-year discriminator from immutable v8 cores versus local non-seed background, combines observation geometry with an independent physical-orbit view, and resolves all family conflicts jointly.

No OrbitTrace target information, target-region event, target coordinate/member/identity, prior target rank, Sugar/HDBSCAN outcome, or future P1 result may choose any P2 feature, threshold, weighting, solver, gate, or variant.

## Frozen inputs

Development panel: GMN 2022 and 2023 with solar longitude 20°–55° removed before label normalization/storage/candidate generation.

Exact promoted-v8 identity is fixed to:

- source commit `c9d6c44704013ba0c9430100e98a29a56b453304`;
- exact 226 recurrent family IDs and original seed-event unions inherited by v8;
- exact promoted-v8 multiplicity order reconstructed from source before any known-shower label evaluation;
- baseline qualified matches 95;
- baseline recovery@100 58;
- baseline MRR 0.045531138942766655;
- baseline top-100 dominant precision 0.6884631112636006;
- baseline macro F1 0.1736657194465356.

The orbital transport is the already source-audited target-excluded GMN representation exposing `q`, `e`, `i`, `peri`, and `node`. P2 must reuse the exact Southworth–Hawkins D_SH implementation identity preserved by R1; P2 may not alter the D_SH formula.

## Immutable seed/core rule

Original v8 seeds are immutable labels only in the self-supervised sense of family identity. They are never removed, reassigned, or expanded recursively. Added P2 members never become training positives, never alter a centroid/covariance/classifier, and never create another candidate.

The exact v8 family order remains unchanged. P2 changes membership only.

## Cross-year predictive feature construction

For each frozen family and each direction `source_year -> target_year` (2022→2023 and 2023→2022):

1. Use only the source-year v8 seed events to build the predictive family template.
2. Define the source-year observation centroid with the same circular/robust conventions already used by promoted v8/P1: circular mean solar longitude, circular mean Sun-centered longitude, median ecliptic latitude, and median geocentric speed.
3. Express source seeds and target events in the inherited four-dimensional geometry units: wrapped solar-longitude residual / 4°, wrapped Sun-centered-longitude residual / 2° with the latitude cosine factor, latitude residual / 2°, and speed residual / 2 km/s.
4. Estimate the source-year seed covariance in this 4D residual space with Oracle Approximating Shrinkage (OAS). If numerical inversion is singular at machine precision, use the Moore–Penrose pseudoinverse; no ridge parameter may be introduced.
5. Observation feature `d_obs` is the nonnegative square root of the resulting Mahalanobis squared distance to the source-year template.
6. Orbit feature `d_orb` is the minimum exact Southworth–Hawkins D_SH from the event to any immutable source-year seed event in that family. No fixed D_SH acceptance threshold is used.

Thus each event/family directional comparison has exactly two features: `[d_obs, d_orb]`.

## Self-supervised training set

P2 trains one global classifier pooled across all frozen families and both cross-year directions. Known-shower catalogue labels are forbidden.

For each family direction:

- positives are the immutable target-year v8 seed events of that same family, scored against the opposite-year source template;
- negatives are every target-year non-seed event whose wrapped solar longitude lies within ±5° of that family target-year immutable seed centroid, excluding every event that is an original seed of any v8 family;
- the ±5° rule is exactly the half-width of the inherited 10° catalogue window and is not a tuned membership radius;
- at least 128 negatives must exist for every family direction; otherwise P2 is input-ineligible rather than retuned.

To prevent dense windows or large families from dominating training, each family direction contributes exactly total weight 0.5 to its positives and total weight 0.5 to its negatives. Therefore a direction with `n_pos` positives assigns weight `0.5/n_pos` to each positive, and a direction with `n_neg` negatives assigns weight `0.5/n_neg` to each negative. No random negative subsampling is allowed.

## Frozen discriminator

Fit exactly one deterministic two-feature scikit-learn pipeline:

1. `StandardScaler`, fit with the exact sample weights above;
2. `LogisticRegression` with L2 penalty, `C=1.0`, `solver='lbfgs'`, `max_iter=1000`, `tol=1e-10`, no class-weight option, and intercept enabled.

The equal positive/negative total weight inside every family direction already creates equal effective class contribution, so no additional class reweighting is allowed. Convergence is an integrity requirement. No alternative feature transform, interaction term, polynomial term, solver, C value, tolerance, or model family may be tried after execution.

The fitted scaler and classifier coefficients/intercept must be serialized and SHA-256 frozen before any known-shower truth evaluation.

## Candidate scoring and joint conflict resolution

After the classifier is frozen:

1. Candidate non-seed events are the union of the same deterministic ±5° target-year family windows used above.
2. For every compatible event/family pair, compute `[d_obs, d_orb]` against the opposite-year template and obtain the classifier probability `p_f`.
3. Convert `p_f` to balanced discriminative odds `o_f = p_f / (1 - p_f)`. Clipping is permitted only at machine epsilon to avoid division by zero and is not a scientific threshold.
4. For an event compatible with families `f=1..k`, introduce one unit background weight and compute family responsibility `r_f = o_f / (1 + sum_g o_g)`.
5. Assign the event only to the family with maximum `r_f` when that maximum is strictly greater than 0.5. Otherwise the event remains unassigned.
6. Ties in maximum responsibility are resolved only by exact promoted-v8 family rank and then family ID; the responsibility threshold itself is unchanged.
7. Original seeds do not enter competition and never move.
8. Added events never retrain, recenter, alter covariance, change the candidate universe, or seed further growth.

The complete P2 membership payload must be serialized and SHA-256 frozen before known-shower labels are made available to the evaluator.

## Evaluation

Use the exact promoted-v8 multiplicity order and exact promoted-v8 `evaluate_order` implementation for both baseline and P2 memberships. No replacement matching, tie, qualification, or F1 evaluator is permitted.

In addition to the standard whole-catalogue endpoints, preserve the exact R1 large-shower subset definition: the frozen-v8-qualified known showers with at least 100 labelled events in the target-excluded 2022/2023 development panel. This subset is fixed from already-allowed target-excluded evidence and may not be reselected.

## One-shot development gates

All integrity gates must pass:

- exact 226-family v8 universe and exact multiplicity order reproduced;
- exact v8 baseline metrics reproduced;
- exact target exclusion precedes orbit decode and label storage;
- exact R1 D_SH implementation identity verified;
- every source/target training pair is cross-year predictive as specified;
- no known-shower label enters feature construction, training, scoring, conflict resolution, or membership freeze;
- classifier converges under the exact frozen solver/settings;
- original seeds are unchanged;
- added events never seed/refit;
- classifier and full memberships are hash-frozen before truth evaluation;
- no parameter/feature/model/threshold/variant search.

All scientific gates must pass simultaneously:

- expansion is non-vacuous;
- qualified known-shower matches >= 95;
- recovery@100 >= 58;
- top-100 dominant-label precision >= 0.65;
- macro F1 improves by at least +0.08 absolute over exact v8;
- on the exact frozen large-shower subset, mean recall is at least 1.5× the exact v8 mean recall;
- on that same subset, mean precision is at least 0.85.

A pass is `PASS_CROSSYEAR_TWO_VIEW_MEMBERSHIP_P2_DEVELOPMENT`.

A scientific failure is `FAIL_CROSSYEAR_TWO_VIEW_MEMBERSHIP_P2_NO_GO` and permanently rejects this exact architecture. Failure does not authorize changing the window, features, D_SH statistic, OAS rule, logistic settings, weights, background unit, responsibility threshold, tie rule, or gates on the observed result.

## Downstream rule

A P2 development pass is not a literature-superiority claim and does not authorize OrbitTrace target access. It must undergo a separately frozen matched-data Sugar/HDBSCAN comparison and then no-retuning external/held-out validation. Only a method satisfying the project’s required comparison and generalization gates may advance to a separately frozen blind target-containing OrbitTrace deployment.
