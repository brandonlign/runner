# OrbitTrace annual-density bifiltration scale diagnostic v1

## Scientific role

This is a **zero-label, target-excluded GMN structural diagnostic only**. It tests a mechanism class that is distinct from the closed recurrent-density scalarization and closed TopoModal scalar-ranker/cut lanes: preserve the 2022 and 2023 local-density fields as two independent filtration coordinates rather than collapsing them to a single scalar before topology is constructed.

The motivation is standard multiparameter-persistence logic: density-sensitive clustering can be represented as a multiparameter filtration, avoiding information loss from an arbitrary one-parameter slice. Relevant methodological antecedents include Carlsson, Singh & Zomorodian (2009), *Computing Multidimensional Persistence*, and Rolle & Scoccola (2020/2024), *Stable and consistent density-based clustering via multiparameter persistence*.

This experiment uses **no shower truth**. It cannot promote a paper method. A PASS may authorize exactly one separately frozen GMN recovery/ranking endpoint using the canonical ranking already frozen below. A FAIL closes this exact bifiltration architecture without truth access.

## Why this is not a rescue of a closed method

Closed `recurrent-density topomodal v1` used one pointwise scalar:

`rho_rec(i) = min(rho_2022(i), rho_2023(i))`

and then built an ordinary one-parameter ToMATo hierarchy. Its binding result explicitly suggested that a future architecture keep the two annual fields distinct instead of scalarizing them.

The present architecture does that literally. It does **not** replace `min` with another mean/product/pseudocount/weight. It constructs the complete connected-component bifiltration of joint annual-density superlevel sets on the fixed physical graph.

Older Pareto diagnostics in the repository operate on already-computed HDBSCAN family feature vectors; they do not construct a two-parameter topological filtration and are not this mechanism.

## Frozen data and physical graph

Use only target-excluded GMN 2022 and 2023 through the exact frozen runtime used by the authoritative TopoModal hierarchy-scale diagnostic.

- years: `2022, 2023`
- protected solar-longitude exclusion: inclusive `[20°,55°]`, applied before all method operations
- pooled deterministic scale subsets: denominator `128` and `1024`, buckets `0,1,2,3`
- subset rule: `SHA256('ORBITTRACE_SCALE_STRESS_V1|' + event_id) mod denominator == bucket`
- physical embedding: exact #1284 embedding
- graph: exact Euclidean radius-1 graph in that embedding
- physical scales inherited unchanged: 5° solar halfwidth, 4° radiant, 10% speed
- minimum reportable support: `4`

Authoritative infrastructure pins:

- fixed-scale TopoModal hierarchy source commit: `dc638e1a272c7eb3d6b709f498a345c94950e15e`
- `orbittrace_topomodal_hierarchy_scale_v1/run_diagnostic.py` Git blob: `c1efa8da34dea140726a4c2fe4943eb29a304538`
- authoritative structural result run: `31955621864`
- authoritative structural result artifact: `9265889512`
- authoritative structural result SHA-256: `e8cf7d92e96db9a1c99578f6efc63baf1534b94ab975e94f789fa6bc4a718497`
- recurrent-EOM implementation blob: `30ac3fa3bc47910370df528fcf3ae8ecb6277b47`
- frozen GMN utility SHA-256: `dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990`
- frozen pooled-year-centroid support result SHA-256: `fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b`

## Exact two annual density coordinates

For each pooled subset, let `G=(V,E)` be the fixed physical radius graph including self in each radius neighborhood exactly as #1284 does.

Let `N_22` and `N_23` be the numbers of subset events from 2022 and 2023.

For every event `i` define:

`d_22(i) = number of radius-neighborhood vertices belonging to 2022`

`d_23(i) = number of radius-neighborhood vertices belonging to 2023`

and normalized coordinates

`rho_22(i) = d_22(i) / N_22`

`rho_23(i) = d_23(i) / N_23`.

No pseudocount, smoothing, clipping, power, weighting, averaging, minimum, maximum, product, or other scalarization is permitted.

## Exact bifiltration

For threshold pair `(a,b)`, define the joint superlevel induced subgraph

`G[a,b] = G[{i : rho_22(i) >= a AND rho_23(i) >= b}]`.

