# OrbitTrace wavelet catalogue v3 development

## Purpose

Build a target-free catalogue candidate generator around the prospectively promoted dual-output episode detector.

The episode method is already frozen as:

- sole continuous score: `brown2010_wavelet_episode_core`;
- additive sparse rescue: fixed4 empirical `p <= 1/129`;
- reporting decision: `(p_wavelet <= 0.05) OR (p_fixed4 <= 1/129)`.

The rejected support-normalized fixed4 wrapper remains a negative result. Catalogue v3 therefore generates candidates directly from wavelet local maxima rather than reranking fixed4 quartets.

## Development panel and blindness

Development years: **2022 and 2023 only**.

Every row with solar longitude in the closed interval **20°–55°** is removed from geometry before shower-label normalization or storage. No 2024–2026 catalogue is loaded. No OrbitTrace coordinate, member identity, canonical artifact, activity interval, or target exception is available.

After the target interval is removed, labels are stored in a separate lookup used only by the final evaluation function. Candidate scanning, exact rescoring, component formation, cross-year linking, and ranking receive no label lookup and contain no label-dependent branch.

## Frozen candidate generation

1. Parse the exact GMN monthly catalogues using the validated fixed4 wrapper parser and data-source interfaces.
2. Use overlapping 10° solar-longitude windows stepped by 5°. The half-window offset removes dependence on one arbitrary bin boundary.
3. Use the frozen wavelet metric: 4° angular probe, 10% fractional speed probe, radius-4 truncation, dimension-3 Mexican-hat kernel.
4. For each anchor, use a 32-neighbor approximate prefilter only to reject anchors that cannot have four events in the positive wavelet lobe.
5. For surviving anchors, shortlist 256 approximate neighbors, exact-rank them in the frozen wavelet metric, and retain the nearest 127 plus the anchor, matching the 128-event benchmark.
6. Retain positive-lobe membership at `r² < 3`, where the frozen Mexican-hat kernel changes sign. Require at least four members.
7. Calibrate wavelet and fixed4 scores separately in each 10° Mondrian bin with 128 source-preserving background episodes.
8. Detect an anchor when `p_wavelet <= 0.05` or `p_fixed4 <= 1/129`.
9. Exact-rescore every provisionally retained anchor against every event in its 10° window. Approximate scores cannot enter the final candidate table.
10. Form yearly components by connecting each retained anchor to its positive-lobe members. Require at least four events and two retained anchors.
11. Link components across years with the inherited frozen centroid radius `1.5` and require recurrence in both development years.

## Ranking and rescue boundary

The main catalogue ranking is wavelet-only:

1. recurrent year count;
2. Fisher sum of the best empirical wavelet p-value from each year;
3. maximum continuous wavelet coefficient;
4. event support.

Fixed4 never changes this ordering. Families detected only by the fixed4 minimum-p rescue are reported in a separate rescue queue.

## Development gates

The development run passes only when:

- the exact frozen wavelet core passes all self-tests;
- the 20°–55° interval is removed before label normalization;
- the loaded years are exactly 2022–2023;
- each year has at least 30 supported Mondrian bins;
- at least 50 recurrent wavelet-ranked families are produced;
- top-100 known-shower recovery is at least 80% of the fixed4 persistence baseline on the same 2022–2023 panel;
- top-100 dominant-label precision is at least 0.50;
- qualified known-shower matches are at least 60% of the fixed4 persistence baseline.

A pass authorizes a separately frozen target-excluded validation on 2024–2025. It does not authorize a 2026 scan, an OrbitTrace reveal, a blind rediscovery claim, or replacement of the historical HDBSCAN discovery account.
