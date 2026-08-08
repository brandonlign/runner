# OrbitTrace probabilistic membership P1 — frozen development protocol

## Purpose

P1 is a genuinely new post-core membership architecture motivated by the broad, target-excluded observation that the proven v8 recurrent cores/ranking are useful while incomplete or brittle final membership can dominate catalogue F1. It is not an R1 retune and does not reuse R1's D_SH threshold, medoid rule, hard conflict rule, or expanded memberships.

P1 keeps the exact promoted v8 recurrent-family universe and exact multiplicity ranking immutable. Only final member assignment changes.

## Frozen inputs

Development panel: GMN 2022 and 2023 with solar longitude 20°–55° removed before label normalization/storage/candidate generation.

Exact v8 artifacts:

- family artifact SHA-256 `f76b8448f299ccf078fc5978c0890b9a084f131080db8d2136b5e6dba77edc7b`;
- multiplicity-evaluation artifact SHA-256 `ed81975fe10c35b49862487b0073b5d192c0983ea47dc56f281d7b4f8a250c03`;
- ranking artifact SHA-256 `e97f840059956c47e3088484d884d7836e3a20e6c415b461564befb0e0699858`;
- exact 226 v8 recurrent family IDs and exact multiplicity order;
- every original v8 seed event is immutable and can never be removed or reassigned.

The historical OrbitTrace target, target-region events, target coordinates, target members, prior target rank, and target-containing outputs are forbidden.

## P1 model

For each frozen family:

1. Reconstruct the intended pooled same-year v8 centroid directly from that family's original seed events: circular mean in solar longitude and Sun-centered longitude, median ecliptic latitude, median geocentric speed.
2. Express every seed as a four-dimensional residual in the inherited v8 geometry units: solar-longitude residual / 4°, Sun-centered longitude residual / 2° with latitude cosine factor, latitude residual / 2°, and speed residual / 2 km/s.
3. Pool seed-only residuals across the two years after within-year centering and estimate one common covariance using Oracle Approximating Shrinkage (OAS). No shower labels or added members enter this fit.
4. For each year, evaluate every non-seed target-excluded event under the current-year pooled centroid and the seed-only covariance.
5. The candidate stream region is the 99% four-dimensional chi-square ellipsoid. The local-background shell is the 99%–99.99% chi-square annulus. These probabilities are distributional definitions, not development-tuned radii.
6. Estimate a conservative local background intensity from the shell using the exact one-sided 95% Garwood Poisson upper bound. This intentionally overestimates, rather than underestimates, contamination.
7. Estimate stream amplitude as the immutable current-year seed count plus only positive non-seed excess over the conservative expected background inside the 99% ellipsoid, divided by 0.99 containment.
8. Compute a Gaussian stream intensity for each candidate under the seed-only covariance. Original v8 seed events never compete and never move.
9. If one non-seed event is compatible with multiple families, all compatible stream intensities compete simultaneously against a conservative local-background intensity. Assign the event only to the maximum-intensity family when that family's normalized posterior responsibility is strictly greater than 0.5. Otherwise leave the event unassigned.
10. Added events never refit centroids, covariance, background, stream amplitude, another family, or another growth step. The exact v8 multiplicity ranking is unchanged.

Thus P1 is a seeded local-background mixture model with conservative background competition, not a radius-expansion variant.

## Pre-truth freeze

The complete expanded family membership payload must be serialized and SHA-256 frozen before any known-shower label is used for evaluation. Label-based evaluation may read only that frozen payload.

## Development gates

All integrity and scientific gates must pass in the single target-excluded 2022/2023 development execution.

Integrity:

- exact 226-family v8 ID universe and exact multiplicity order;
- exact v8 baseline metrics reproduced from the frozen seed memberships;
- every original seed event preserved in its original family;
- no original seed event assigned elsewhere;
- added events do not seed or refit any model quantity;
- membership payload frozen before truth evaluation;
- exact 20°–55° exclusion inherited from the frozen parser;
- no parameter/radius/threshold/variant search.

Scientific:

- expansion is non-vacuous;
- qualified known-shower matches do not regress below frozen v8's 95;
- recovery@100 does not regress below frozen v8's 58;
- top-100 dominant precision remains at least 0.65;
- macro F1 improves by at least +0.08 absolute over frozen v8.

Failure is `FAIL_PROBABILISTIC_MEMBERSHIP_P1_NO_GO` and permanently rejects this exact P1 architecture. A failure does not authorize nearby posterior, shell, covariance, confidence, or containment variants on the same result.

## Next stages

A development pass does not establish superiority over Sugar/HDBSCAN and does not authorize target access. It authorizes a separately frozen matched-data literature comparison and then no-retuning external/held-out validation. Only after the method has met the required comparison and generalization gates may a final blind target-containing OrbitTrace deployment be frozen and executed.