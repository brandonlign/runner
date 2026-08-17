# OrbitTrace cross-year PP-SBM scale v1 — frozen zero-label protocol

## Status

**FROZEN BEFORE IMPLEMENTATION AND BEFORE ANY SCIENTIFIC OUTCOME FOR THIS MECHANISM.**

This is a zero-label structural screen only. It cannot open GMN shower truth, cannot access SonotaCo, and cannot promote a method over the current full-GMN champion by itself.

The current full-GMN development champion remains density-synchronous recurrent-EOM HDBSCAN v1 (#1263). Multiple later zero-label recurrence constructions have established a specific structural problem without using the protected target: hard pooled/cross-year connectivity can produce extremely stable but giant recurrent background structures, while flat hierarchy catalogues can overrepresent nested variants. This experiment does **not** split or tune the failed `(4,4)` bicore. It returns to the raw inherited cross-year physical graph and replaces threshold-connected-component extraction with an independently motivated statistical partition model.

## Independent statistical motivation

Use the Bayesian **degree-corrected planted partition model** (PP-SBM), which searches specifically for assortative communities while accounting for heterogeneous node degree and selects the partition complexity through description length rather than a user-chosen number of groups.

Primary method references:

- Zhang & Peixoto, *Statistical inference of assortative community structures*, Phys. Rev. Research 2, 043271 (2020), DOI `10.1103/PhysRevResearch.2.043271`, arXiv `2006.14493`.
- Peixoto, *Efficient Monte Carlo and greedy heuristic for the inference of stochastic block models*, Phys. Rev. E 89, 012804 (2014), DOI `10.1103/PhysRevE.89.012804`, arXiv `1310.4378`.

The implementation is the graph-tool PP-SBM/description-length inference path validated in a data-free runtime probe before this protocol was frozen.

## Frozen runtime

The graph-tool runtime is pinned by immutable container digest:

`tiagopeixoto/graph-tool@sha256:4e613c0da8cfb85c05661c124da0ef2d167ec4a5a3347ae10a8f5030bab0a375`

Required runtime version string:

`3.6 (commit fd9762d9, Sun Aug 2 18:45:30 2026 +0200)`

Data-free probe run `32082462606` established that under this exact image:

- `PPBlockState(uniform=False, deg_corr=True)` is available;
- `minimize_blockmodel_dl(...)` is available;
- OpenMP can be fixed to one thread;
- two fits with the same RNG seed return identical canonical partitions;
- a synthetic connected graph containing five strong planted bipartite communities is recovered as five PP-SBM blocks.

No scientific GMN row entered that probe.

## Firewall and immutable panel source

Use only target-excluded GMN 2022+2023.

Inclusive solar longitude `[20.0,55.0]` must be removed by the already-audited parser before geometry or graph construction. No protected event may enter any PP-SBM input.

Forbidden throughout Stage 1:

- GMN shower labels / hidden truth;
- OrbitTrace target information, target events, coordinates, membership, activity outcome, or rank;
- SonotaCo 2013/2014 scientific access;
- ASFN/EFN event-level access;
- AMOS scientific access;
- MAARSY or DMS scientific access;
- orbital elements or orbital distances;
- station metadata;
- uncertainty metadata;
- any post-result search over radius, model class, seed, support, degree correction, uniform prior, number of groups, graph projection, or gate.

The eight sparse panel universes and zero-label reference capacities come only from the already-sealed endpoint artifact:

- source run `32037435314`;
- artifact `9291169452`;
- artifact digest `sha256:af497634e100883b0448737465e27b4e523ffa85f48979c829125e95acfc58ac`;
- exact `BIFILTRATION_GMN_RANKING_V1_PRELABEL.json` SHA-256 `95f8a57718a30b2c7e85016d505276d72cccb9e4ac1d6eb29f13067efc73dd0c`.

Frozen panels are denominators `128,1024`, buckets `0,1,2,3`, with reference capacities:

- `d=128`: `29,35,38,33`;
- `d=1024`: `8,5,6,9`.

These K values are a zero-label structural capacity floor only. Any later truth comparison must be separately frozen against #1263.

## Exact raw cross-year graph

For each sparse panel independently:

1. reconstruct exact normalized target-excluded events;
2. sort events by stable event ID;
3. compute exact inherited six-dimensional GEO6 embedding from the frozen recurrent-EOM parent geometry;
4. query exact Euclidean radius `r=1.0`, `p=2`, `eps=0`;
5. discard self edges and every same-year edge;
6. retain only undirected 2022↔2023 edges with exact GEO6 distance `<=1.0`;
7. remove only vertices with **zero** retained cross-year degree before PP-SBM inference.

The zero-degree removal is not a fitted threshold: a vertex with no cross-year edge carries no recurrence relation in this graph. No positive-degree cutoff, bicore peel, k-core, butterfly/bitruss filter, same-year edge, halo, nearest-neighbor fallback, or graph projection is allowed.

## Frozen PP-SBM inference

For each panel, construct one undirected graph containing only the positive-cross-year-degree vertices and the frozen cross-year edges.

Run graph-tool with:

- `openmp_set_num_threads(1)`;
- `state=PPBlockState`;
- `state_args=dict(uniform=False, deg_corr=True)`;
- `minimize_blockmodel_dl(...)` with all other arguments at graph-tool 3.6 defaults.

No number of groups B is supplied. Partition complexity is selected by the PP-SBM description length.

The RNG seed for panel `(d,b)` is not hand-selected:

`seed = uint32_be(SHA256('ORBITTRACE_CROSSYEAR_PPSBM_SCALE_V1|' + str(d) + '|' + str(b))[0:4]) & 0x7fffffff`.

Run the exact inference **twice with the same seed**. Canonicalize each partition as the sorted collection of sorted event-ID memberships. The two canonical partitions and description lengths must be identical. This duplicate run is a determinism/integrity check, not a model search; no alternate seed is eligible.

## Candidate families

Each inferred PP-SBM block is one candidate membership.

A block is eligible for the Stage-1 structural catalogue iff it contains at least:

- `4` events from 2022; and
- `4` events from 2023.

The value `4` is the long-frozen minimum recurrent-stream support constant. Blocks failing this support rule are recorded but are not candidate families. No block is split, merged, expanded, trimmed, reassigned, or connected-component postprocessed.

Because PP-SBM is a partition, eligible candidate memberships must be pairwise disjoint automatically; this is verified explicitly.

Candidate IDs are SHA-256 hashes of sorted event IDs. A deterministic **diagnostic** order may be serialized by descending `min(n2022,n2023)`, descending internal cross-year edge count, descending member count, then membership SHA-256. This diagnostic order is **not authorized for shower-truth evaluation**.

## Cross-scale structural test

For each nested bucket, compare `d=1024` fine families to `d=128` coarse families.

Restrict every coarse eligible PP-SBM block to the exact fine event universe, discard restricted memberships that no longer contain at least four events from each year, deduplicate identical restrictions, then compute each fine family's best Jaccard overlap with any surviving coarse restriction. The bucket score is the mean best Jaccard across fine families.

Compute the same already-established mean-best-Jaccard reference from the immutable recurrent-EOM memberships stored in the sealed endpoint artifact.

No labels enter either calculation.

## Frozen Stage-1 gates

All gates are mandatory:

1. `immutable_endpoint_source`: exact sealed endpoint SHA reproduces.
2. `runtime_pin`: exact graph-tool image digest and version reproduce.
3. `strict_crossyear_graph_all`: every inference edge joins different years and has GEO6 distance `<=1.0`.
4. `positive_degree_inference_all`: every PP-SBM input vertex has at least one retained cross-year edge.
5. `fixed_seed_repeatability_all`: both same-seed fits yield identical canonical partitions and description lengths in every panel.
6. `candidate_membership_universe_all`: every candidate event belongs to its frozen panel universe.
7. `annual_support_floor_all`: every eligible family has at least four members from each year.
8. `pairwise_disjoint_all`: eligible family memberships do not overlap within a panel.
9. `capacity_at_least_reference_k_all_8`: eligible family count is at least frozen reference K in all eight panels.
10. `cross_scale_nonlower_4_of_4`: PP-SBM mean-best-Jaccard is at least recurrent reference in every nested bucket.
11. `cross_scale_mean_not_lower`: mean PP-SBM cross-scale score across four buckets is at least recurrent reference mean.
12. `firewall`: no truth, target, SonotaCo, ASFN/EFN event rows, AMOS, MAARSY, DMS, orbital, station, or uncertainty information is accessed.

PASS verdict:

`PASS_CROSSYEAR_PPSBM_SCALE_V1_PRETRUTH`

Otherwise:

`FAIL_CROSSYEAR_PPSBM_SCALE_V1_PRETRUTH`

## Promotion / closure boundary

A Stage-1 PASS means only that a nonparametric degree-corrected assortative partition of the raw cross-year graph is structurally viable enough to justify a **separately preregistered** target-excluded GMN ranking/comparison against #1263. No shower truth may be opened until that Stage-2 protocol exists and freezes its ranking/evaluation rule.

A Stage-1 FAIL permanently closes this exact raw-cross-year degree-corrected PP-SBM v1 architecture. Do not rescue by changing the graph radius, dropping degree correction, enabling `uniform=True`, changing seeds, trying multiple seeds/restarts after outcome, fixing B, using nested/general/overlapping SBM as a v1 patch, adding bicore/bitruss/butterfly filtering, projecting the graph, splitting blocks, changing support, or weakening the gates. A future genuinely distinct statistical model would require independent motivation and a new preregistration.
