# Frozen protocol — GMN v31 directional morphology recurrence v1

## Scientific role

This is a **target-excluded GMN 2022/2023 development successor** to the frozen v31 local-geometry-margin OOF method. It is selected entirely outside SonotaCo and must not access SonotaCo 2013/2014, the protected OrbitTrace target solar-longitude interval 20°–55°, OrbitTrace target information/events, MAARSY, or DMS.

The first technically valid result produced under this protocol is binding.

## Why this is a distinct mechanism

Recent target-excluded v31 successors established that adding a genuinely new physical observable can change the ranking, but the following exact lanes are already closed and are not being retried here:

- activity-profile distribution statistics and alternate activity-profile summaries;
- radial-coherence distribution statistics and alternate radial-statistic/transform rescues;
- centroid-distance / annual-width ratios;
- annual member-count or detector-component balance;
- removal/reweighting of the duplicated member-balance coordinate;
- all earlier v32–v60 SonotaCo-driven metric, scaling, reference, fusion, diversity, component-transfer, rank-algebra, and related rescue families preserved by the repository.

This successor does **not** compare one-dimensional radial distributions, activity distributions, widths, counts, centroids, or component multiplicities. It tests a different physical proposition: a real recurrent stream should tend to preserve the **directional shape and orientation of its local member cloud** across independent years, even when its radial spread or activity profile changes.

## Immutable parent and data

Parent: exact target-excluded GMN v31 offline development package used by the already-binding activity-profile/radial-coherence successors.

Required immutable identities:

- candidate count: 226 hard families;
- parent feature dimension: 23;
- parent feature SHA-256: `fea3b063772c75b675e37a227b53a4aa3c5b86fdcbfcef1487b1e1448689cdf5`;
- centroid SHA-256: `a53b9862f1ec3d751745f80aec2625d7904128474c9263c55ea953cf60d0621f`;
- exact parent raw OOF margin SHA-256: `f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`;
- P19 prelabel payload SHA-256: `276129ef8f9f31a1f8e7b1570c15f5e67ed1a7274f293f5da65bab60f86e32b8`;
- pooled-year-centroid v8 result SHA-256: `fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b`;
- offline manifest SHA-256: `16fb5ef3cd8dbbb3873e9bc23874fe7da3db68498772a5e992fbceed6cb980d7`;
- active ranker source SHA-256: `dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990`.

Exact parent control metrics must reproduce before the candidate result is accepted:

- recovered@25 = 23
- recovered@50 = 41
- recovered@100 = 66
- top-100 dominant precision = 0.7229521515453452
- MRR = 0.050244164168646674
- qualified matches = 95

The immutable hard-order control must also reproduce:

- recovered@25 = 21
- recovered@50 = 38
- recovered@100 = 59
- top-100 dominant precision = 0.6884631112636006
- MRR = 0.046734076055452344
- qualified matches = 95

## Sole new coordinate

For each family and each year `y ∈ {2022, 2023}`, use only that family’s already-fixed member events and its already-fixed annual centroid.

For member event `e` and annual centroid `c_y`, form the signed three-coordinate residual vector

`r(e,y) = [ dlon/4°, dlat/4°, log(Vg_e/Vg_c)/log(1.10) ]`,

where:

- `dlon` is the wrapped signed ecliptic-longitude difference in `[-180°,180°)`;
- `dlat` is signed ecliptic-latitude difference;
- `Vg_e` and `Vg_c` must both be positive and finite.

These are the same fixed physical coordinate scales already used by the frozen fixed4 geometry; there is no scale search.

For each year, define the uncentered residual second-moment tensor around the fixed annual centroid

`M_y = mean_e [ r(e,y) r(e,y)^T ]`.

Then define the trace-normalized directional-shape tensor

`S_y = M_y / trace(M_y)` when `trace(M_y) > 0`, and the all-zero 3×3 tensor when the trace is exactly zero.

The **only appended feature** is

`morphology_discrepancy = || S_2022 - S_2023 ||_F / sqrt(2)`.

For positive-semidefinite trace-one tensors this lies in `[0,1]`; exact-zero annual tensors remain well-defined by the fixed zero convention. No eigenvalue sorting, principal-axis sign convention, angular threshold, covariance shrinkage, determinant, eccentricity, anisotropy ratio, trace/width companion, radial statistic, or additional morphology coordinate is permitted.

The parent 226×23 feature matrix is extended to exactly 226×24 by appending this single coordinate.

## Frozen training/ranking path

Nothing else changes from the target-excluded v31 development evaluator:

1. fixed strict five-fold groups and labels from the authoritative offline package;
2. fold-training ordinary mean/std z-scaling of all candidate features, with exact zero-std fallback to 1;
3. ordinary Euclidean k=1 distance to nearest positive and nearest nonpositive training family;
4. OOF margin `d_nonpositive - d_positive`;
5. exact inherited diversity order with `(lambda=0.8, scale=1.0)`;
6. one equal 1-based rank-sum fusion with the immutable hard order;
7. unchanged monotone GMN development evaluator.

No feature selection, sign flip, transform, weight, threshold, metric, k, scaling, reference-pool, diversity, fusion, source, candidate, membership, fold, or evaluator search is allowed.

## Binding promotion gates

PASS requires **all** of the following on the first technically valid run:

- recovered@100 > 66;
- recovered@50 >= 41;
- recovered@25 >= 23;
- top-100 dominant precision >= 0.7229521515453452;
- MRR >= 0.050244164168646674;
- qualified matches = 95.

A PASS authorizes only a separately frozen SonotaCo development benchmark under the post-v60 governance rule. It is not itself a SonotaCo result or external validation.

A FAIL permanently closes this exact directional second-moment morphology-discrepancy successor. In particular, do not rescue a failure using eigenvalue-only variants, principal-axis angles, determinants, anisotropy/eccentricity summaries, covariance/correlation alternatives, shrinkage/ridge, signed or squared Frobenius changes, alternate normalization, added radial/width terms, multiple tensor coordinates, thresholds, transforms, weights, feature subsets, metric/k/scaling changes, or fusion/diversity changes selected from the outcome.

## Firewall

Before any result is accepted, execution must verify:

- inclusive protected solar-longitude interval `[20.0°,55.0°]` remains excluded by the inherited frozen runtime;
- `sonotaco_2013_2014_access = false`;
- `target_information_access = false`;
- `target_region_events_accessed = false`;
- `maarsy_scientific_access = false`;
- `dms_scientific_access = false`;
- no post-result second search occurs.

Any provenance mismatch, changed immutable input, nonfinite physical residual, missing annual centroid/member set, changed parent control, or firewall violation is a technical invalidation, not a scientific result.