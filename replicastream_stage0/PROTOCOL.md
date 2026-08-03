# ReplicaStream Stage-0 protocol

**Frozen before authoritative real-data execution: 2026-08-03.**

## Question

Can a meteor-stream search use annual replicability as part of discovery—not merely as a post-hoc check—to retain weak recurrent streams while rejecting equally large one-year concentrations?

This is a kill test. It is separate from GhostStream and must not be applied to GhostStream unless every continuation gate passes on independent data.

## Data

- Real survey background: the shower-removed SonotaCo subset released with Shober (2026).
- File MD5: `f57a2ac71832ceca9227441c00b8cd58`.
- Fifteen separate observing years, 2009–2023, are retained rather than collapsed into a virtual year.
- A conservative mask removes the known M2026-A1 / removed 87 Virginids concentration before fitting the background.
- Search coordinates: solar longitude, Sun-centered ecliptic longitude, ecliptic latitude, and geocentric speed.

## Detectors

1. **Pooled virtual-year baseline:** all years are summed before scanning.
2. **Pooled-plus-confirmation baseline:** a pooled excess must also show nominal one-sided support (`p <= 0.05`) in at least three individual years. Its full search maximum is separately null-calibrated, so it is not penalized by inheriting the pooled threshold.
3. **ReplicaStream:** each template produces one annual excess p-value per year. The score is the third-strongest annual evidence (`r = 3`), and the maximum over all locations and widths is empirically calibrated from complete null catalogs.

ReplicaStream therefore rewards evidence distributed across at least three years and cannot be raised by one exceptional year alone.

## Catalog-level error control

Each detector receives its own threshold from the distribution of its maximum over the entire frozen template bank in simulated null catalogs. The nominal probability of any catalog-level false detection is `alpha = 0.10`.

## Stress tests

- **One-year artifact:** the same total number of injected events as a recurrent stream is concentrated into one year.
- **Shared annual structure:** all years receive the same smooth multiplicative spatial distortion before sampling, representing persistent observing-geometry or reduction structure omitted from the fitted independent-year null.

## Injection test

- Recurrent streams are active in five randomly selected years.
- Injected events per active year: `4, 6, 8, 12`.
- Weak comparison: average recovery at `4` and `6` events per active year.
- Strong comparison: average recovery at `8` and `12` events per active year.
- Recovery requires a selected template within the frozen neighborhood of the injection.

## Frozen continuation gates

All gates must pass:

1. ReplicaStream ideal-null catalog FWER is at most `0.15`.
2. Weak recurrent recovery is no more than `0.10` below the strongest baseline.
3. Weak one-year-artifact detection is at most `0.20`.
4. Shared-structure null catalog FWER is at most `0.20`.
5. Weak recurrence-margin gain over the strongest baseline is at least `0.15`.
6. Strong recurrent recovery is no more than `0.05` below the strongest baseline.

Failure of any gate gives `KILL_OR_REDESIGN_REPLICASTREAM`. Passing all gates permits—not proves—a larger benchmark against known weak showers, held-out-year confirmation, network/geographic splits, and alternative values of `r` with multiplicity control.
