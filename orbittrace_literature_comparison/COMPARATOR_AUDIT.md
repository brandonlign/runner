# OrbitTrace comparator audit

This audit records what each comparator actually is. Labels in this file are part of the frozen reporting contract.

## Existing internal baselines

All three existing comparators operate on the same frozen 128-event episode and the same internal four-dimensional geometry distance:

- solar-longitude displacement divided by 2°;
- Sun-centered ecliptic-longitude displacement, latitude-adjusted and divided by 2°;
- ecliptic-latitude displacement divided by 2°;
- geocentric-speed displacement divided by 2 km s⁻¹.

### Internal split statistic

Eight deterministic 64/64 reference-query splits are made. For every query event, the second-nearest reference distance is computed. The two strongest query events are averaged, negated, and the median across eight splits is the episode score.

### Internal local-density statistic

The score is the maximum number of episode events within internal distance 2.5 of any event, including the event itself.

### Internal DBSCAN

The frozen implementation uses the precomputed internal four-dimensional distance, `eps=2.5`, and `min_samples=4`. Its score is the largest non-noise cluster size.

**Classification:** internal baseline. It is not a reproduction of Sugar et al. (2017).

## Literature episode-track implementations

### Sugar et al. deterministic published core

The implementation uses the paper's six-dimensional Sun-centered geocentric vector:

1. cos solar longitude;
2. sin solar longitude;
3. sin(Sun-centered ecliptic longitude) × cos(ecliptic latitude);
4. cos(Sun-centered ecliptic longitude) × cos(ecliptic latitude);
5. sin(ecliptic latitude);
6. geocentric speed / 72 km s⁻¹.

The published `min_samples=5` is retained. Epsilon is transferred without shower labels using the paper's rule: the 23rd percentile of the fourth-nearest-neighbor distance over the exact filtered SonotaCo 2025 benchmark universe. That scalar is frozen before any SonotaCo 2023 run.

The continuous episode score is largest DBSCAN cluster size. The original paper's 1,000 uncertainty-clone recurrence and cluster-merging stage is not included in this deterministic-core result and must be evaluated on the separate catalogue track.

### Rudawska–Jenniskens D_SH single linkage

The implementation uses the exact Southworth–Hawkins orbital-distance equations, single linkage, the published `D_SH < 0.05` decision threshold, and the published six-member minimum. The continuous episode score is the negative linkage distance at which a connected component first reaches six members.

A four-member variant is also run because the frozen benchmark explicitly contains k=4 episodes. It was registered before scores and is always labelled **sparse adaptation**, never the published Rudawska–Jenniskens method.

## Catalogue-track methods

The following are not forced into the episode leaderboard:

- Sugar et al. uncertainty-aware recurrence pipeline;
- Peña-Asensio–Ferrari HDBSCAN with GEO, ORBIT, and LUTAB vectors;
- Brown et al. CMOR-style 3D wavelet activity-map search.

Their published unit of analysis is a large catalogue, multi-year activity map, or catalogue-level clustering result. Changing their minimum cluster sizes or search geometry merely to make them operate on 128-event k=4 episodes would produce new adapted methods, not faithful reproductions.

## Shared evaluation contract

Every episode-track method receives the identical event rows and uses the identical positive, calibration-negative, and held-out-negative episodes. All methods are evaluated with the same weak-stream AUROC, folds, conservative local rank p-values, pooled false-positive rates, reporting sectors, and k=4/6/8/12 recall. Published binary decisions are reported separately.
