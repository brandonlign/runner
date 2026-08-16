# OrbitTrace orbit-vector density-synchronous recurrent-EOM v1 — frozen protocol

## Scientific goal
Test a genuinely different, cross-survey physical detector view rather than another normalization of the existing geocentric representation.

GMN raw trajectory files expose `q`, `e`, `i`, argument of perihelion, and ascending node before the legacy OrbitTrace parser projects rows down to geocentric fields. The already-frozen SonotaCo interface carries the same five native orbital elements (`q`, `e`, `inc`, `peri`, `node`). This permits the same detector representation to be recomputed independently on both surveys.

This experiment is frozen before any orbital-field coverage result or known-shower truth from the new representation is inspected.

## Binding baseline
Compare only with the frozen density-synchronous recurrent-EOM GMN winner:
- run `31852836840`
- artifact `9238142199`
- 2022 recovered@100 = 89
- 2023 recovered@100 = 90
- total recovered@100 = 179
- ordered-membership SHA256 `e8f374ad03e7072463118ee6440a54d96d11e3aab17202cfe336f866530224f2`

The baseline is read from its frozen artifact and is never recomputed.

## Firewall and data role
- Development data: GMN 2022+2023 only.
- In every raw monthly frame, code may inspect only stable trajectory ID and solar longitude for all rows.
- The closed solar-longitude interval 20°–55° is removed **before any orbital element is indexed**.
- Only rows already outside that interval may expose `q/e/i/peri/node` to this detector.
- OrbitTrace target information and protected-region orbital values are forbidden.
- Known-shower labels stay sealed until the full orbit representation, hierarchy, selected nodes, memberships, order, and hashes are persisted.
- SonotaCo 2013/2014, ASFN, EFN, AMOS, MAARSY, and DMS are not accessed in this GMN endpoint.

## Raw orbital field contract
GMN source fields:
- primary perihelion distance: `q_au`;
- fallback perihelion distance: `q_au_` only when `q_au` is missing/nonfinite;
- eccentricity: `e`;
- inclination: `i_deg`;
- argument of perihelion: `peri_deg`;
- ascending node: `node_deg`.

If both `q_au` and `q_au_` are finite, `q_au` is authoritative. The fallback rule is fixed now and may not be changed after coverage or performance is seen.

An accessible event is orbit-eligible iff all five selected orbital elements are finite, `q>0`, `e>=0`, and `0<=i<=180°`. No upper eccentricity cut, quality-score cut, uncertainty cut, label-dependent cut, or survey-specific cut is used. Angles are reduced modulo 360°.

Events without a valid orbit remain in the known-shower evaluation denominator but cannot enter orbit-space candidates; this prevents changing the benchmark universe in the new detector's favor.

## Frozen ORBIT7 vector representation
Let `i` be inclination, `Ω` ascending node, and `ω` argument of perihelion in radians.

Represent the unit orbital-plane normal as

`h = [sin(i) sin(Ω), -sin(i) cos(Ω), cos(i)]`.

Represent the unit perihelion/eccentricity direction as

`p = [cos(Ω)cos(ω)-sin(Ω)sin(ω)cos(i),
      sin(Ω)cos(ω)+cos(Ω)sin(ω)cos(i),
      sin(ω)sin(i)]`.

Let `evec = e * p`.

The detector vector is exactly

`ORBIT7 = [q, h_x, h_y, h_z, evec_x, evec_y, evec_z]`.

No centering, standardization, whitening, learned metric, axis weighting, year weighting, density transform, uncertainty scaling, or parameter sweep is allowed. `q` is already expressed in AU, so its numerical coordinate is the dimensionless perihelion distance in units of 1 AU; `h` is unitless; `evec` has norm `e`.

This vector is a physical two-vector orbital description: the plane-normal chord encodes orbital-plane separation, while the eccentricity vector jointly encodes eccentricity magnitude and apsidal direction. It is intentionally independent of the existing geocentric radiant/speed geometry.

## Detector architecture held fixed
Run exact `hdbscan==0.8.43` on ORBIT7 with:
- `min_cluster_size=10`
- `min_samples=10`
- Euclidean metric
- EOM cluster selection
- `cluster_selection_epsilon=0`
- `allow_single_cluster=False`
- `prediction_data=False`

Then apply the exact existing **density-synchronous recurrent-EOM** stability calculation, EOM node selection, candidate extraction, and ranking. The sole scientific change relative to the binding architecture is the event representation and the resulting orbit-eligible event subset.

Candidate order is exactly:
1. larger density-synchronous stability;
2. larger ordinary HDBSCAN stability;
3. larger member count;
4. stable SHA256 family ID.

## Pretruth freeze
Before any known-shower label is indexed, persist:
- exact source/evidence hashes;
- raw rows and rows excluded before orbital access;
- accessible and orbit-eligible event counts by year;
- missing/invalid-orbit counts only as aggregate statistics;
- exact ORBIT7 definition identifier;
- HDBSCAN condensed-tree SHA256;
- density-synchronous selected nodes;
- full ordered candidate memberships and membership SHA256;
- candidate count and largest-family size;
- firewall state.

No event-level orbital values are persisted in the public artifact beyond the detector's candidate event IDs; the transform itself has no fitted parameters.

## Binding GMN success gate
PASS requires all:
1. total recovered@100 >= **184** (+5 over 179);
2. 2022 recovered@50 not lower and recovered@100 >= 89;
3. 2023 recovered@50 not lower and recovered@100 >= 90;
4. top-100 dominant precision not lower in either year;
5. MRR not lower in either year;
6. median top-500 fragmentation not higher in either year;
7. at least 100 candidate families and largest selected family <=1% of all 738,682 accessible events;
8. ordered memberships differ from the frozen winner;
9. all source, reproducibility, pretruth, and firewall checks pass.

Anything else is FAIL. No post-result orbit-axis scaling, q/e cut, quality cut, D-threshold, HDBSCAN tuning, reranking, union with GEO candidates, or rescue is authorized for v1.

## Transfer rule
A GMN PASS earns exactly one separately frozen exposed-SonotaCo 2013/2014 transfer benchmark. SonotaCo must construct the same ORBIT7 directly from its native `q/e/inc/peri/node`; no GMN-fitted numbers exist to transfer. Broad superiority still requires a genuinely untouched external survey after development.