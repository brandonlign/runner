# StreamTube Stage-0 protocol

**Frozen before authoritative execution:** 2026-08-03.

## Question

Can a physically constrained drifting stream-tube detector recover sparse meteor streams that are too weak to form a significant static density peak, without increasing catalog-level false detections?

This is a kill test. It is not part of GhostStream and must not be applied to GhostStream unless the continuation gates pass on independent benchmarks.

## Data

- Real sporadic background: the shower-removed SonotaCo subset released with Shober (2026).
- File MD5: `f57a2ac71832ceca9227441c00b8cd58`.
- A conservative mask removes the known M2026-A1 / removed 87 Virginids concentration before fitting the null.
- Coordinates: solar longitude, Sun-centered ecliptic longitude, ecliptic latitude, and geocentric speed.

## Detectors

1. **Static tube baseline:** integrates a Poisson likelihood-ratio score over finite-duration tubes with zero radiant drift.
2. **Drifting tube:** uses the same score, durations, widths, background model, and catalog-level calibration, but scans a frozen bank of nonzero radiant-drift slopes.

The Stage-0 grid is intentionally coarse. It tests whether drift integration has enough signal to justify a later fine-grid benchmark; it is not a final detector.

## Error control

For each detector, the threshold is selected from the distribution of the maximum score over the complete template bank in null catalogs. This controls the probability of any catalog-level false detection at nominal `alpha = 0.10` within the frozen Stage-0 search.

A second null uses a sharper background than the fitted calibration model to test sensitivity to background misspecification.

## Injection test

- Injected stream sizes: `k = 6, 8, 12, 20`.
- Every injected stream has nonzero radiant drift drawn from the frozen slope bank.
- Recovery requires a reported candidate above the calibrated threshold and spatial/kinematic agreement with the injection.
- The comparison of primary interest is the average recovery at `k = 6, 8`.

## Frozen continuation gates

All gates must pass:

1. Drift-tube probability of any false detection on ideal nulls is at most `0.15`.
2. Drift-tube weak-stream recovery exceeds the static baseline by at least `0.10`.
3. Drift-tube recovery at `k = 12, 20` is no more than `0.05` below the static baseline.
4. Drift-tube probability of any false detection under the sharper-background stress test is at most `0.20`.

Failure of any gate gives `KILL_OR_REDESIGN_STREAM_TUBE`. Passing all gates only permits a fine-grid comparison against HDBSCAN, DBSCAN, fixed-bin/wavelet searches, and known weak real showers.
