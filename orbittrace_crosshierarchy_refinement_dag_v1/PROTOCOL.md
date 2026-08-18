# OrbitTrace cross-hierarchy refinement DAG v1

## Status

**FROZEN ZERO-LABEL STRUCTURAL DIAGNOSTIC BEFORE EXECUTION.**

This is not a truth-scored detector and is not a repair of the closed recurrent-Pareto inactivity router. It tests a genuinely different representation motivated by a structural fact that the closed router exposed before truth: support-resolved TopoModal children can overlap multiple recurrent-EOM parents at dense scale, so forcing a unique parent is not generally a valid correspondence model.

The diagnostic asks whether the canonical many-to-many overlap structure itself is stable enough under deterministic thinning to justify a separately frozen future detector.

The post-freeze edit following technical no-result run `32184246575` changes **provenance wording only**: the raw support-resolved TopoModal parent is rebound against its own immutable support-resolved-cut prelabel, not against the later overlap-consensus/Pareto successor chain. No hierarchy, membership rule, graph, atom, metric, panel, gate, threshold, firewall, or interpretation boundary is changed.

## 1. Scientific question

Can recurrent-EOM and support-resolved TopoModal be related through a label-free bipartite correspondence DAG whose canonical common-refinement atoms are more stable under thinning than either hierarchy alone?

The representation does **not** choose one parent, average parent ranks, resolve parent sets, alter either hierarchy, or use shower truth. Every overlap is retained exactly.

This is motivated by two established ideas, used only at the representation level:

- correspondence-based comparison of hierarchical clusterings rather than assuming node identity across samples;
- DAG/multi-parent clustering structures when a tree representation is too restrictive.

No literature method is copied as a detector. OrbitTrace's object here is the exact event-overlap relation between two already-frozen meteor candidate hierarchies.

## 2. Firewall

Use only target-excluded GMN 2022+2023 development geometry already authorized for structural diagnostics.

Before any geometry or hierarchy construction, exclude inclusive solar longitude `[20.0,55.0]`.

Forbidden throughout this diagnostic:

- shower labels or truth metrics;
- OrbitTrace target identity, coordinates, members, orbital information, or protected-region events;
- SonotaCo scientific access;
- ASFN/EFN event-level access;
- AMOS scientific access;
- MAARSY or DMS scientific access;
- any result-informed scale, support, graph, overlap, degree, pruning, weighting, rank, or gate change.

## 3. Exact nested panels

Reuse only the established deterministic `ORBITTRACE_SCALE_STRESS_V1` subsets:

`H(eid) = uint64_be(SHA256('ORBITTRACE_SCALE_STRESS_V1|' + eid)[0:8])`.

Construct exactly 12 pooled 2022+2023 panels:

- denominator 64, buckets 0,1,2,3;
- denominator 128, buckets 0,1,2,3;
- denominator 1024, buckets 0,1,2,3.

For each fixed bucket, `d=1024` is nested inside `d=128`, which is nested inside `d=64`.

No new salt, bucket, denominator, replicate, bootstrap, or random seed is authorized.

## 4. Frozen parent representations

### 4.1 Recurrent-EOM

Reconstruct exact recurrent-EOM HDBSCAN v1 unchanged:

- exact GEO6 geometry;
- `min_cluster_size=10`;
- `min_samples=10`;
- Euclidean HDBSCAN hierarchy;
- annual-normalized recurrent EOM extraction;
- exact selected memberships.

Ranking is irrelevant to this diagnostic except as provenance; no recurrent score enters the DAG.

### 4.2 Support-resolved TopoModal cut

Reconstruct the already-frozen support-resolved TopoModal cut unchanged:

- the flagship physical embedding and radius `1.0` graph;
- manual radius-count density;
- GUDHI ToMATo hierarchy;
- minimum support `4` only as inherited by the frozen support-resolved cut;
- exact deterministic cut that partitions each reportable TopoModal root;
- no alternative persistence threshold or hierarchy selection.

For d=128 and d=1024, unordered recurrent memberships and raw support-resolved TopoModal memberships must reproduce the immutable `TOPOMODAL_SUPPORT_RESOLVED_CUT_V1_PRELABEL.json` from authoritative run `31961908008`, artifact `9267530845`, prelabel SHA-256 `4529eadd9ff93aae057f0a6fd5e0dd923f2300b7c6e01b74a0b7638e22da6de6`, before accepting this diagnostic.

