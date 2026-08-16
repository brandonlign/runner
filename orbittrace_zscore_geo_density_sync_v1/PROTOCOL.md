# OrbitTrace Z-score GEO density-synchronous recurrent-EOM v1 — frozen protocol

## Scientific goal
Test one literature-motivated, survey-adaptive physical similarity change aimed directly at transfer: replace the hand-scaled Euclidean GEO6 geometry with component-wise Z-score-standardized GEO6 before HDBSCAN, while keeping the current density-synchronous recurrent-EOM architecture unchanged.

This is motivated by two independent published results on meteor association/clustering:
- Peña-Asensio & Sánchez-Lozano (2024) found standardized Euclidean with the geocentric GEO vector to be the strongest tested association metric on CAMS.
- Peña-Asensio & Ferrari (2025) applied HDBSCAN to meteoroid streams after standardizing every vector component to zero mean and unit variance, and found EOM superior to leaf selection.

The OrbitTrace repository has no prior `seuclidean`, standardized-Euclidean, or Z-score-GEO detector experiment found in the pre-run audit. Density/background correction lines are closed and are not part of this test.

## Binding baseline
Compare only against the frozen density-synchronous recurrent-EOM GMN winner:
- run `31852836840`
- artifact `9238142199`
- 2022 recovered@100 = 89
- 2023 recovered@100 = 90
- total recovered@100 = 179
- exact ordered-membership SHA256 `e8f374ad03e7072463118ee6440a54d96d11e3aab17202cfe336f866530224f2`

The baseline is read from the frozen artifact; it is not recomputed, avoiding CPU-dependent HDBSCAN reconstruction as a comparison requirement.

## Data/firewall
- GMN 2022+2023 development only.
- Solar longitude 20°–55° excluded before computing any normalization statistic or clustering operation.
- OrbitTrace target information/protected-region events forbidden.
- Known-shower labels cannot be indexed until the complete standardized hierarchy, selected nodes, memberships, and order are persisted.
- SonotaCo 2013/2014, ASFN, EFN, AMOS, MAARSY, DMS are not accessed in this GMN endpoint.

## Frozen representation
Start from the exact inherited GEO6 representation:

`[cos(sol), sin(sol), sin(lon)*cos(lat), cos(lon)*cos(lat), sin(lat), vg/72]`

Across the complete accessible target-excluded GMN 2022+2023 development set, for each of the six components compute:

`mu_j = mean(X_j)`

`sigma_j = sqrt(mean((X_j-mu_j)^2))`

and transform:

`Z_j = (X_j-mu_j)/sigma_j`.

This is population Z-score normalization (`ddof=0`). All six means and standard deviations are frozen in pretruth output.

No labels, shower identities, target information, seasonal-background weights, orbital elements, uncertainty proxies, covariance whitening, learned metric, axis tuning, or post-hoc scaling enter the transform.

For later survey transfer, the algorithmic rule is fixed now: compute the same unlabeled component-wise Z-score statistics independently on that survey's accessible analysis corpus before clustering. GMN-derived numerical means/stds are not transferred to another survey.

## Detector architecture held fixed
Fit exact `hdbscan==0.8.43` with:
- `min_cluster_size=10`
- `min_samples=10`
- `metric='euclidean'`
- `cluster_selection_method='eom'`
- `cluster_selection_epsilon=0.0`
- `allow_single_cluster=False`
- `prediction_data=False`

Then apply the exact existing density-synchronous recurrent-EOM objective and node selection:
- ordinary HDBSCAN stability unchanged;
- annual recurrent bookkeeping unchanged;
- density-synchronous alive-mass objective unchanged;
- candidate extraction/ranking unchanged.

The sole scientific change is `GEO6 -> Z-score(GEO6)` before HDBSCAN.

## Pretruth freeze
Before any known-shower label is indexed, persist:
- input/source hashes and event counts;
- six `mu_j` and `sigma_j` values;
- standardized component means/stds as numerical audit;
- condensed-tree SHA256;
- selected density-synchronous nodes;
- full ordered candidate memberships;
- candidate count, largest-family size, ordered-membership SHA256;
- firewall state.

## Binding GMN success gate
PASS requires all of:
1. total recovered@100 >= **184** (+5 over 179);
2. 2022 recovered@50 not below frozen winner and recovered@100 >= 89;
3. 2023 recovered@50 not below frozen winner and recovered@100 >= 90;
4. top-100 dominant precision not lower in either year;
5. MRR not lower in either year;
6. median top-500 fragmentation not higher in either year;
7. at least 100 candidate families and largest selected family <=1% of accessible events;
8. ordered memberships differ from the frozen winner;
9. all reproducibility/firewall checks pass.

Anything else is FAIL. No post-result alternative standardization, per-year standardization, robust scaling, covariance whitening, feature dropping, axis weighting, or HDBSCAN tuning is authorized for v1.

## Goal/transfer rule
A GMN PASS is only the first goal-level step. It must then pass one separately frozen exposed-SonotaCo transfer benchmark against the existing frozen literature comparators using the same algorithmic rule (survey-local unlabeled Z-score normalization). Broad superiority/generalization still requires a genuinely untouched external survey.