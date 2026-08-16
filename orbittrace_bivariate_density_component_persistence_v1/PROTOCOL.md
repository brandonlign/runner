# OrbitTrace bivariate annual-density component persistence v1

## Status

**FROZEN BEFORE IMPLEMENTATION AND BEFORE ANY SHOWER-TRUTH OUTCOME FOR THIS SUCCESSOR.**

This successor follows the binding failure of recurrent-density topomodal v1. The previous method retained the fixed physical radius graph but collapsed the two annual normalized local densities to the pointwise minimum before building a one-parameter hierarchy. It preserved strong sparse recovery/purity but failed both MRR gates and made roughly 67–82% of sparse-panel vertices zero-density.

This successor does **not** try another scalar annual combiner. It keeps the two annual local-density coordinates distinct and defines candidate topology from the full two-parameter superlevel filtration on the already-established fixed physical graph.

The first technically valid outcome is binding. No result-informed threshold grid, scalarization, smoothing, pseudocount, radius, density transform, support floor, persistence score, tie-break, truth metric, or gate change is permitted.

## 1. Scientific hypothesis

A recurring meteor stream should occupy a connected local structure that survives simultaneous tightening of **both** annual density requirements. Collapsing `(rho_22,rho_23)` to a scalar such as `min(rho_22,rho_23)` discards the partial-order structure of the two annual fields before topology is constructed.

For each event i on the fixed physical graph define the annual normalized local densities exactly as in the closed recurrent-density predecessor:

`rho_22(i) = d_22(i) / N_22`

`rho_23(i) = d_23(i) / N_23`.

Instead of scalarizing them, define for every threshold pair `(a,b)` the active vertex set

`V(a,b) = {i : rho_22(i) >= a AND rho_23(i) >= b}`

and use the connected components of the induced fixed-radius graph on `V(a,b)`.

The complete collection of these components over all exact data-determined threshold cells is the candidate topology.

This is a genuine two-parameter density filtration. The motivation is consistent with density-cluster-tree methods, where clusters are connected components of density superlevel sets, and with multiparameter density clustering, where retaining the multiparameter object can preserve stability information that one-parameter slices discard. This protocol itself is fully specified by the finite empirical graph and does not depend on any external implementation or parameter selector.

## 2. Firewall

Use only target-excluded GMN 2022+2023 development data.

Inclusive solar longitude `[20.0,55.0]` is removed before graph construction, annual counts, filtration, candidate generation, ranking, or truth evaluation.

Forbidden:

- OrbitTrace target information or target-region events;
- SonotaCo event/truth access in the GMN experiment;
- ASFN or EFN event-level access;
- AMOS scientific access;
- MAARSY or DMS scientific access;
- orbital elements in candidate construction;
- any known-shower label, comparator outcome, or truth metric in candidate generation/ranking.

## 3. Exact sparse development panels

Reuse exactly `ORBITTRACE_SCALE_STRESS_V1`:

`H(eid) = uint64_be(SHA256('ORBITTRACE_SCALE_STRESS_V1|' + eid)[0:8])`.

Exactly eight pooled GMN 2022+2023 subsets:

- denominator `128`, buckets `0,1,2,3`;
- denominator `1024`, buckets `0,1,2,3`.

No additional denominator, bucket, salt, bootstrap, or replicate is authorized.

## 4. Physical graph — unchanged from #1284

Order events deterministically by event ID.

Use the exact #1284 physical embedding:

- `h_sol = 2 sin(5 deg / 2)`;
- `h_rad = 2 sin(4 deg / 2)`;
- `h_logv = ln(1.1)`;

`Z = [cos(sol)/h_sol, sin(sol)/h_sol, cos(lat)cos(lon)/h_rad, cos(lat)sin(lon)/h_rad, sin(lat)/h_rad, log(vg)/h_logv]`.

Construct the exact symmetric Euclidean radius graph at

`r = 1.0`.

Self is included in each radius-neighbor list exactly as in #1284.

No kNN, adaptive radius, local scaling, mutual reachability, MST replacement, or bandwidth search is permitted.

## 5. Two annual density coordinates

For one sparse panel let:

- `N_22` = accessible 2022 event count;
- `N_23` = accessible 2023 event count;
- `d_22(i)` = number of radius neighbors of i from 2022;
- `d_23(i)` = number of radius neighbors of i from 2023.

Define only

`rho_22(i)=d_22(i)/N_22`

`rho_23(i)=d_23(i)/N_23`.

