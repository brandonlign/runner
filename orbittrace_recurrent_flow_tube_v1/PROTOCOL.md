# OrbitTrace recurrent flow-tube detector v1 — frozen protocol

## Status and provenance

This document freezes a genuinely new OrbitTrace methodology branch before any valid GMN 2023 held-out outcome is obtained.

Binding upstream governance: PR #1190. The exposed SonotaCo v32–v60 successor sequence remains permanently closed. PR #1194 is prior GMN evidence only; because it developed on 2022/2023 jointly, it is not used as this branch's held-out protocol and its SonotaCo compatibility result, if any, may not motivate this method.

Firewall state at design freeze:

- `target_information_access=false`
- `target_region_events_accessed=false`
- `maarsy_scientific_access=false`
- `dms_scientific_access=false`
- protected solar longitude `[20°,55°]` is removed before labels, candidate construction, fitting, scoring, diagnostics, endpoints, or model selection.
- SonotaCo 2013/2014 is not accessed during architecture development or GMN testing.

## 1. Scientific problem

Sparse meteor streams create a joint clustering and association problem rather than a single-density clustering problem. A physical stream may be locally weak, non-convex in radiant/speed space, change smoothly with solar longitude, and appear as several disconnected local fragments. Existing OrbitTrace GMN evidence (#839, #1194) shows severe proposal fragmentation: many qualified candidate fragments may map to one known shower.

The method therefore targets a specific weakness: **recover a stream as one physically continuous, recurrent trajectory through observing strata, rather than as whichever local density fragment happens to rank highest.**

## 2. Core mechanism

Name: **Recurrent Flow-Tube (RFT) detector**.

The central object is a directed path of local meteor micro-atoms across independent solar-longitude strata. It is not an HDBSCAN hierarchy, DBSCAN connected component, OPTICS reachability ordering, or a reranking of HDBSCAN output.

### 2.1 Exact event representation

For every eligible meteor event after the blind exclusion, use only quantities already available in the frozen GMN runtime:

1. solar-centered radiant longitude,
2. ecliptic latitude,
3. geocentric speed,
4. solar longitude for ordering/stratification.

Radiant longitude and latitude are embedded as a 3-D unit vector. Speed is represented as `log(v_g)`. The 4-D state is therefore `(u_x,u_y,u_z,log(v_g))`.

No orbital elements are used.

### 2.2 Independent observing strata

Within one calendar year, sort eligible events by solar longitude and divide the accessible solar-longitude domain into fixed non-overlapping **2° bins**. The protected `[20°,55°]` interval is absent before binning. Bins with fewer than 4 eligible events produce no micro-atoms.

### 2.3 Local micro-atoms

Inside each 2° bin, compute the physical dissimilarity

`d(i,j)^2 = (theta_ij / 3°)^2 + (log(v_i/v_j) / log(1.08))^2`,

where `theta_ij` is radiant angular separation.

For each event, identify its 4 nearest neighbors within the same stratum. A **micro-atom** is a maximal set of at least 4 events connected only by *reciprocal* 4-nearest-neighbor links satisfying `d(i,j) <= 1`.

This local construction is deliberately not the scientific output. It only provides small, high-purity local atoms for the cross-stratum association mechanism. No density hierarchy, core-distance transformation, epsilon sweep, or cluster-stability extraction is performed.

For each atom record:

- circular/embedded radiant centroid,
- median log-speed,
- event count,
- robust within-atom median `d` to the atom medoid,
- stratum center,
- exact member IDs.

### 2.4 Flow compatibility across strata

Atoms may connect only forward to atoms whose stratum centers are 2°, 4°, or 6° later in accessible solar longitude, without crossing the blind interval.

For atom `a` at solar longitude `lambda_a` and atom `b` at `lambda_b`, define the drift-normalized transition cost

`C(a,b) = (theta(mu_a,mu_b)/(1.5° + 0.20*DeltaLambda))^2 + (log(v_a/v_b)/(log(1.04)+0.004*DeltaLambda))^2`,

with `DeltaLambda` in degrees.

A directed edge exists iff `C(a,b) <= 1`.

The formula allows smooth radiant/speed drift while becoming modestly more tolerant across one skipped stratum. These constants are frozen before GMN 2022 development results and are not searched.

### 2.5 Recurrent flow tubes

A candidate tube is a maximal directed path/component in the atom DAG satisfying all of:

- at least 3 occupied strata,
- span of at least 6° solar longitude,
- at least 10 unique meteor events,
- no event may belong to two atoms within the same final tube; if paths converge, the lower total transition-cost path owns the shared downstream atom, with deterministic atom-ID tie break.

This path ownership rule is the explicit anti-fragmentation mechanism: multiple nearby local fragments may compete, but a physical stream is represented by one globally coherent recurrent trajectory.

### 2.6 Perturbation persistence and noise rejection

For development and deployment, perform exactly **16 deterministic perturbation replicas**. Each replica applies a zero-mean deterministic pseudo-random perturbation indexed by event ID and replica:

- radiant tangent-plane perturbation sigma = `0.35°`,
- multiplicative speed perturbation sigma = `1.0%`.

These are fixed conservative observational perturbations, not learned uncertainty estimates.

Run sections 2.2–2.5 independently in each replica. Match replica tubes to the unperturbed tube by maximum event Jaccard overlap. Define

`P = number of replicas with Jaccard >= 0.50 / 16`.

A final tube is retained iff `P >= 0.50`.

This is persistence under realistic observational perturbation, not HDBSCAN cluster stability: there is no density hierarchy or birth/death integral.

### 2.7 Final membership construction

For every retained tube, collect the union of events from its unperturbed atoms. Compute a robust local trajectory by linear least-squares radiant-unit-vector and log-speed drift against solar longitude using the tube's events. A member is retained only if its standardized residual to that trajectory is `<= 2.5` under the same 3° / 8% physical scales. Refit once after this trimming; no iterative threshold search is allowed.

Final candidates with fewer than 10 members after trimming are discarded.

### 2.8 Candidate score

The ranking score is fixed and interpretable:

`S = P * log1p(N) * log1p(K) / (1 + median_transition_cost + median_trajectory_residual)`,

where:

- `P` = perturbation persistence,
- `N` = final member count,
- `K` = occupied 2° strata,
- `median_transition_cost` = median cost of selected DAG transitions,
- `median_trajectory_residual` = median final standardized trajectory residual.

Candidates are ranked by descending `S`, then descending `P`, then descending `N`, then deterministic candidate ID.

No learned reranker is part of RFT v1.

## 3. Novelty

The proposed novelty is the **meteor-specific recurrent flow-tube construction**: sparse local meteor atoms are globally associated as a single directed, physically drifting trajectory across solar-longitude strata, and the resulting tube must survive explicit observational perturbations before final membership is built.

The central mechanism is cross-stratum trajectory association plus perturbation persistence. Density is only used indirectly to form tiny reciprocal-neighbor atoms.

## 4. Comparison with existing approaches

### HDBSCAN

RFT does not use mutual-reachability distance, a single-linkage density hierarchy, condensed trees, or HDBSCAN stability extraction. It does not begin with HDBSCAN candidates. Removing recurrence/strata from RFT destroys its core DAG trajectory-association mechanism rather than reducing it to HDBSCAN.

### DBSCAN

RFT does not produce final clusters from fixed-radius connectivity. The reciprocal-neighbor atom stage is local and intentionally incomplete; final streams require multi-stratum directed association, path ownership, perturbation survival, and trajectory-consistent membership.

### OPTICS

RFT has no reachability ordering or valley extraction.

### v31

v31 is a strict-OOF local-geometry ranker over an existing SonotaCo proposal universe. RFT is an event-level candidate generator, consolidator, final-membership constructor, and ranker. It does not reuse v31 scoring.

### Prior OrbitTrace GMN methods / #839 / #1194

#839 and #1194 rank a 4,504-family proposal union and retain severe fragmentation as a ranking problem. RFT instead attempts to prevent fragmentation through one path-ownership/flow-tube object before ranking.

### Graph/community clustering

RFT uses a graph, but not generic community detection. The graph is a directed acyclic cross-stratum association graph with meteor-specific smooth-drift transition physics, deterministic path ownership, perturbation recurrence, and a trajectory-based final membership layer. Removing those meteor-specific constraints leaves no equivalent community-clustering objective.

## 5. Interpretability

- reciprocal local atoms: high-purity local evidence without requiring a global density level;
- cross-stratum edges: physically plausible stream drift;
- path ownership: prevents duplicated fragments from representing one trajectory;
- minimum occupied strata/span: recurrence requirement;
- perturbation persistence: rejects unstable/noise-induced candidates;
- trajectory trimming: constructs final membership around the inferred physical drift tube;
- score: rewards persistence, membership support, and recurrence while penalizing incoherent transitions/residuals.

## 6. Frozen GMN 2022 development protocol

Development data: **target-excluded GMN 2022 only**.

Permitted on GMN 2022:

- engineering validation that event fields parse correctly;
- verification that the blind exclusion occurs before all scientific operations;
- computation of the frozen RFT v1 output;
- known-shower evaluation of the frozen v1 architecture;
- the preregistered ablations in section 8;
- mechanism diagnostics listed below.

Not permitted:

- changing numerical constants after seeing a GMN 2022 result;
- searching thresholds, k, physical scales, perturbation count/amplitude, score weights, bin width, rank cutoffs, or alternate distance functions;
- looking at GMN 2023 while changing the method.

GMN 2022 is used to decide only whether this already-frozen architecture is sufficiently viable to justify the one-shot GMN 2023 test.

Development viability gate:

- at least 120 qualified known-shower matches in the complete retained candidate catalogue;
- recovered known showers at top 100 >= 55;
- top-100 dominant precision >= 0.60;
- median qualified candidates per recovered known shower at top 500 <= 3.0;
- at least 75% of top-100 retained candidates have perturbation persistence `P >= 0.75`.

If this viability gate fails, RFT v1 terminates without GMN 2023 access. A successor is not automatic.

## 7. Frozen one-shot GMN 2023 held-out test

Held-out data: **target-excluded GMN 2023 only**.

Before loading 2023 labels or evaluating 2023 output, source SHA, protocol SHA, every constant above, feature fields, candidate rules, scoring, evaluation code, and success gate must be frozen in the repository.

Primary metrics:

1. distinct qualified known showers represented in the full retained catalogue;
2. recovered known showers at ranks 25, 50, 100, and 500;
3. top-100 dominant precision;
4. mean reciprocal rank of represented known showers;
5. fragmentation: median qualified candidate count per recovered known shower within top 500.

Held-out PASS requires all of:

- full-catalogue qualified known showers >= 120;
- recovered@100 >= 58;
- recovered@50 >= 35;
- top-100 dominant precision >= 0.65;
- fragmentation median <= 3.0;
- no firewall/provenance violation.

`USEFUL_BUT_INSUFFICIENT` requires all firewall/provenance checks plus at least four of the five numerical gates above, with recovered@100 >= 52.

Otherwise verdict is FAIL.

No GMN 2023 result may change RFT v1.

## 8. Frozen ablations

Ablations are GMN 2022 only and are explanatory, not model-selection searches.

Exactly three are allowed:

1. **No path ownership**: allow every maximal compatible path to emit independently; tests whether global ownership actually reduces fragmentation.
2. **No perturbation persistence**: set retention to the unperturbed tubes only; tests whether perturbation survival rejects unstable noise.
3. **No trajectory trim**: use atom-union membership directly; tests whether final physical trajectory membership improves purity.

All other architecture variants are unauthorized.

## 9. Preregistered mechanism diagnostic and stopping rule

If GMN 2023 FAILS, one diagnostic may be computed from already-generated held-out outputs without changing candidate order:

- `coverage_failure`: fewer than 120 qualified known showers exist anywhere in the complete retained RFT catalogue;
- `ranking_failure`: at least 120 are represented, but recovered@100 < 58;
- `fragmentation_failure`: fragmentation median > 3.0;
- `purity_failure`: top-100 dominant precision < 0.65.

A successor is authorized only when **exactly one** failure class is active and the corresponding GMN-2022 ablation/mechanism evidence already points to one specific structural correction. If multiple failure classes are active, or the development ablations do not identify a unique mechanism, terminate the branch.

No successor may be justified by shower identities, rank-boundary identities, alternate metrics, or SonotaCo outcomes.

## 10. SonotaCo boundary

Only an RFT version that receives `PASS` on the one-shot GMN 2023 test may proceed to a separately frozen SonotaCo 2013/2014 matched benchmark.

SonotaCo remains **EXPOSED DEVELOPMENT/BENCHMARK DATA ONLY**, never external validation. RFT must not be modified after its SonotaCo result.

Comparators at that stage, if authorized, are HDBSCAN, relevant frozen literature comparators, v31 where scientifically meaningful, and the strongest relevant pre-existing OrbitTrace method.
