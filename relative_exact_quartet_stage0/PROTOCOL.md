# Relative exact-quartet coherence: development preflight protocol

Status: fixed development-screen reproduction. This formulation was derived after PR #32's fresh 2026 result and screened only on the retired development years 2019, 2021, 2023, and 2025. No 2020/2022/2024 or 2026 event or label is read.

## Question

Can the exact minimum-diameter four-event clique be normalized by the window's robust local four-neighbor scale to retain k=4 sensitivity while removing dense-background false positives?

## Statistic

For each 128-event window in the unchanged physical feature space:

1. compute all pairwise distances using relative solar longitude / 2 degrees, Sun-centered ecliptic radiant longitude and latitude / 2 degrees, and geocentric speed / 2 km/s;
2. find the exact minimum pairwise diameter among every four-event clique by adding pairwise edges in increasing distance order until a K4 first appears;
3. compute every event's third-nearest-neighbor distance and take their median;
4. score the window by `log(median third-neighbor distance / exact K4 diameter)`.

The exact K4 search is partition invariant. The median scale is robust to a sparse 4-12-event stream and is intended to normalize structured local background density.

## Data and calibration

- exact PR #14 odd-year selected-event artifact from workflow `30855193522`;
- years 2019, 2021, 2023, 2025 only;
- remove solar longitude 20-55 degrees before all pools and scores;
- 128 events per window and a +/-10 degree local neighborhood;
- same-corpus empirical calibration within year and fixed 60-degree sector;
- 256 calibration and 64 independent audit windows per year-sector;
- two positive replicates for k in {4,6,8,12};
- strong comparators: unnormalized exact K4 diameter, the PR #31 LCC score, radius-2.5 local density, and epsilon-2.5/min-samples-4 clustering analogue.

## Frozen continuation gates

Every gate encoded in the source must pass, including pooled FPR <=0.06 at 0.05, pooled FPR <=0.02 at 0.01, worst-sector FPR <=0.12, weak AUROC >=0.80, preservation against LCC and density, complex-fold robustness, k=4 power and gain, and k=6/k=8 preservation.

No threshold, scale, normalization, seed, comparator, fold, blind interval, or endpoint may change after this runner reproduction. A failure closes the relative-quartet route.

Source SHA-256: `56b184abcfc11c095e376cb50f9e18fb0d351e854de5e2ad7228177338da841f`.