The pair `(rho_22,rho_23)` is never collapsed to min/max/mean/product/geometric mean/harmonic mean/norm/rank/ECDF or any learned scalar before topology.

Zero annual density is allowed. No vertex is deleted because either coordinate is zero.

Pretruth checks must verify:

- integer count identities exactly;
- finite nonnegative densities;
- deterministic density-vector hashes;
- exact year-swap equivariance: swapping year labels swaps the two coordinate vectors and leaves the two-parameter component family/ranking invariant after transposing threshold axes.

## 6. Exact finite bifiltration

Because `rho_y=d_y/N_y` and `d_y` is integer, topology changes only when an integer annual neighbor-count threshold changes.

Define the exact threshold lattice

`K_22 = {0,1,...,max_i d_22(i)}`

`K_23 = {0,1,...,max_i d_23(i)}`.

For every `(k22,k23)` in the complete Cartesian product `K_22 x K_23`, define

`A(k22,k23) = { i : d_22(i) >= k22 AND d_23(i) >= k23 }`.

Let `G(k22,k23)` be the induced subgraph of the fixed radius graph on `A(k22,k23)`.

The filtration objects are **all connected components** of every `G(k22,k23)`.

There is:

- no selected threshold pair;
- no diagonal/min-density slice;
- no Pareto-frontier threshold subset;
- no adaptive grid;
- no quantile grid;
- no persistence threshold;
- no component-count selector;
- no one-parameter flattening.

Every integer threshold pair is included exactly once.

## 7. Candidate identity and exact two-parameter support area

For each exact component membership C appearing anywhere in the threshold lattice:

- canonical membership = sorted event IDs;
- support cells `S(C)` = number of threshold pairs `(k22,k23)` for which C is **exactly** one connected component of `G(k22,k23)`.

Only after the entire threshold lattice has been enumerated, retain/report candidates with at least **4 member events**. The support-4 floor is the same reporting/truth floor used throughout the sparse-recovery experiments; it is not a graph-density or core-neighbor requirement.

Define exact empirical bivariate persistence area

`A(C) = S(C) / (N_22 * N_23)`.

Each threshold-count cell corresponds to density-coordinate area `1/(N_22*N_23)`, so this is the exact area of the discrete annual-density threshold cells over which the membership persists as a connected component.

The axes at count threshold zero are included. Thus a component supported only when one annual threshold is zero occupies only the corresponding narrow boundary strip rather than being deleted outright. This is intentional and frozen.

No alternative area weighting, logarithm, square root, normalization by panel maxima, Jaccard factor, component-size factor, recurrence bonus, or background subtraction is permitted.

## 8. Ranking

Rank all support-4 unique component memberships exactly by:

1. `A(C)` descending;
2. deterministic family hash ascending.

No other tie-break or score is used.

Candidate prefix: `BDCP1`.

This ranking is not a post-hoc scalarization of pointwise annual densities. It is the measure of the region in the **full two-parameter filtration** over which an exact connected component exists.

## 9. Exactness / implementation freedom

The scientific object is the complete lattice definition above, not a particular algorithm.

An implementation may use repeated graph connected-components, threshold sweeps, disjoint-set union, rollback, caching, or another exact acceleration only if it produces exactly the same:

- active-set semantics at every threshold pair;
- connected-component memberships;
- support-cell counts for every membership;
- final support-4 candidate set and order.

No threshold pair may be skipped as an approximation.

For development-scale audit, the implementation must independently verify at least the smallest sparse panel by a second exact enumeration implementation before the prelabel is sealed. This cross-check is engineering integrity only and uses no labels.

## 10. Why this is not a closed lane

This successor is distinct from prior closed work:

- recurrent-density topomodal v1 collapsed annual densities to `min(rho_22,rho_23)` before a one-parameter ToMATo hierarchy; this method never scalarizes the annual pair and has no ToMATo hierarchy;
- density-synchronous recurrent-EOM changed HDBSCAN FOSC quality on a fixed 10/10 condensed tree; this method has no HDBSCAN candidate tree;
- cross-year-core HDBSCAN used opposite-year 10th-neighbor core distances and support-10 condensation; this method has no k-neighbor core requirement or condensation;
- local-kNN year mixing was a post-hoc rank feature over fixed recurrent-EOM candidates; this method changes candidate topology upstream;
- the old v31 joint-component Pareto-frontier diagnostic used two already-frozen family percentiles **after** candidate construction and defined a record/Pareto subset; this method applies no Pareto family ranking and instead enumerates all graph components over annual-density thresholds;
- the old joint-density/trajectory conformal work expanded membership of fixed v8 families using source-seed conformity; it did not construct an annual-density component filtration;
- generic multiscale subset scans and Persistable 2–15 flattening varied scale/density selectors or one-parameter flattenings; this method fixes physical radius at 1.0 and its two filtration axes are the two observing-year normalized local densities, with no selected slice or flattening parameter.

