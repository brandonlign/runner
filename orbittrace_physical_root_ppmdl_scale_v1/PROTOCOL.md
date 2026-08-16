# OrbitTrace physical-root Bayesian planted-partition MDL scale diagnostic v1

## Status

**FROZEN BEFORE IMPLEMENTATION AND BEFORE ANY DIAGNOSTIC OUTCOME.**

This is a zero-label structural diagnostic only. It cannot promote a paper method or open shower truth.

## Scientific motivation

The exact fixed-scale topomodal family (#1284 and its frozen successors) has now repeatedly shown that broad physical families survive severe catalogue thinning and recover substantially more known streams than fixed-support recurrent-EOM, but complete-hierarchy scalar ranking repeatedly places those streams too late. A separately frozen graph-permutation significance test also found no individually significant finite q-density modes while the broad physical root/component families retained the recovery advantage.

The remaining structural question is therefore not another hierarchy score. It is whether the **interior of each broad fixed physical family can be represented as an automatically selected assortative graph partition** rather than as every nested density state.

This diagnostic uses the Bayesian planted-partition model of Zhang & Peixoto (Phys. Rev. Research 2, 043271, 2020), implemented by graph-tool. The model is nonparametric in community count and uses description-length/Bayesian model selection rather than a user-selected cluster count, modularity resolution, persistence cutoff, or density threshold.

This is distinct from the permanently closed historical recurrent-core/halo membership-expansion family: no existing candidate is expanded, no seed candidate is used, no orbital element is used, and no membership radius beyond the already-frozen #1284 physical graph is introduced.

## 1. Firewall

Use only target-excluded GMN 2022+2023 geometry. Remove inclusive solar longitude `[20.0,55.0]` before geometry.

Forbidden:

- OrbitTrace target information or target-region events;
- shower labels/truth in any statistic, fit, candidate, gate, or interpretation;
- SonotaCo scientific access;
- ASFN or EFN event-level access;
- AMOS scientific access;
- MAARSY or DMS scientific access;
- result-informed graph radius, physical scale, community-count constraint, resolution parameter, prior, model option, support, random-seed search, restart count, subset, salt, metric, or gate change.

## 2. Frozen nested subsets

Reuse exact PR #1272 identity rule:

`H(eid) = uint64_be(SHA256('ORBITTRACE_SCALE_STRESS_V1|' + eid)[0:8])`.

Use exactly four nested pairs:

- coarse denominator `128`, buckets `0,1,2,3`;
- fine denominator `1024`, the same buckets.

No other denominator, bucket, salt, or replicate is authorized.

## 3. Exact fixed physical graph

Reuse #1284 physical embedding and graph without modification:

- `h_sol = 2 sin(5°/2)`;
- `h_rad = 2 sin(4°/2)`;
- `h_logv = ln(1.1)`;
- `Z = (cos(sol)/h_sol, sin(sol)/h_sol, cos(lat)cos(lon)/h_rad, cos(lat)sin(lon)/h_rad, sin(lat)/h_rad, ln(v_g)/h_logv)`;
- exact symmetric Euclidean radius `r=1.0`;
- sort observations by exact event ID before graph construction.

For this graph-partition model, self-neighborhood entries used by #1284 only for density counting are **not graph edges**. The undirected graph contains exactly one edge `{i,j}` for every distinct pair with Euclidean `Z` distance `<=1.0`.

No edge weight, kNN edge, adaptive radius, density value, recurrence weight, or kernel is permitted.

## 4. Physical-root separation

Compute exact connected components of the frozen radius-1 graph.

Each connected component is modeled **independently**. Components are never joined by the statistical model. This keeps the already-established broad physical roots as hard outer boundaries while replacing their internal density hierarchy with an inferential partition.

Components with fewer than four observations cannot yield an evaluable candidate and are skipped.

## 5. Bayesian planted-partition extraction

Implementation is graph-tool stable release `2.98`, official image tag `tiagopeixoto/graph-tool:release-2.98`. The execution must record `graph_tool.__version__` and the pulled image RepoDigest. Scientific execution requires reported graph-tool version to begin with `2.98`; otherwise stop before any diagnostic metric.

For each physical connected component independently:

1. create its exact simple undirected induced graph;
2. set both NumPy RNG and graph-tool RNG to the deterministic component seed below;
3. call `graph_tool.inference.minimize_blockmodel_dl(graph, state=graph_tool.inference.PPBlockState)` with **no scientific argument overrides**;
4. use the returned best-fit bottom partition directly;
5. canonicalize block labels only by their exact sorted event-ID memberships;
6. retain every inferred block with member count >=4 as one candidate;
7. discard inferred blocks below support 4; do not merge, grow, rerun, or replace them with their parent root.

The `PPBlockState` is the degree-corrected Bayesian planted-partition model provided by graph-tool. No alternative SBM, nested hierarchy, overlap model, modularity objective, normalized-cut objective, degree-correction toggle, flat/nonflat comparison, posterior sampling, refinement sweep, annealing, multiple restart, or model averaging is authorized.

### Deterministic RNG rule

For a component with sorted event IDs `ids`, denominator `d`, and bucket `b`, define

`component_hash = SHA256('|'.join(ids))`

and

`seed = uint32_be(SHA256('ORBITTRACE_PHYSICAL_ROOT_PPMDL_SCALE_V1|' + str(d) + '|' + str(b) + '|' + component_hash)[0:4])`.

Use exactly that seed once. No seed search or restart selection is allowed.

## 6. Candidate semantics

The complete successor candidate set on a subset is the union of all support>=4 best-fit planted-partition blocks across its physical connected components.

Candidate identity is exact member set. Deduplicate exact duplicate memberships defensively; no overlapping/nested alternative representations are added.

This diagnostic has **no ranking**.

## 7. Exact recurrent-EOM comparator

On each identical subset reconstruct exact recurrent-EOM HDBSCAN v1 unchanged:

- GEO6;
- `min_cluster_size=10`;
- `min_samples=10`;
- Euclidean;
- exact annual-normalized recurrent-EOM kernel;
- exact FOSC/EOM extraction.

No truth is opened.

## 8. Cross-scale metric

Reuse #1284 exactly.

For each bucket and method:

1. let `F` be fine-subset candidates;
2. restrict every coarse candidate to the exact fine event universe;
3. discard restricted memberships below support 4;
4. deduplicate exact restricted memberships;
5. for every fine candidate record best Jaccard similarity to any retained restricted coarse candidate;
6. record candidate-unweighted mean/median best Jaccard, exact-match fraction, and candidate counts.

Primary metric: fine→coarse candidate-unweighted mean best Jaccard.

## 9. Frozen interpretation gate

Return

`SUPPORTS_PHYSICAL_ROOT_PPMDL_CROSS_SCALE_COHERENCE`

iff all five #1284-style conditions hold:

1. at least one eligible planted-partition candidate exists in all eight subsets;
2. in every fine subset, planted-partition candidate count is at least exact recurrent-EOM candidate count;
3. pooled fine→coarse candidate-unweighted mean best Jaccard is strictly greater than recurrent-EOM;
4. median of the four bucket-level fine→coarse mean-best-Jaccards is strictly greater than recurrent-EOM; and
5. planted-partition extraction has a strict bucket-level mean-best-Jaccard win in at least three of four buckets.

Otherwise return

`REFUTES_PHYSICAL_ROOT_PPMDL_CROSS_SCALE_COHERENCE`.

No mixed verdict and no post-result rescue.

## 10. Consequence

A positive result establishes only zero-label structural viability and authorizes one **separately frozen** target-excluded GMN recovery/ranking successor. Before that successor opens shower truth, its ranking/evidence rule and all promotion gates must be frozen independently.

A negative result permanently closes this exact physical-root + degree-corrected Bayesian planted-partition MDL architecture. It may not be rescued by changing graph-tool model class, degree correction, graph scale, component boundary, support, seed, restart count, optimizer arguments, subset, salt, metric, or gate after outcome.