# OrbitTrace fixed-scale TopoModal — final flagship freeze

## Status

**FLAGSHIP_FROZEN — METHOD DEVELOPMENT COMPLETE**

The OrbitTrace flagship detector is the exact fixed-scale topological modal hierarchy established in PR #1284 and evaluated once under the separately frozen sparse-recovery protocol.

No further ranking, threshold, density, graph, persistence, recurrence, orbital, station-support, hierarchy-selection, or candidate-canonicalization variant is authorized from the existing GMN 2022/2023 development outcomes.

This freeze does not rewrite the historical verdict of any earlier protocol. It records the final flagship scientific claim that is directly supported by the immutable evidence.

## Exact flagship method

The detector uses a fixed physical metric rather than a sample-count-dependent HDBSCAN support scale.

For each target-excluded meteor, construct the six-dimensional embedding

`[cos(sol)/h_sol, sin(sol)/h_sol, cos(lat)cos(lon)/h_rad, cos(lat)sin(lon)/h_rad, sin(lat)/h_rad, log(vg)/h_logv]`

with

- `h_sol = 2 sin(5 deg / 2)`;
- `h_rad = 2 sin(4 deg / 2)`;
- `h_logv = ln(1.1)`;
- exact Euclidean radius graph `r = 1`;
- local density `rho_i = radius_degree_i / n`, including self;
- GUDHI ToMATo on the exact manual radius graph and density;
- complete modal merge hierarchy retained;
- minimum candidate support `4`;
- no selected cluster count and no persistence threshold.

The frozen reporting order is the exact sparse-recovery order from source blob

`752df8212ce601227f6e9170b0fe994ba06b515d`

and immutable prelabel SHA-256

`db608f84bf333d18d624199f2d31c27b4183ee3a75a3d930cef4b9766a19d4de`.

No part of that method or order is changed by this final freeze.

## 1. Sample-size generalization — strong positive result

Binding structural run: `31955621864`  
Artifact: `9265889512`  
Artifact digest: `sha256:2ddc5dbfc434b3887c284f639640d1b60276f5ceff1b9313e8604ddbb1beed6f`  
Result SHA-256: `e8cf7d92e96db9a1c99578f6efc63baf1534b94ab975e94f789fa6bc4a718497`

Across four deterministic target-excluded GMN nested pairs, approximately `5.8k -> 0.7k` events:

- pooled fine-to-coarse mean best Jaccard: **0.8067062037**;
- fixed-support HDBSCAN comparator: `0.6152941107`;
- median bucket: **0.8129624258** vs `0.6089001948`;
- strict bucket wins: **4/4**;
- nonempty output: **8/8** subsets;
- sparse candidate non-collapse: **4/4** buckets.

Fine candidate counts were `9/7/6/9`, compared with `8/5/6/9` for the fixed-support HDBSCAN comparator.

The absolute pooled Jaccard gain is `+0.1914120930` and the relative gain is about `+31%`.

## 2. Known-stream recovery at identical candidate budget — strong positive result

Binding recovery run: `31959926804`  
Artifact: `9266993487`  
Artifact digest: `sha256:0c2e38d633f30115ed5b64fdafe295e3b0f027ec16700a081856c780e87ecda5`  
Immutable prelabel: `db608f84bf333d18d624199f2d31c27b4183ee3a75a3d930cef4b9766a19d4de`

Every subset used the comparator's exact candidate count as the flagship reporting budget. The comparator candidate counts were:

- ~5.8k scale: `29 / 35 / 38 / 33`;
- ~0.7k scale: `8 / 5 / 6 / 9`.

### ~0.7k events

- qualified recovered showers: `20 ->` **31** (`+55%`);
- mean dominant precision across the complete matched-budget list: `0.3530315710 ->` **0.5886672679**;
- median fragmentation: `1.0 -> 1.0`;
- panelwise recovery: **8/8 nonlower, 6/8 strict wins, 0 losses**.

### ~5.8k events

- qualified recovered showers: `94 ->` **140** (`+48.9%`);
- mean dominant precision across the complete matched-budget list: `0.3396191654 ->` **0.5543714415**;
- median fragmentation: `1.0 -> 1.0`;
- panelwise recovery: **8/8 nonlower, 8/8 strict wins, 0 losses**.

The flagship therefore expands recoverable stream coverage substantially without increasing the frozen fragmentation statistic.

## 3. Direct relationship to ordinary HDBSCAN

This is not merely an improvement over a private custom comparator.

The independent zero-label fixed-scale stress experiment, binding run `31929171717`, proved that at denominator `128` all four sparse GMN buckets had **exactly identical ordinary-HDBSCAN-EOM and recurrent-EOM selected-node sets**, with selected-node symmetric difference `0` in `4/4` buckets. At denominator `1024`, the same exact identity held in `4/4` buckets.

Those are the same deterministic sparse scales and bucket definitions used by the flagship recovery experiment. The flagship recovery prelabel independently reproduced the comparator membership summaries before truth evaluation.

Therefore, for **set-level matched-budget quantities that consume the complete HDBSCAN candidate catalogue**, the comparator values in the flagship recovery experiment are also ordinary HDBSCAN EOM values on these panels.

Because the ordinary-HDBSCAN candidate counts are at most `38`, the complete matched-budget list is below 50 and below 100 in every panel. Consequently the following flagship gains transfer directly to ordinary HDBSCAN without assuming any HDBSCAN ranking convention:

- complete-catalogue qualified recovery: `20 -> 31` at ~0.7k and `94 -> 140` at ~5.8k;
- complete-catalogue dominant precision: `0.3530 -> 0.5887` and `0.3396 -> 0.5544`;
- fragmentation: `1.0 -> 1.0` at both scales.

This is the primary standard-HDBSCAN comparison for the flagship.

Rank-dependent statistics are deliberately **not** transferred from the recurrent ordering to ordinary HDBSCAN unless an ordering identity is separately proved. The flagship claim is therefore detection/recovery, purity, fragmentation, and sample-size generalization — not universal rank dominance.

## Final flagship claim

The strongest defensible claim is:

> On deterministic target-excluded GMN sparse-sample stress spanning roughly an eightfold sample-size change, the fixed-scale TopoModal detector preserves candidate identity substantially better than fixed-support HDBSCAN and, at identical candidate-reporting budget, recovers substantially more known meteor showers with higher candidate purity and no increase in median fragmentation.

For the exact tested sparse scales, the ordinary HDBSCAN EOM candidate catalogue is identical to the frozen comparator catalogue, so the set-level recovery and purity gains above are direct standard-HDBSCAN gains.

Do **not** rewrite this as universal superiority on every ranking metric, every survey, or every literature algorithm.

## What is finished

The flagship detector itself is finished.

Further work belongs to application/characterization rather than method invention:

- use the exact frozen method for figures and manuscript description;
- characterize computational scaling before any full-catalogue deployment;
- apply only under separately frozen, scientifically appropriate validation protocols;
- do not reopen GMN 2022/2023 as an optimization oracle.

## Firewall

Throughout the binding flagship evidence:

- protected solar longitude `[20.0,55.0]` remained excluded inclusively;
- OrbitTrace target information/events were not accessed;
- MAARSY and DMS were not accessed;
- no AMOS scientific rows were accessed;
- the structural result used no shower truth;
- the recovery order was frozen before the truth boundary;
- no result-informed flagship parameter change is authorized.