## 11. Mandatory immutable prelabel boundary

Before any shower truth is loaded, serialize for all eight panels:

- event-universe hash and annual totals;
- exact graph configuration, edge count, degree summaries;
- `d_22`, `d_23`, `rho_22`, `rho_23` hashes;
- threshold lattice dimensions and exact number of enumerated cells;
- all unique component memberships before support filtering with support-cell counts, or an immutable hash plus auditable support-4 rows if artifact size requires compact storage;
- every support-4 candidate membership, `S(C)`, `A(C)`, family hash, and final rank;
- selected recurrent-EOM comparator membership and rank;
- source/artifact hashes and all firewall flags;
- independent exact-enumeration cross-check result for the smallest sparse panel.

Write `BIVARIATE_DENSITY_COMPONENT_PERSISTENCE_V1_PRELABEL.json`, compute SHA-256, and verify it in a separate workflow step. Only after this seal may known-shower labels be evaluated.

A technical failure before the prelabel SHA exists is an engineering no-result. Repair may not change the filtration, area, candidate floor, or ranking.

## 12. Comparator and truth semantics

Comparator is exact selected recurrent-EOM HDBSCAN v1 on each identical sparse panel:

- GEO6;
- min cluster size 10;
- min samples 10;
- Euclidean;
- annual-normalized recurrent EOM;
- normal recurrent FOSC/EOM extraction and selected-parent ranking.

Comparator candidate summaries must reproduce the authoritative #1284 sparse structural artifact before truth.

Truth semantics are unchanged, separately for 2022 and 2023 inside each pooled panel:

- annual shower eligibility >=4 events;
- qualified candidate/shower match requires dominant-shower precision >=0.5 and overlap >=4;
- qualified matches;
- recovered@25/@50/@100/@500;
- top-100 dominant precision;
- MRR;
- median top-500 fragmentation.

For each sparse subset let `K` equal the number of recurrent-EOM comparator candidates. The successor must have at least K reportable candidates before truth; otherwise this architecture returns a binding pretruth scientific failure `FAIL_BDCP1_CANDIDATE_SHORTAGE` for that panel and cannot pass promotion.

If candidate supply is sufficient, evaluate all K comparator candidates and exactly the first K frozen BDCP1 candidates.

## 13. Frozen ten promotion gates

Use exactly the same ten gates as the prior sparse truth experiments.

### Fine sparse scale d=1024

1. successor qualified total strictly greater than recurrent-EOM;
2. qualified matches nonlower in at least 6/8 annual panels;
3. mean MRR not lower;
4. mean top-100 dominant precision not lower;
5. mean fragmentation not higher.

### Coarse scale d=128

6. successor qualified total not lower;
7. qualified matches nonlower in at least 6/8 annual panels;
8. mean MRR not lower;
9. mean top-100 dominant precision not lower;
10. mean fragmentation not higher.

All ten plus candidate-budget sufficiency are required for

`PASS_BIVARIATE_DENSITY_COMPONENT_PERSISTENCE_V1`.

Any failed gate returns `FAIL_BIVARIATE_DENSITY_COMPONENT_PERSISTENCE_V1` and permanently closes this exact filtration/area ranking. Do not rescue with selected slices, Pareto layers, alternate area weights, alternate annual density transforms, or post-result rank fusion.

## 14. Conditional exposed SonotaCo transfer

Before the GMN result is opened, freeze a conditional SonotaCo 2013/2014 direct-transfer benchmark using the exact historical four-panel matched evaluator, exact budgets, and selected recurrent-EOM controls.

Only a GMN PASS authorizes execution. SonotaCo remains **EXPOSED DEVELOPMENT ONLY**.

## 15. Interpretation

A PASS would be the first evidence that preserving the full annual-density partial order can combine:

- fixed-radius/sample-size-resilient geometry;
- recurrent two-year structure without fixed-k support;
- superior sparse known-stream recovery/purity;
- noninferior early ranking/MRR relative to recurrent-EOM.

A FAIL closes the architecture exactly.