No sealed d=64 support-resolved-cut output is required or invented. d=64 is reconstructed from the same immutable parent implementations because the predecessor support-resolved-cut experiment froze only d=128/d=1024 panels and this diagnostic does not require unique-parent correspondence.

## 5. Cross-hierarchy correspondence DAG

For a panel let `T={T_i}` be the pairwise-disjoint support-resolved TopoModal memberships and `R={R_j}` the pairwise-disjoint recurrent-EOM memberships.

Create a bipartite graph with:

- one node for every `T_i`;
- one node for every `R_j`;
- an edge `(i,j)` iff `T_i ∩ R_j` is nonempty.

No overlap threshold is used. Any nonempty event intersection is an edge.

For every edge define its **common-refinement atom**

`A_ij = T_i ∩ R_j`.

Because both parent families are internally disjoint, all nonempty atoms in one panel must be pairwise disjoint. This is an invariant, not a fitted rule.

Record without pruning:

- exact atom event IDs and hashes;
- atom size;
- TopoModal-node degree;
- recurrent-node degree;
- connected-component IDs in the bipartite graph;
- number/fraction of TopoModal nodes with degree >1;
- number/fraction of recurrent nodes with degree >1;
- joint covered-event count `|union(T) ∩ union(R)|`;
- complete atom coverage of that joint support.

The diagnostic does not turn atoms into a ranked detector catalogue.

## 6. Cross-scale stability metric

Evaluate exactly eight nested transitions:

- d=64 -> d=128 for each bucket 0..3;
- d=128 -> d=1024 for each bucket 0..3.

For every transition, the finer/sparser event universe is the comparison universe. Project each denser-panel membership onto that exact nested universe and discard only empty projections.

For any two membership families `A` and `B`, define directional event-weighted mean-best-Jaccard:

`D(A->B) = sum_a |a| max_b J(a,b) / sum_a |a|`,

where `J` is ordinary Jaccard on the nested universe.

Define symmetric stability:

`S(A,B) = (D(A->B) + D(B->A))/2`.

Compute `S` separately for:

1. recurrent-EOM memberships;
2. support-resolved TopoModal memberships;
3. all nonempty common-refinement atoms.

No atom-size cutoff, correspondence threshold, matching algorithm, rank, or truth metric enters this score.

## 7. Frozen structural interpretation gate

Return

`SUPPORTS_CROSSHIERARCHY_REFINEMENT_DAG_V1`

iff all of the following hold:

1. all 12 panel universes and protected-region exclusions reproduce exactly;
2. d=128/d=1024 recurrent and raw support-resolved TopoModal memberships reproduce the immutable support-resolved-cut prelabel exactly;
3. every panel's atoms are pairwise disjoint, nonempty, and their union equals `union(T) ∩ union(R)` exactly;
4. the representation is genuinely exercising the motivating topology: at least one d=64 panel contains a TopoModal node with degree >1;
5. pooled mean symmetric atom stability across the eight transitions is strictly greater than pooled mean recurrent-EOM stability;
6. pooled mean symmetric atom stability is strictly greater than pooled mean support-resolved TopoModal stability;
7. median symmetric atom stability across the eight transitions is strictly greater than the corresponding recurrent-EOM median;
8. median symmetric atom stability is strictly greater than the corresponding TopoModal median;
9. atoms strictly beat **both** parent representations on at least 5 of 8 transitions.

Otherwise return

`REFUTES_CROSSHIERARCHY_REFINEMENT_DAG_V1`.

A tie does not count as a strict win.

These gates intentionally require the common-refinement representation to add structural stability beyond the already-strong TopoModal parent. Merely resolving the multi-parent bookkeeping problem is not enough.

## 8. Interpretation boundary

A SUPPORTS result authorizes only one separately frozen follow-up that asks how to extract a detector catalogue from the DAG/common-refinement representation without truth-informed tuning. It does not itself authorize a ranking, atom-size threshold, connected-component merge, parent weighting, or OrbitTrace search.

A REFUTES result closes the exact unweighted nonempty-overlap common-refinement/DAG representation as the next stability mechanism. Do not rescue it by overlap thresholds, atom-size pruning, edge weights, degree penalties, component contraction, parent preference, Jaccard thresholds, alternate scale-stress subsets, or relaxed gates.

Either outcome remains zero-label structural evidence and does not change the existing recurrent-EOM paper/development result, the fixed-scale TopoModal flagship evidence, or any pristine external-validation result.
