# OrbitTrace joint GEO6 + ORBIT7 density-synchronous recurrent-EOM v1 — frozen protocol

## Scientific goal
Test one genuinely multiview physical detector: form density structure jointly in the established geocentric radiant/speed representation and an independent orbital-element representation, instead of replacing one view with the other or post-hoc reranking candidates.

The motivation is fixed by two completed target-excluded GMN results:
- the promoted GEO6 density-synchronous recurrent-EOM detector retains stronger top-100 recovery (179 total);
- the separately frozen ORBIT7-only detector failed at 173 total but produced higher MRR in both years, showing that orbit space contains complementary early-order structure rather than being a viable replacement for GEO6.

JOINT13 therefore asks whether requiring one HDBSCAN hierarchy to be locally coherent in **both** physical descriptions can retain GEO6 recovery while using orbital information to suppress ambiguous background structure.

This is not a reranker, candidate union/intersection, member veto, fitted metric, learned embedding, density rescaling, or parameter search. A repository search before freezing found no prior OrbitTrace detector using raw joint GEO6+orbit-vector HDBSCAN.

## Binding baseline
Compare only against the frozen density-synchronous recurrent-EOM GMN winner:
- run `31852836840`;
- artifact `9238142199`;
- 2022 recovered@100 = 89;
- 2023 recovered@100 = 90;
- total recovered@100 = 179;
- ordered-membership SHA256 `e8f374ad03e7072463118ee6440a54d96d11e3aab17202cfe336f866530224f2`.

The baseline is read from its frozen artifact and is never recomputed.

## Data and firewall
- Development data: GMN 2022+2023 only.
- For each raw monthly frame, only stable trajectory ID and solar longitude may be inspected for all rows.
- Closed solar-longitude interval 20°–55° is excluded **before any orbital element is indexed**.
- Only already-safe rows may expose `q/e/i/peri/node`.
- OrbitTrace target information and protected-region orbital values are forbidden.
- Known-shower labels remain sealed until the complete JOINT13 hierarchy, selected nodes, memberships, order, and hashes are persisted.
- SonotaCo 2013/2014, ASFN, EFN, AMOS, MAARSY, and DMS are not accessed in this GMN endpoint.

The already completed sol-first coverage audit established that all 738,682 accessible GMN events have complete, physically valid native `q/e/i/peri/node`; JOINT13 nevertheless independently verifies eligibility and does not consume event values from the audit artifact.

## View 1: exact inherited GEO6
For every accessible event use the exact promoted geocentric representation:

`GEO6 = [cos(sol), sin(sol), sin(sun_lon)*cos(ecl_lat), cos(sun_lon)*cos(ecl_lat), sin(ecl_lat), vg/72]`.

No centering, Z-score, whitening, density factor, year weighting, or fitted transform is allowed.

## View 2: exact frozen ORBIT7
GMN raw orbital fields:
- primary `q_au`; fallback `q_au_` only if primary is missing/nonfinite;
- `e`;
- `i_deg`;
- `peri_deg`;
- `node_deg`.

If both q fields are finite, `q_au` is authoritative. Eligibility requires finite values, `q>0`, `e>=0`, `0<=i<=180°`; angles are modulo 360°.

With inclination `i`, node `Ω`, and argument of perihelion `ω` in radians:

`h = [sin(i) sin(Ω), -sin(i) cos(Ω), cos(i)]`

`p = [cos(Ω)cos(ω)-sin(Ω)sin(ω)cos(i),
      sin(Ω)cos(ω)+cos(Ω)sin(ω)cos(i),
      sin(ω)sin(i)]`

`evec = e*p`

`ORBIT7 = [q, h_x, h_y, h_z, evec_x, evec_y, evec_z]`.

No orbit-axis scaling, D-criterion threshold, standardization, quality cut, uncertainty weighting, or fitted transform is allowed.

## Sole scientific change: JOINT13
For each accessible event define exactly

`JOINT13 = concat(GEO6, ORBIT7)`.

Use ordinary Euclidean distance in this raw 13-dimensional physical embedding.

There is **no relative view weight**. This is deliberate and frozen: both component representations already use bounded/natural dimensionless coordinates (unit-circle/unit-vector components, `vg/72`, perihelion distance in units of 1 AU, and eccentricity-vector components). No coefficient may be inserted before or after outcome.

## Detector architecture held fixed
Run exact `hdbscan==0.8.43` on JOINT13 with:
- `min_cluster_size=10`;
- `min_samples=10`;
- Euclidean metric;
- EOM cluster selection;
- `cluster_selection_epsilon=0`;
- `allow_single_cluster=False`;
- `prediction_data=False`.

Then apply the exact existing density-synchronous recurrent-EOM stability calculation, EOM node selection, candidate extraction, and ranking.

Candidate order is exactly:
1. descending density-synchronous stability;
2. descending ordinary HDBSCAN stability;
3. descending member count;
4. ascending stable SHA256 family ID.

The sole scientific change from the binding architecture is `GEO6 -> JOINT13` before HDBSCAN.

## Pretruth freeze
Before any known-shower label is indexed, persist:
- exact source/input hashes and event counts;
- raw rows excluded before orbital access;
- joint-eligible counts by year;
- exact representation identifier;
- condensed-tree SHA256;
- selected density-synchronous nodes;
- full ordered candidate memberships and ordered-membership SHA256;
- candidate count and largest-family size;
- firewall state.

No event-level physical coordinates are serialized in the public artifact.

## Binding GMN success gate
PASS requires all:
1. total recovered@100 >= **184** (+5 over 179);
2. 2022 recovered@50 not lower and recovered@100 >=89;
3. 2023 recovered@50 not lower and recovered@100 >=90;
4. top-100 dominant precision not lower in either year;
5. MRR not lower in either year;
6. median top-500 fragmentation not higher in either year;
7. at least 100 candidate families and largest selected family <=1% of all 738,682 accessible events;
8. ordered memberships differ from the frozen winner;
9. every source, reproducibility, pretruth, and firewall gate passes.

Anything else is FAIL. No post-result view weighting, orbit scaling, feature deletion/addition, HDBSCAN tuning, reranking, candidate union, or rescue is authorized for v1.

## Transfer rule
A GMN PASS earns exactly one separately frozen exposed-SonotaCo 2013/2014 transfer benchmark. SonotaCo must build the same GEO6-equivalent geocentric view from its native radiant/speed/solar-longitude fields and the same ORBIT7 from native `q/e/inc/peri/node`; no GMN-fitted number exists to transfer.

Broad superiority still requires a genuinely untouched external survey after development.