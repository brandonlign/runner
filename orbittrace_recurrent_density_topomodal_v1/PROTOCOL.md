# OrbitTrace recurrent-density topomodal v1

## Status

**FROZEN BEFORE IMPLEMENTATION AND BEFORE ANY SHOWER-TRUTH OUTCOME FOR THIS SUCCESSOR.**

This successor begins from the fixed-radius ToMATo/#1284 architecture after multiple frozen experiments established a reproducible pattern: its candidate hierarchy has substantially better known-stream coverage and purity than recurrent-EOM under severe deterministic thinning, but several post-hoc scalar rankings and hierarchy schedules still fail the preregistered MRR gates.

The next scientific change therefore occurs **before the hierarchy exists**. The physical radius graph remains fixed and sample-size independent, while the scalar field used by ToMATo is changed from pooled local density to a two-year recurrent local density.

The first technically valid truth outcome is binding. No result-informed radius, annual combiner, pseudocount, smoothing, threshold, density transform, rank fusion, candidate filter, support floor, tie-break, truth metric, or gate change is permitted.

## 1. Scientific hypothesis

A recurring meteor stream should create a local density enhancement at the same physical phase-space location in both observing years. The original #1284 density

`rho_pool(i) = |N(i)| / N`

can be high when a radius neighborhood is populated mainly by one year. The selected recurrent-EOM HDBSCAN parent solves a related problem downstream by requiring annual EOM persistence, but it retains the sample-size-dependent HDBSCAN 10/10 support mechanism.

V1 instead defines a **recurrent density field on #1284's already-successful fixed physical radius graph**:

`rho_rec(i) = min( |N(i) ∩ Y_2022| / N_2022, |N(i) ∩ Y_2023| / N_2023 )`.

ToMATo then discovers modes and the complete merge hierarchy of `rho_rec` directly.

The annual `1/N_y` normalization is inherited from the selected recurrent-EOM principle and makes the local field comparable under unequal annual sample sizes. The pointwise minimum is the same conservative repeated-observation principle as recurrent-EOM, but it acts on local fixed-radius density **before mode construction**, not on HDBSCAN EOM after a 10/10 hierarchy has already been built.

## 2. Firewall

Use only target-excluded GMN 2022+2023 development data.

The inclusive protected solar-longitude interval `[20.0,55.0]` is removed before graph construction, annual counts, density estimation, hierarchy construction, ranking, or truth evaluation.

Forbidden:

- OrbitTrace target information or target-region events;
- SonotaCo event/truth access in the GMN experiment;
- ASFN or EFN event-level access;
- AMOS scientific access;
- MAARSY or DMS scientific access;
- orbital elements in candidate construction;
- any label or known-shower identity in density, hierarchy, candidate generation, or ranking.

## 3. Exact sparse development panels

Reuse exactly the already-frozen `ORBITTRACE_SCALE_STRESS_V1` deterministic nested samples:

`H(eid) = uint64_be(SHA256('ORBITTRACE_SCALE_STRESS_V1|' + eid)[0:8])`.

Exactly eight pooled 2022+2023 panels:

- denominator `128`, buckets `0,1,2,3`;
- denominator `1024`, buckets `0,1,2,3`.

No additional denominator, bucket, salt, replicate, bootstrap, or sample-size choice is authorized.

These panels directly test the architecture at approximately ~5.8k and ~0.7k pooled events, where the fixed 10/10 HDBSCAN support mechanism is known to become weak/inactive.

## 4. Physical embedding and radius graph — unchanged from #1284

Order events deterministically by event ID.

Use the exact fixed physical embedding from #1284:

- `h_sol = 2 sin(5 deg / 2)`;
- `h_rad = 2 sin(4 deg / 2)`;
- `h_logv = ln(1.1)`;

`Z = [cos(sol)/h_sol, sin(sol)/h_sol, cos(lat)cos(lon)/h_rad, cos(lat)sin(lon)/h_rad, sin(lat)/h_rad, log(vg)/h_logv]`.

Construct the exact symmetric Euclidean radius graph with

`r = 1.0`.

The radius, embedding, metric, and exact-neighbor rule are inherited unchanged from #1284. No kNN graph, mutual-reachability graph, local scaling, adaptive radius, or bandwidth search is permitted.

## 5. Sole scientific change — recurrent local density