The threshold coordinates are **all distinct positive observed values** of each annual density coordinate. No binning or selected grid is permitted.

To give the filtration its exact continuous parameter measure, for each descending distinct positive coordinate value `u_j`, associate width

`Delta u_j = u_j - u_{j+1}`

with the final `u_{m+1}=0`. Endpoints have measure zero and therefore do not affect area.

For every pair of coordinate cells, enumerate every connected component of `G[a,b]`. A component is reportable iff its membership contains at least 4 events.

Identical event memberships appearing at multiple threshold pairs are one canonical candidate.

## Canonical bifiltration persistence area

For each unique reportable membership `C`, define

`A(C) = sum Delta a * Delta b`

over all threshold cells whose induced graph contains **exactly membership C as one connected component**.

This is the 2D parameter-space area over which the exact component persists. It is not a pointwise scalarization of annual densities and does not require a path/slice through the bifiltration.

Require `A(C) > 0` for every emitted candidate.

The canonical downstream total order is frozen now, before this zero-label structural result:

1. `A(C)` descending;
2. member count descending;
3. SHA-256 of sorted event IDs ascending.

The current diagnostic does not use shower truth or evaluate this ranking. If this structural diagnostic PASSes and a later GMN truth endpoint is authorized, that endpoint must use this exact order with no score transform, blend, quota, path selection, or reranking.

## Structural comparisons

For each denominator/bucket subset, also reproduce exact recurrent-EOM HDBSCAN v1 candidates using the frozen comparator implementation.

For each bucket, compare the nested fine (`d=1024`) candidate universe to the corresponding coarse (`d=128`) universe by the exact #1284 procedure:

- restrict every coarse membership to the fine event universe;
- discard restricted memberships below support 4;
- deduplicate exact memberships;
- for every fine candidate, take its best Jaccard match among restricted coarse candidates;
- use candidate-unweighted mean best Jaccard as the primary bucket score.

Also report median best Jaccard, exact-match fraction, candidate counts, annual-density zero fractions, persistence-area summaries, and an area-weighted best-Jaccard diagnostic. The area-weighted value is reporting-only and cannot affect the verdict.

## Frozen five-gate structural verdict

Use the same five structural questions as the authoritative #1284 scale diagnostic so the result is directly interpretable.

All five are mandatory:

1. bifiltration output is nonempty in all eight subsets;
2. fine bifiltration candidate count is at least recurrent-EOM candidate count in all four buckets;
3. pooled fine→coarse candidate-unweighted mean best Jaccard is strictly greater than recurrent-EOM;
4. median bucket fine→coarse candidate-unweighted mean best Jaccard is strictly greater than recurrent-EOM;
5. bifiltration strictly beats recurrent-EOM in at least `3/4` bucket scores.

Exact positive interpretation:

`SUPPORTS_ANNUAL_DENSITY_BIFILTRATION_CROSS_SCALE_COHERENCE`

Otherwise:

`REFUTES_ANNUAL_DENSITY_BIFILTRATION_CROSS_SCALE_COHERENCE`

No gate depends on shower labels or OrbitTrace target information.

## No-rescue rule

If the exact architecture fails, do not rescue it by:

- changing the physical graph or scales;
- using a subset of thresholds or quantile grid;
- adding zero-density boundary components;
- changing support 4;
- replacing exact-component persistence area by support×area, log area, square-root area, Pareto layer, rank product, or another score;
- selecting a one-parameter slice or path after the result;
- changing annual density normalization;
- adding pseudocounts or smoothing;
- adding station/orbit/annual-confirmation evidence;
- changing the thinning denominators, buckets, or salt;
- relaxing any structural gate.

A PASS authorizes at most one separately frozen GMN truth endpoint with the already-frozen persistence-area ranking. It does not authorize SonotaCo or pristine external access.

## Firewall

Forbidden throughout this diagnostic:

- OrbitTrace target information or target-region events;
- protected solar longitude `[20°,55°]`;
- shower truth;
- SonotaCo 2013/2014 event rows or truth;
- ASFN/EFN event-level data;
- AMOS;
- MAARSY;
- DMS;
- any pristine external endpoint;
- post-result parameter search.
