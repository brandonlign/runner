# OrbitTrace sporadic-coordinate recurrent-EOM v1 — frozen binding protocol

## Goal
Test exactly one upstream use of the only new signal that has shown positive discrimination in recent experiments: survey-local seasonal-background contrast.

The frozen member-denoise experiment improved precision and MRR but lost one recovered shower (178 vs 179), showing the signal is informative but hard deletion is too destructive. The balanced local-graph/hierarchy line then failed label-free due severe percolation and is permanently closed.

This experiment therefore changes **only the point representation** while keeping the current recurrent-EOM detector architecture.

## Frozen baseline
Binding comparison is the density-synchronous recurrent-EOM GMN development winner from run `31852836840` / artifact `9238142199`:
- 2022 recovered@100 = 89
- 2023 recovered@100 = 90
- total recovered@100 = 179
- exact winner ordered-membership SHA256 `e8f374ad03e7072463118ee6440a54d96d11e3aab17202cfe336f866530224f2`

## Frozen seasonal-background coordinate
Use the already-frozen label-free weights from run `31912528972`, artifact `9254119364`:
- `SPORADIC_ANALOGUE_WEIGHTS.npy`
- SHA256 `648b88efc09192738dcce8eb2af15e215676dd62451a88cd9230337d80fd5347`
- weight definition `w = 2*c/(1+c)`, `c = r_bg/r_actual`
- therefore neutral survey-local background contrast is exactly `w=1`.

No weight recomputation, offset change, k change, transform change, or thresholding is authorized.

## Sole scientific change: GEO7
For every accessible target-excluded GMN event use the inherited GEO6 representation:

`[cos(sol), sin(sol), sin(lon)*cos(lat), cos(lon)*cos(lat), sin(lat), vg/72]`

and append one seventh coordinate:

`z = w - 1`.

Thus `z=0` is neutral local background, positive values are locally denser than seasonal controls, negative values are less dense. Because the frozen bounded weight lies in `(0,2)`, `z` naturally lies in `(-1,1)` like the angular GEO6 coordinates. There is **no learned or tuned scale factor**.

## Detector architecture held fixed
Run `hdbscan.HDBSCAN` with the exact current recurrent-EOM settings:
- `min_cluster_size=10`
- `min_samples=10`
- `metric='euclidean'`
- `cluster_selection_method='eom'`
- `cluster_selection_epsilon=0.0`
- `allow_single_cluster=False`
- `prediction_data=False`

Then apply the exact existing recurrent-EOM stability, EOM node selection, candidate extraction, and ranking code from `orbittrace_recurrent_eom_hdbscan_v1` without modification.

No density-sync refinement, reranking, member deletion, graph construction, extra gate, feature fitting, or target-specific operation is allowed.

## Pretruth freeze
Before indexing any known-shower label value, persist:
- exact source/artifact hashes;
- exact event counts and target exclusion;
- exact GEO7 coordinate definition and frozen weight hash;
- HDBSCAN selected recurrent nodes;
- full ordered candidate memberships;
- ordered-membership SHA256;
- candidate count and largest-family diagnostics;
- firewall state.

## Binding GMN gate
Compare the exact frozen GEO7 recurrent-EOM candidate order against the binding 179-recovery winner.

PASS requires all of:
1. total recovered@100 >= **184** (+5 minimum);
2. 2022 recovered@50 >= baseline and recovered@100 >= 89;
3. 2023 recovered@50 >= baseline and recovered@100 >= 90;
4. top-100 dominant precision is not lower in either year;
5. MRR is not lower in either year;
6. median top-500 fragmentation is not higher in either year;
7. at least 100 GEO7 recurrent candidate families exist and no selected family contains >1% of all accessible events;
8. the GEO7 ordered membership differs from the frozen winner;
9. all firewall and reproducibility checks pass.

Anything else is a FAIL. No post-result rescaling of coordinate 7, thresholding, blending, parameter search, or scientific rescue is authorized for v1.

## Firewall
- GMN 2022+2023 development only.
- Solar longitude 20°–55° excluded before all method operations.
- OrbitTrace target information/protected-region events forbidden.
- SonotaCo 2013/2014, ASFN, EFN, AMOS, MAARSY, DMS not accessed in this GMN endpoint.

## Transfer rule
A GMN PASS is only progress toward the goal. It must then reproduce and pass a separately frozen exposed-SonotaCo comparison against the literature comparator before any claim of improved transfer. Broad generalization still requires a genuinely untouched external dataset.