For each exact sparse panel let:

- `N_22` = number of accessible 2022 events in the panel;
- `N_23` = number of accessible 2023 events in the panel;
- `N(i)` = exact radius-1.0 neighbors of event i, including i itself;
- `d_22(i)` = number of neighbors in `N(i)` belonging to 2022;
- `d_23(i)` = number of neighbors in `N(i)` belonging to 2023.

Define

`rho_22(i) = d_22(i) / N_22`

`rho_23(i) = d_23(i) / N_23`

and the sole ToMATo weight

`rho_rec(i) = min(rho_22(i), rho_23(i))`.

Rules:

- self remains part of the radius neighborhood exactly as in #1284; therefore it contributes only to its own year count;
- zero recurrent density is allowed when one year has no event in the local radius neighborhood;
- no pseudocount, epsilon, floor, clipping, log transform, power, harmonic/geometric/arithmetic blend, weighted minimum, annual exposure model, or local re-normalization is allowed;
- no event is deleted because `rho_rec=0`;
- annual identities are used only in this frozen density formula and later truth evaluation, never known-shower labels.

Pretruth identities must verify for every point:

- finite `rho_22`, `rho_23`, `rho_rec`;
- `rho_rec >= 0`;
- `rho_rec <= rho_22` and `rho_rec <= rho_23`;
- year-swap invariance of the complete `rho_rec` vector;
- if `rho_22 == rho_23`, `rho_rec` equals that common value exactly within numerical representation.

## 6. ToMATo hierarchy and candidate universe

Fit GUDHI `3.12.0` ToMATo with:

- `graph_type='manual'` using the exact fixed radius graph;
- `density_type='manual'` using `rho_rec` as weights.

Construct the **complete** ToMATo hierarchy exactly as #1284 did:

- every leaf basin;
- every internal merge-node membership from `children_`;
- every connected-component root membership;
- exact membership deduplication.

Only after the complete hierarchy exists, retain/report memberships having at least **4 events**. This support-4 reporting floor is inherited from the already-frozen sparse known-stream truth convention and is not a density/core-neighbor requirement.

No root deletion, finite-feature-only selection, antichain cut, lineage scheduling, component-count selector, or hierarchy pruning is permitted.

## 7. Native ranking — exact #1284 rule applied to the new density field

The ranking rule is unchanged scientifically from the frozen `topomodal_sparse_recovery_v1.topomodal_ranked` architecture, except that every density-derived quantity is computed from `rho_rec` rather than `rho_pool`.

Let GUDHI's finite mode prominence values be the sorted `diagram_[:,0]-diagram_[:,1]` sequence. As in the frozen #1284 implementation, the i-th `children_` merge node is created at the i-th nondecreasing prominence value; the workflow must verify GUDHI's `merge_threshold_` cluster-count identity for every unique prominence before any truth access.

For each support-4 hierarchy membership compute:

- `is_root`;
- creation prominence in the ToMATo prominence hierarchy;
- non-root prominence span to its immediate enclosing hierarchy node;
- peak `rho_rec` among its members;
- mean `rho_rec` among its members;
- member count;
- deterministic membership hash.

Rank exactly:

### roots

1. roots before non-roots;
2. peak recurrent density descending;
3. mean recurrent density descending;
4. member count descending;
5. family hash ascending.

### non-roots

1. prominence span descending;
2. peak recurrent density descending;
3. mean recurrent density descending;
4. member count descending;
5. family hash ascending.

No recurrent-EOM score, original pooled-density score, map-equation score, lineage round, overlap/diversity term, learned model, or truth-derived feature is blended into the order.

Deterministic candidate prefix: `RDTM1`.

## 8. Why this is not a closed lane

This successor is scientifically distinct from the already-closed mechanisms:

