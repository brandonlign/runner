# OrbitTrace Valsecchi direct-node encounter GEO density-sync v1 — frozen protocol

## Scientific goal
Test one physically motivated, survey-portable representation change aimed directly at the project goal: replace the current hand-scaled GEO6 coordinates with a Euclidean embedding of the **direct-node branch of the Valsecchi–Jopek–Froeschlé geocentric encounter geometry**, while keeping HDBSCAN and the density-synchronous recurrent-EOM selector unchanged.

The goal is not a small rerank improvement. A GMN development pass requires at least **+5 recovered showers at @100** over the frozen 179 winner, with no annual regression in the existing precision/early-rank/fragmentation gates. Only a clean GMN pass can earn a separately frozen SonotaCo transfer test.

## Independent motivation fixed before outcome
Valsecchi, Jopek & Froeschlé (1999) defined a meteoroid similarity description from four geocentric encounter quantities directly tied to observations: normalized geocentric speed `U`, encounter-direction quantities `cos(theta)` and `phi`, and encounter season/longitude. They showed `U` and `cos(theta)` are near-invariant under the principal secular perturbation considered in their theory. Galligan (2001) found the Valsecchi `D_N` criterion comparatively stable in radar-stream recovery, including regimes where orbital-element criteria are sensitive to uncertainty. Moorhead (2015) gives the observable-coordinate form of `D_N` and uses unit weights.

This experiment does **not** claim to implement full `D_N`. Full `D_N` takes the minimum of a direct-node angular branch and a simultaneous opposite-node branch in order to allow two Earth-crossing nodes of essentially the same orbit to associate. OrbitTrace's benchmark treats observed meteor showers at different seasons/nodes as distinct detection targets, so v1 freezes the **direct-node branch only**. This avoids deliberately aliasing distinct seasonal showers while retaining the published encounter variables and their direct-branch distance.

A pre-run repository search found no prior OrbitTrace `D_N`, Valsecchi encounter-coordinate, `U/cos(theta)/phi`, or equivalent direct-node encounter-geometry detector experiment.

## Binding baseline
Compare only against the frozen density-synchronous recurrent-EOM GMN winner:
- run `31852836840`;
- artifact `9238142199`;
- 2022 recovered@100 = 89;
- 2023 recovered@100 = 90;
- total recovered@100 = **179**;
- exact ordered-membership SHA256 `e8f374ad03e7072463118ee6440a54d96d11e3aab17202cfe336f866530224f2`.

The baseline is read from the frozen artifact and is never recomputed for comparison.

## Data and firewall
- GMN 2022+2023 development only.
- Protected solar longitude 20°–55° is excluded before representation construction or clustering.
- OrbitTrace target information and target-region events remain inaccessible.
- Known-shower labels cannot be indexed until the complete encounter-coordinate hierarchy, selected nodes, memberships and order are durably written.
- SonotaCo 2013/2014, ASFN, EFN, AMOS, MAARSY and DMS are not accessed in this endpoint.

The frozen target-excluded GMN interface contains exactly the required observables: solar longitude `sol`, Sun-centred geocentric ecliptic radiant longitude `sun_lon`, ecliptic latitude `ecl_lat`, and geocentric speed `vg` (plus identity/metadata fields). No orbital elements, uncertainty proxies, labels, or external-survey information enter v1.

## Sole scientific transformation
For each accessible event let:
- `L` = Sun-centred geocentric ecliptic radiant longitude in radians;
- `B` = geocentric ecliptic radiant latitude in radians;
- `lambda` = solar longitude in radians;
- `Vg` = geocentric speed in km/s.

Freeze the mean Earth orbital speed used by the published observable form of `D_N`:

`V_EARTH = 29.7 km/s`.

Define normalized encounter speed:

`U = Vg / 29.7`.

Using the Earth-centred ecliptic encounter frame (axis orientation signs do not affect pairwise distances), construct the unit geocentric velocity direction opposite the radiant:

`ux = cos(B) * cos(L)`

`uy = cos(B) * sin(L)`

`uz = -sin(B)`

and define:

`cos_theta = uy`

`phi = atan2(ux, uz)`.

The frozen six-dimensional Euclidean embedding is:

`VE6 = [U, cos_theta, cos(phi), sin(phi), cos(lambda), sin(lambda)]`.

For two events, ordinary squared Euclidean distance in `VE6` is exactly:

`(dU)^2 + (d cos_theta)^2 + 4 sin^2(dphi/2) + 4 sin^2(dlambda/2)`,

which is the direct-node angular branch of the unit-weight Valsecchi encounter distance. A deterministic pretruth numerical audit must verify equality of the embedding distance and this explicit formula to absolute error < `1e-12` on a fixed set of event pairs.

No Z-scoring, covariance whitening, learned scaling, seasonal-background factor, orbital element, uncertainty field, fitted parameter, axis weight, or post-hoc score enters the representation. `29.7 km/s` is fixed from the physical definition, not tuned on GMN.

## Detector architecture held fixed
Fit exact `hdbscan==0.8.43` with:
- `min_cluster_size=10`;
- `min_samples=10`;
- `metric='euclidean'`;
- `cluster_selection_method='eom'`;
- `cluster_selection_epsilon=0.0`;
- `allow_single_cluster=False`;
- `prediction_data=False`.

Then apply the exact existing density-synchronous recurrent-EOM objective and node-selection/ranking code unchanged. The sole scientific change is `GEO6 -> VE6` before HDBSCAN.

## Pretruth freeze
Before any known-shower label is indexed, persist:
- exact input/source hashes and accessible event counts;
- `V_EARTH=29.7`;
- encounter representation definition/version;
- direct-branch Euclidean-equivalence audit maximum error;
- condensed-tree SHA256;
- selected density-synchronous nodes;
- full ordered candidate memberships;
- candidate count, largest-family size and ordered-membership SHA256;
- firewall state.

## Binding GMN success gate
PASS requires all of:
1. total recovered@100 >= **184** (+5 over 179);
2. 2022 recovered@50 not below the winner and recovered@100 >= 89;
3. 2023 recovered@50 not below the winner and recovered@100 >= 90;
4. top-100 dominant precision not lower in either year;
5. MRR not lower in either year;
6. median top-500 fragmentation not higher in either year;
7. at least 100 candidate families and largest selected family <=1% of accessible events;
8. ordered memberships differ from the frozen winner;
9. all reproducibility and firewall checks pass.

Anything else is FAIL.

## Goal / transfer rule
A GMN PASS is only the first goal-level step. The exact representation and detector must then be frozen before one exposed SonotaCo 2013/2014 transfer benchmark against the existing literature comparators. Broad generalization still requires a genuinely untouched external survey afterward; SonotaCo is exposed development evidence only.

## No rescue
If v1 fails, permanently close this exact direct-node Valsecchi encounter embedding. Do not retry after seeing the result with:
- a different Earth speed constant;
- full opposite-node aliasing;
- alternate `phi` weights;
- speed/angle weights;
- Z-score or covariance scaling;
- per-year or per-season scaling;
- feature dropping/addition;
- HDBSCAN parameter changes;
- reranking or score blending;
- route/year-specific exceptions;
- target-guided tuning.

Any successor after failure must have a distinct independently motivated mechanism.