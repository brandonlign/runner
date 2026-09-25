# Noise-deconvolved covariance-flow alignment: frozen Stage-0

Status: new candidate following the decisive failure of exact present-day compactness matching. GhostStream is excluded.

## Motivation

The matched-null benchmark tested 86,400 real sporadic groups. None matched the controls' median or 90th-percentile present-day `D_SH`, even though 92.99% matched the local orbit regime. The exact-matching formulation is therefore killed rather than relaxed.

This candidate conditions on compactness differently. For each group, it preserves the eigenvalue spectrum of that group's own present-day covariance and randomizes only the covariance **orientation**. It then asks whether the observed orientation is unusually stable under the local gravitational flow.

## Narrow novelty claim under test

Numerical integration, covariance propagation, clone sampling, chaos indicators, and evolving D-criteria are established. The provisional contribution is the combination of:

1. subtracting event-level measurement covariance from the observed group covariance;
2. restricting the covariance to the local tangent space of the Earth-crossing orbit manifold;
3. preserving the tangent covariance eigenvalues exactly while randomizing its orientation;
4. scoring alignment with a local N-body state-transition map;
5. comparing real shower groups with orbit-region-matched sporadic groups using a self-normalized orientation percentile.

A pass would justify a broader literature and dynamics benchmark. It would not establish novelty by itself.

## Fixed data and groups

Use the checksum-verified artifact from runner workflow `30849390889`, artifact `8869994126`.

Controls: IAU 4/GEM, 6/LYR, 7/PER, and 13/LEO. Years: 2019, 2021, 2023, 2025.

Shower groups are the same four disjoint 20-event clone-ready groups defined in the static-matching protocol.

For every shower group, construct four sporadic groups:

- IAU `-1` only;
- same control month;
- exactly five events from every frozen year;
- nearest-neighbor construction around four distinct local-orbit seeds;
- standardized median orbit-regime distance no greater than `0.50`;
- no sporadic event used more than four times per control.

Present-day `D_SH` is not matched because the prior gate proved that requirement infeasible. Each group's orientation score preserves its own covariance eigenvalues and is therefore self-normalized for scale.

## Orbital coordinates and noise deconvolution

Use the five-dimensional nonsingular orbit vector

`[log(a), e cos(varpi), e sin(varpi), sin(i/2) cos(Omega), sin(i/2) sin(Omega)]`,

where `varpi = omega + Omega`.

For each event, transform the diagonal reported uncertainties in `(a, e, i, omega, Omega)` to this vector with a fixed central-difference Jacobian. Average the event covariance matrices to obtain the group's measurement covariance.

Subtract measurement covariance from the sample covariance and project negative eigenvalues to zero. Add a fixed ridge of `1e-10` times the trace before numerical scoring. The raw, non-deconvolved covariance is retained as an ablation.

## Earth-crossing tangent space

At the group medoid, define the node-distance constraint as the heliocentric radius at whichever node is closest to 1 au. Compute its numerical gradient in the five-dimensional orbit coordinates.

Use an orthonormal four-dimensional basis for the null space of that gradient. Project the deconvolved covariance into this tangent space.

## Local gravitational-flow map

Use `rebound==5.0.1` with its packaged outer-Solar-System initial conditions and IAS15.

For each group medoid:

- add the nominal massless orbit at a fixed packaged Solar-System epoch;
- add central positive and negative perturbations along each of the five orbit coordinates;
- integrate backward 100 years;
- estimate the five-by-five local flow Jacobian by central finite differences;
- record relative planetary energy error and reject a group if it exceeds `1e-8`.

The packaged epoch is an acknowledged Stage-0 approximation. A pass requires a later ephemeris-accurate confirmation.

## Orientation percentile

Let the four nonnegative tangent-covariance eigenvalues be fixed. Generate 2,000 deterministic Haar-random rotations in four dimensions. Lift every rotated covariance back to five dimensions and propagate it with the same local flow Jacobian.

Score volume growth as the change in the log pseudo-determinant of the four largest propagated covariance eigenvalues. Lower growth is more dynamically stable.

The orientation percentile is

`(1 + number of rotations with growth <= observed growth) / 2001`.

Lower percentiles indicate unusually stable observed orientation.

## Frozen evaluation

Primary classifier score: `-log10(orientation percentile)`.

Compare 16 shower groups with 64 orbit-region-matched sporadic groups.

All continuation gates must pass:

1. all groups integrate with relative planetary energy error at most `1e-8`;
2. shower-versus-sporadic AUROC is at least `0.75`;
3. at least three of four controls have median shower orientation percentile at most `0.20`;
4. at least 10 of 16 shower groups have percentile at most `0.20`;
5. at most 20% of sporadic groups have percentile at most `0.20`;
6. absolute Spearman correlation between classifier score and median log uncertainty is at most `0.30`;
7. deconvolved AUROC is no more than `0.05` worse than raw-covariance AUROC;
8. no single control contributes more than half of the total shower-sporadic score separation.

## Kill rules

Kill the candidate if any gate fails. Do not rescue it by changing the lookback horizon, rotation count, tangent constraint, covariance coordinates, uncertainty subtraction, control showers, classifier threshold, or group selection after seeing results.

Do not apply this method to GhostStream unless every gate passes and a later ephemeris-accurate benchmark confirms the result.