- **density-synchronous recurrent-EOM** left HDBSCAN's pooled 10/10 hierarchy unchanged and changed only a local FOSC quality by integrating the pointwise annual minimum of alive-mass curves; this method removes HDBSCAN entirely and changes the density field from which fixed-radius ToMATo modes/hierarchy are created;
- **cross-year-core HDBSCAN** replaced each point's HDBSCAN core distance by an opposite-year **10th-neighbor** distance, then still condensed at `min_cluster_size=10`; this method has no k-neighbor order, no mutual reachability, no MST core-distance geometry, and no support-10 condensation;
- **local-kNN year mixing** was a rank-only enrichment of a fixed recurrent-EOM candidate catalogue; this method changes candidate topology upstream using global fixed-radius annual density estimates;
- **reciprocal transfer / cross-year consensus/core** constructed or matched annual cluster models/cores; this method uses one pooled graph, one scalar symmetric recurrent density field, and no annual cluster matching;
- **generic thinning persistence** rescored structures by survival under subsampling; thinning is not an input or score here—the deterministic sparse panels are evaluation panels only;
- **map-equation / intrinsic persistence / lineage scheduling** acted after the pooled-density #1284 candidate hierarchy existed; this method changes which modes and hierarchy nodes exist before ranking.

## 9. Mandatory pretruth freeze

For all eight sparse panels, before shower truth can be loaded, serialize:

- exact event-universe hash and annual event totals;
- fixed physical embedding/graph configuration;
- complete recurrent-density vector hash plus summary;
- exact ToMATo leaf/merge/root counts;
- every support-4 candidate membership and complete deterministic order;
- every recurrent-EOM comparator membership and complete deterministic order;
- all source/artifact hashes and firewall flags.

Write `RECURRENT_DENSITY_TOPOMODAL_V1_PRELABEL.json`, SHA-256 seal it, and verify it in a separate workflow step. Only then may known-shower truth be loaded.

Any implementation failure before this immutable SHA exists is an engineering no-result. Engineering repair may not change the formula or ranking above.

## 10. Comparator and truth semantics

Comparator: exact selected recurrent-EOM HDBSCAN v1 on each identical sparse subset:

- GEO6;
- HDBSCAN min cluster size 10;
- min samples 10;
- Euclidean;
- annual normalized recurrent EOM;
- normal recurrent FOSC/EOM extraction;
- exact selected-parent ranking.

Before truth, comparator candidate membership summaries must reproduce the authoritative #1284 structural stress artifact exactly.

Use the exact established annual truth metric separately for 2022 and 2023 inside each pooled subset:

- annual shower eligibility: at least 4 truth events;
- qualified candidate/shower match: dominant-shower precision `>=0.5` and overlap `>=4`;
- report qualified matches, recovered@25/@50/@100/@500, top-100 dominant precision, MRR, and median top-500 fragmentation.

Equal budget per sparse subset:

`K = number of recurrent-EOM comparator candidates`.

Evaluate all K comparator candidates and exactly the first K recurrent-density topomodal candidates. Complete successor coverage is reporting-only.

## 11. Frozen promotion gates — unchanged

Use exactly the same ten gates as the previous #1284 sparse truth experiments.

### Fine sparse scale `d=1024`

1. successor qualified total strictly greater than recurrent-EOM;
2. qualified matches nonlower in at least 6/8 annual panels;
3. mean MRR not lower;
4. mean top-100 dominant precision not lower;
5. mean fragmentation not higher.

### Coarse sparse scale `d=128`

6. successor qualified total not lower;
7. qualified matches nonlower in at least 6/8 annual panels;
8. mean MRR not lower;
9. mean top-100 dominant precision not lower;
10. mean fragmentation not higher.

All ten are required for `PASS_RECURRENT_DENSITY_TOPOMODAL_V1`.

Any failure returns `FAIL_RECURRENT_DENSITY_TOPOMODAL_V1` and closes this exact recurrent-density formula/ranking. No alternate annual combiner or density transform may be selected from the outcome.

## 12. Conditional exposed transfer

Before the GMN result is opened, freeze a conditional SonotaCo 2013/2014 direct-transfer benchmark using the exact historical four-panel matched evaluator, budgets, and selected recurrent-EOM controls.

Only a GMN PASS may execute it. SonotaCo remains **EXPOSED DEVELOPMENT ONLY**.

## 13. Interpretation

A PASS would be the first architecture in this line to combine:

- fixed-radius/sample-size-resilient candidate construction;
- recurrent local support encoded without a fixed-k core requirement;
- superior sparse known-stream recovery/purity;
- noninferior early ranking/MRR relative to recurrent-EOM.

That would justify moving immediately to the already-frozen exposed transfer benchmark and then exact full-GMN scalability/recovery work without changing the scientific method.

A FAIL closes this exact architecture.