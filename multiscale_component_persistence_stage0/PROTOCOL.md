# Multiscale component-persistence coherence: frozen development screen

Status: frozen development-screen reproduction on GMN 2019, 2021, 2023, and 2025 only. No 2020/2022/2024 or 2026 confirmation event, label, score, or endpoint is read.

## Scientific question

Can a partition-invariant multiscale topology statistic distinguish a genuinely compact sparse stream component from an accidental dense quartet by requiring both internal connectivity and separation from the surrounding local background?

## Statistic

For each 128-event local window in the unchanged physical feature space:

1. compute the complete physical-distance graph using relative solar longitude / 2 degrees, Sun-centered ecliptic radiant longitude and latitude / 2 degrees, and geocentric speed / 2 km/s;
2. build the exact single-linkage hierarchy with Kruskal's algorithm;
3. for every dendrogram component containing 4 through 12 events, record its internal connection threshold and the next edge at which it merges with outside background;
4. score the window by the maximum `log(external merge distance / internal connection distance)`.

The candidate has no reference/query partition and no fixed clustering radius. It rewards a sparse component only if it persists across a nontrivial interval of distance scales.

## Frozen development benchmark

- exact PR #14 odd-year selected-event artifact from workflow `30855193522`;
- remove solar longitude 20°–55° before every pool, window, score, fold, and endpoint;
- 128-event windows in a ±10° solar-longitude neighborhood;
- same-corpus empirical calibration within year and fixed 60° sector;
- 256 calibration and 64 independent audit windows per sector;
- two positive replicates for k in {4,6,8,12};
- fixed comparators: exact K4 diameter, PR #32 nearest-neighbor quartet diameter, unchanged PR #31 LCC, local density, and DBSCAN analogue;
- fixed gates for calibration, weak AUROC, comparator preservation, complex-fold robustness, k=4 power, k=6/k=8 preservation, and monotonicity.

Any failed gate kills the formulation. No component-size range, linkage rule, persistence ratio, feature scale, calibration count, seed, threshold, comparator, fold, blind interval, or endpoint may change after this run.

Source SHA-256: `66284b308fb0dc3356dc9c3d7df4b68816154556ba1b902773cca939ae0dd257`.
