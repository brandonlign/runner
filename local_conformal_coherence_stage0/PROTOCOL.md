# Local conformal coherence: frozen Stage-0 protocol

## Question

Can a meteor-stream search produce locally calibrated, event-level evidence under the real nonstationary sporadic background, rather than reporting an uncalibrated cluster score or relying on a synthetic global null?

This is a calibration method, not another clustering architecture. A fixed second-nearest-neighbor physical-coherence score is converted into split-conformal p-values using calibration meteors from the same year and adjacent-month seasonal stratum. The score function is fitted only on a disjoint reference split.

## Literature boundary

This protocol does **not** claim that false-positive modelling, null catalogs, or multiple-comparison correction are new to meteor science.

- Galligan (2003, MNRAS 340, 893) tested stream associations against similar regions of orbital-element space.
- Moorhead (2016, MNRAS 455, 4329) constructed shower analogues and selected per-shower D cutoffs at a chosen false-positive rate.
- Shober (2026, ApJ; arXiv:2602.16845) used KDE sporadic null realizations, local z-scores, DBSCAN, and a Dunn-Sidak family-wise adjustment.

The candidate contribution being tested is narrower: cross-fitted **event-level conformal calibration on real, locally matched meteor backgrounds**, with explicit empirical calibration gates down to p = 0.001. A later stage may use these p-values with an arbitrary-dependence multiple-testing rule; this Stage-0 PR does not claim catalog discoveries or FDR control.

## Frozen design

1. Load the exact selected GMN event artifact and the exact frozen Stage-0 baseline parser from PR #14.
2. Exclude every event with solar longitude from 20.0 degrees through 55.0 degrees before constructing any stratum or score. This broad blind interval contains GhostStream-April-36.9. No GhostStream radiant, speed, orbit, membership, or detection score may be used.
3. Use only events labelled sporadic by the source audit; the existing ESV exclusion in the frozen parser remains active.
4. Within each year, merge adjacent calendar months until at least 4,500 events are available. The merge uses counts only.
5. Stable-hash each event into four partitions:
   - partitions 0 and 1: reference set,
   - partition 2: calibration set,
   - partition 3: untouched null-test set.
6. Represent each event by fixed physical coordinates:
   - solar longitude on the unit circle,
   - Sun-centered ecliptic radiant on the unit sphere,
   - geocentric speed,
   - fixed scales of 2 degrees and 2 km/s.
7. Fit a nearest-neighbor index on the reference set only. The evidence score is the negative distance to the **second** reference neighbor; larger values mean more locally coherent events. The second neighbor is frozen from split geometry before any shower-power result: a weak 4–8-member stream sends only about 2–4 members into the 50% reference set, so an eighth-neighbor score could be perfectly calibrated while being structurally unable to detect the target regime.
8. Convert each test score to the conservative split-conformal p-value

   `p = (1 + number of calibration scores >= test score) / (n_calibration + 1)`.

9. Compare the local seasonal calibration with a deliberately unmatched global calibration. This is an ablation: local conditioning must repair a measurable worst-stratum failure, not merely reproduce the global result.

## Frozen continuation gates

All gates must pass before any real-shower power benchmark is allowed:

- every seasonal group has at least 500 calibration and 500 test events;
- pooled upper 95% bounds on Type-I error are at most 0.11, 0.06, 0.015, and 0.003 at alpha 0.10, 0.05, 0.01, and 0.001;
- pooled anti-conservative empirical-CDF excess is at most 0.015;
- worst seasonal-stratum Type-I error at alpha 0.05 is at most 0.08;
- local matching improves both worst-stratum anti-conservative CDF excess and worst-stratum alpha-0.05 error relative to global unmatched calibration.

Passing this audit means only that the p-values are empirically calibrated enough to earn a complex-held-out real-shower power test. It does not establish discovery power, catalog-level error control, or methodological superiority.
