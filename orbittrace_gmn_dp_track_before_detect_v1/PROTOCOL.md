# OrbitTrace dynamic-programming track-before-detect v1 — frozen protocol

## Status

This protocol freezes a genuinely different event-level detector before any scientific outcome is computed. It is not an RFT rescue and does not alter any failed RFT-v1 constant after seeing its result.

Scientific scope: target-excluded GMN 2022+2023 development only. SonotaCo 2013/2014 is not accessed by this experiment. MAARSY, DMS, and the protected OrbitTrace target remain inaccessible.

Firewall:
- protected solar longitude `[20°,55°]` removed before every scientific operation;
- `target_information_access=false`;
- `target_region_events_accessed=false`;
- `sonotaco_2013_2014_access=false`;
- `maarsy_scientific_access=false`;
- `dms_scientific_access=false`.

## 1. Motivation

Classic track-before-detect (TBD) methods accumulate weak evidence over a physically allowed trajectory before thresholding target existence, rather than requiring a local detection first. That is structurally attractive for sparse meteor showers: a real stream can be weak in every short solar-longitude interval yet coherent across many intervals.

Meteor-shower literature independently supports solar-longitude-resolved radiant/speed searches: Brown et al. (2010, Icarus 207, 66–81, DOI 10.1016/j.icarus.2009.11.015) used solar-longitude-binned wavelet searches, while Sugar et al. (2017, MAPS 52, 1048–1059, DOI 10.1111/maps.12856) showed the utility and limitations of density clustering in solar longitude/radiant/speed space. The general DP-TBD mechanism traces to Barniv (1985, IEEE TAES 21, 144–156) and subsequent performance work such as Tonissen & Evans (1996, IEEE TAES 32, 1440–1451, DOI 10.1109/7.543865).

The scientific change is therefore architectural: **accumulate unthresholded local evidence along a trajectory first; form a meteor-stream candidate second.** No HDBSCAN/DBSCAN candidates or scores enter the detector.

## 2. Data universe

Use only GMN 2022 and 2023 events from the frozen runtime after protected-region exclusion. Stack the two years into one virtual solar-longitude year for detection; event IDs retain year identity.

Required fields only:
1. solar longitude;
2. Sun-centered ecliptic radiant longitude;
3. ecliptic radiant latitude;
4. geocentric speed;
5. event ID.

No orbital elements, shower labels, SonotaCo features, target information, or source-generator metadata are allowed in detection.

## 3. Fixed state representation

Accessible solar longitude is divided into non-overlapping `2°` strata.

Every meteor is an observation state; there is **no local cluster/detection threshold** and no preselection by shower labels or candidate generators.

Physical distance between two meteor states is

`d^2 = (theta/3°)^2 + (log(v_i/v_j)/log(1.08))^2`,

where `theta` is radiant angular separation. These are fixed physical similarity scales inherited from the already-frozen OrbitTrace event representation, not fitted here.

## 4. Unthresholded emission evidence

For event/state `i` in stratum `b`:

- `n_bin(i)` = number of **other** events in the same 2° stratum with `d<=1`;
- `n_all(i)` = number of **other** events in the complete target-excluded 2022+2023 virtual-year pool with `d<=1`;
- `f_b = N_b / N_all`, the event fraction of stratum `b`.

Expected local count under the pooled background is `mu_i = f_b * n_all(i)`.

Frozen emission merit:

`e_i = log((n_bin(i)+0.5)/(mu_i+0.5))`.

The `0.5` Jeffreys pseudocount is fixed. Negative evidence is retained; no emission threshold or top-local-density filter is allowed.

## 5. Dynamic-programming track accumulation

A path moves only forward by one or two 2° strata. For each event in the destination stratum, predecessor proposals are the **8 nearest** events in physical distance from each permitted predecessor stratum. This sparse-neighbor rule is computational, deterministic, and frozen; it does not threshold local density.

For a transition spanning `g in {1,2}` strata, penalty is

`q(i,j) = d(i,j)^2 / (2g)`.

Dynamic-programming merit is

`V_j = e_j + max(0, max_i[V_i - q(i,j)])`.

The zero option starts a new path. Ties are resolved by event ID. No transition-distance cutoff is applied.

Only paths with at least **3 occupied strata** are eligible to form candidates.

## 6. Fixed candidate extraction

For each terminal state retain its single optimal backtracked path. Define path ranking merit

`T = V_terminal / sqrt(L)`,

where `L` is the number of states in the path. This is the frozen signal-accumulation normalization; no score weights are learned.

For bounded computation, inspect exactly the best **5,000** eligible terminal paths by `T`, with deterministic event-ID tie breaking. This is a candidate-extraction budget, not a scientifically tuned score threshold.

For each seed path:
1. fit one linear least-squares trajectory versus solar longitude in radiant-unit-vector components and log-speed;
2. normalize predicted radiant vectors;
3. collect all target-excluded GMN 2022+2023 events lying within the seed path's solar-longitude span whose standardized trajectory residual is `<=1.0` under the same `3° / 8%` physical scales;
4. require at least `4` final members;
5. candidate score remains the seed `T` merit; no label-informed reranking is allowed.

Process seeds in descending `T`. If a candidate's event-membership Jaccard overlap is `>=0.50` with any already accepted higher-scoring candidate, discard it as a duplicate. Otherwise retain it. No family deletion or merging occurs later.

## 7. Evaluation

Only after the complete candidate order is frozen may GMN known-shower labels be interpreted.

Use the established OrbitTrace qualification rule:
- eligible known shower has at least 4 events in the target-excluded 2022+2023 label universe;
- candidate qualifies for a shower if overlap >=4 events and candidate precision >=0.50;
- each shower is credited at its first qualifying rank.

Report:
- full-catalogue qualified showers;
- recovered@25/@50/@100/@500;
- top-100 dominant precision;
- MRR;
- median qualified candidates per recovered shower in top 500;
- candidate count.

## 8. Frozen comparison gates

Reference #839 active union metrics:
- recovered@25 = `22`;
- recovered@50 = `40`;
- recovered@100 = `75`;
- recovered@500 = `159`;
- top-100 dominant precision = `0.7645689180574315`;
- MRR = `0.019037817654898162`;
- qualified showers = `256`.

`PASS_DP_TBD_V1_GMN_DEVELOPMENT` requires all:
1. recovered@100 **>75**;
2. recovered@50 >=40;
3. recovered@25 >=22;
4. top-100 dominant precision >=0.7645689180574315;
5. MRR >=0.019037817654898162;
6. full-catalogue qualified showers >=200;
7. protected-data/provenance firewall passes.

A stricter reported diagnostic `BEATS_839_FULL` is true only if the PASS gates hold **and** recovered@500 >=159 and qualified showers >=256.

Otherwise v1 fails. No constant, neighborhood size, bin width, pseudocount, transition penalty, path-length rule, seed budget, residual tube, Jaccard rule, score, or gate may be changed after the first technically valid result.

## 9. Claim boundary

A GMN PASS means only that DP-TBD v1 is a materially better **GMN development candidate** than the active ranking baseline under the preregistered gates. It does not establish SonotaCo transfer or external validation. Any SonotaCo comparison would require a separate frozen protocol and SonotaCo must still be described as exposed development/benchmark data.
