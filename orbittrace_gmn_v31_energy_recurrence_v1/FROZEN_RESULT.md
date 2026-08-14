# Frozen result — GMN v31 multivariate energy recurrence v1

Binding run: `31762891111`  
Binding job: `94652771748`  
Execution head: `c04161a3bbd48ba90c008889c4a2a9bac1d00454`  
Artifact: `9205285772`  
Artifact digest: `sha256:d705162f462d616821b658488620987276ad664318c69478fb66efb7c89acf1c`

Frozen protocol commit: `277303eaa8c502bb1585d88e39a2dd144e09b93d`  
Frozen protocol blob: `9cb586bfb9c6296600edd7f6edf75a4ebfe50993`  
Frozen implementation commit: `a7af821fc7b3ec44c76e16522d79554e2e08ab7a`  
Frozen implementation blob: `b1c473abc0f088f6d906d509b5deb1a3f02a3de6`

Verdict: **FAIL_GMN_V31_ENERGY_RECURRENCE_V1**

All preregistered source, runtime, immutable-artifact, exact 23D reconstruction, centroid, fold, parent-margin, evaluator, and firewall checks passed. The first technically valid outcome is binding.

Exact v31 parent:

- @25 = **23**
- @50 = **41**
- @100 = **66**
- top-100 precision = **0.7229521515453452**
- MRR = **0.050244164168646674**
- qualified = **95**

Frozen 24D energy-recurrence fusion:

- @25 = **23**
- @50 = **41**
- @100 = **66**
- top-100 precision = **0.7151166537098473**
- MRR = **0.05017432008448316**
- qualified = **95**

Frozen local-only energy-recurrence order:

- @25 = **21**
- @50 = **40**
- @100 = **65**
- top-100 precision = **0.6362016282315841**
- MRR = **0.037127464463668186**
- qualified = **95**

Gate result:

- @100 >66: **FAIL** (66)
- @50 >=41: **PASS** (41)
- @25 >=23: **PASS** (23)
- precision >= parent: **FAIL**
- MRR >= parent: **FAIL**
- qualified =95: **PASS**

This is a binding scientific failure and does **not** authorize SonotaCo access.

Frozen hashes:

- energy-recurrence vector: `a370e68ba7f30c1ea298e7fbdecb4c9ee062898d961fdfb1d6dbaead4e4e7d64`
- candidate raw margin: `82c6d0928325f9099dca197167510599fabac3380f4c070106b9c93a498c7021`
- candidate fused order: `8d8bcab7932a7ed5cac658b30481477b25af2e5d69f579ad4a1abd5f3fbb5044`

Feature distribution (provenance only):

- all families: min `0.14583035566165262`, median `0.5957687326507133`, max `2.0059833353224152`
- positive families: min `0.14583035566165262`, median `0.5078011049229739`, max `1.544817241087757`
- nonpositive families: min `0.21082013972568497`, median `0.6845763285954077`, max `2.0059833353224152`

Scientific interpretation: the frozen full multivariate two-sample discrepancy has the expected aggregate direction—positive families have lower median cross-year energy distance—but appending it to exact v31 does not improve fixed-budget recovery and lowers precision/MRR. It is rejected rather than optimized.

Permanent closure: no result-informed rescue using squared-only energy statistic, unbiased U-statistic, Wasserstein/MMD/KS alternatives, radial projections, axis decompositions, kernels/bandwidths, trimming, sample-size correction, centroid alignment, whitening/covariance normalization, activity-phase augmentation, weights/transforms/subsets, metric/k/scaling/reference changes, or diversity/fusion changes.

Protected solar longitude 20°–55° remained inaccessible. No OrbitTrace target information/events, SonotaCo 2013/2014, MAARSY, or DMS was accessed.