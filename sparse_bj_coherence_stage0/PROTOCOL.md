# Sparse Berk-Jones coherence: development preflight protocol

Status: fixed development-screen reproduction on 2019/2021/2023/2025 only. No consumed even-year or 2026 confirmation event or label is read.

## Question

Can a partition-invariant sparse order-statistic test aggregate four to eight locally coherent events more effectively than selecting only the single strongest quartet or randomly splitting reference and query events?

## Statistic

For each 128-event window in the unchanged four-dimensional physical feature space:

1. compute each event's distance to its third-nearest other event;
2. divide all 128 third-neighbor distances by their window median;
3. use an inner same-corpus empirical null to convert the 128 normalized distances to lower-tail event p-values;
4. calculate a one-sided Berk-Jones statistic over the first 1 through 8 ordered event p-values;
5. use an independent outer same-corpus empirical window null to calibrate the adaptive Berk-Jones maximum.

The complete statistic is partition invariant. The outer calibration absorbs dependence among event p-values and selection over sparse subset sizes.

## Frozen screen

- exact PR #14 odd-year selected-event artifact from workflow `30855193522`;
- remove solar longitude 20-55 degrees before all pools and scores;
- 128-event +/-10 degree windows;
- year-by-60-degree-sector same-corpus calibration;
- 64 inner, 64 outer, and 32 independent audit windows per sector;
- one positive replicate for k in {4,6,8,12};
- comparators: exact K4 diameter, PR #31 LCC, radius-2.5 density, and epsilon-2.5 clustering analogue;
- fixed gates for FPR, worst-sector behavior, AUROC, comparator preservation, and k=4/k=6/k=8 recall.

No subset-size limit, normalization, calibration count, seed, threshold, comparator, blind interval, or endpoint may change after this runner reproduction. A failure closes the sparse order-statistic route.

Source SHA-256: `90b550ee4f682d05a81b1b6a6ea5e8ca6c2d3264b4dee5769e213dca95ef7de6`.
