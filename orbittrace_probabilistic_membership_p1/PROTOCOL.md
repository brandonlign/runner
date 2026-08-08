# OrbitTrace probabilistic membership P1 — frozen development protocol

## Purpose

P1 is a genuinely new post-core membership architecture motivated by the broad, target-excluded observation that the proven v8 recurrent cores/ranking are useful while incomplete or brittle final membership can dominate catalogue F1. It is not an R1 retune and does not reuse R1's D_SH threshold, medoid rule, hard conflict rule, or expanded memberships.

P1 keeps the exact promoted v8 recurrent-family universe and exact multiplicity ranking immutable. Only final member assignment changes.

## Frozen inputs

Development panel: GMN 2022 and 2023 with solar longitude 20°–55° removed before label normalization/storage/candidate generation.

Exact promoted-v8 identity:

- source commit `c9d6c44704013ba0c9430100e98a29a56b453304`;
- passed v8 workflow `31217916558`, artifact `9009728299`, artifact digest `sha256:88d2d607e05d027015c338f7e23b64a6195e55ae24f1b2ac745f5e9bc6df599e`;
- exact v8 result JSON SHA-256 `fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b`;
- exact structural-family artifact inherited unchanged by v8 from passed v6, SHA-256 `f76b8448f299ccf078fc5978c0890b9a084f131080db8d2136b5e6dba77edc7b`;
- exact 226 recurrent family IDs and original seed-event unions;
- exact promoted-v8 multiplicity order is recomputed before labels with the promoted v8 source after reconstructing its pooled same-year centroids from those immutable seed events;
- promoted-v8 baseline identity: 95 qualified matches, recovery@100 = 58, MRR = 0.045531138942766655, top-100 dominant precision = 0.6884631112636006.

The predecessor v6 ranking artifact is explicitly not a P1 ranking input. The historical OrbitTrace target, target-region events, target coordinates, target members, prior target rank, and target-containing outputs are forbidden.

## P1 model

For each frozen family:

1. Reconstruct the exact promoted-v8 pooled same-year centroid directly from that family's original seed events using the exact v8 source: circular mean in solar longitude and Sun-centered longitude, median ecliptic latitude, median geocentric speed.
2. Recompute and freeze the exact promoted-v8 multiplicity order with the promoted v8 scoring code. No label enters this reconstruction.
3. Express every seed as a four-dimensional residual in the inherited v8 geometry units: solar-longitude residual / 4°, Sun-centered longitude residual / 2° with latitude cosine factor, latitude residual / 2°, and speed residual / 2 km/s.
4. Pool seed-only residuals across the two years after within-year centering and estimate one common covariance using Oracle Approximating Shrinkage (OAS). No shower labels or added members enter this fit.
5. For each year, evaluate every non-seed target-excluded event under the current-year pooled centroid and the seed-only covariance.
6. The candidate stream region is the 99% four-dimensional chi-square ellipsoid. The local-background shell is the 99%–99.99% chi-square annulus. These probabilities are distributional definitions, not development-tuned radii.
7. Estimate a conservative local background intensity from the shell using the exact one-sided 95% Garwood Poisson upper bound. This intentionally overestimates, rather than underestimates, contamination.
8. Estimate stream amplitude as the immutable current-year seed count plus only positive non-seed excess over the conservative expected background inside the 99% ellipsoid, divided by 0.99 containment.
9. Compute a Gaussian stream intensity for each candidate under the seed-only covariance. Original v8 seed events never compete and never move.
10. If one non-seed event is compatible with multiple families, all compatible stream intensities compete simultaneously against a conservative local-background intensity. Assign the event only to the maximum-intensity family when that family's normalized posterior responsibility is strictly greater than 0.5. Otherwise leave the event unassigned.
11. Added events never refit centroids, covariance, background, stream amplitude, another family, or another growth step. The exact v8 multiplicity ranking is unchanged.

Thus P1 is a seeded local-background mixture model with conservative background competition, not a radius-expansion variant.

## Pre-truth freeze and evaluation

The complete expanded family membership payload must be serialized and SHA-256 frozen before any known-shower label is used for P1 evaluation. Label-based baseline and P1 evaluation use the exact promoted-v8 `evaluate_order` implementation and the exact recomputed v8 multiplicity order; no replacement evaluator or tie rule is permitted.

## Development gates

All integrity and scientific gates must pass in the single target-excluded 2022/2023 development execution.

Integrity:

- exact 226-family promoted-v8 ID universe and exact multiplicity order reconstructed from the promoted source;
- exact promoted-v8 baseline metrics reproduced;
- every original seed event preserved in its original family;
- no original seed event assigned elsewhere;
- added events do not seed or refit any model quantity;
- membership payload frozen before P1 truth evaluation;
- exact 20°–55° exclusion inherited from the frozen parser;
- no parameter/radius/threshold/variant search.

Scientific:

- expansion is non-vacuous;
- qualified known-shower matches do not regress below frozen v8's 95;
- recovery@100 does not regress below frozen v8's 58;
- top-100 dominant precision remains at least 0.65;
- macro F1 improves by at least +0.08 absolute over frozen v8.

Failure is `FAIL_PROBABILISTIC_MEMBERSHIP_P1_NO_GO` and permanently rejects this exact P1 architecture. A failure does not authorize nearby posterior, shell, covariance, confidence, or containment variants on the same result.

## Implementation-freeze correction record

Before any P1 scientific execution, source-only audit found that the initial wrapper had mistakenly read the predecessor v6 ranking artifact even though the protocol called for exact promoted v8. The wrapper was corrected before activation to recompute v8's pooled-centroid multiplicity ranking from source commit `c9d6c44704013ba0c9430100e98a29a56b453304` and to reuse v8's exact evaluator. No P1 membership rule, probability, covariance estimator, background rule, posterior cutoff, or development gate changed, and no P1 result existed when the correction was made.

## Next stages

A development pass does not establish superiority over Sugar/HDBSCAN and does not authorize target access. It authorizes a separately frozen matched-data literature comparison and then no-retuning external/held-out validation. Only after the method has met the required comparison and generalization gates may a final blind target-containing OrbitTrace deployment be frozen and executed.