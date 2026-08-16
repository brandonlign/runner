# OrbitTrace topomodal lineage-interleaved v2

## Status

**FROZEN BEFORE IMPLEMENTATION AND BEFORE ANY SHOWER-TRUTH OUTCOME FOR THIS SUCCESSOR.**

This is a new successor after `topomodal lineage-balanced v1` was closed as **technically invalid before truth**. V1 never produced an immutable prelabel and never evaluated shower truth. V2 preserves the scientifically motivated part of v1 — preventing nested candidates from one surviving density mode from monopolizing early report slots — but it does **not** reuse, repair, clip, or reinterpret v1's invalid raw-density lifetime.

V2 introduces **no new scalar ranking score**. It reuses the exact already-frozen intrinsic #1284 topomodal ranking from `orbittrace_topomodal_sparse_recovery_v1` and changes only how that fixed order is scheduled across exact ToMATo mode lineages.

## 1. Actual hypothesis

The #1284 fixed-radius ToMATo hierarchy has repeatedly shown superior sparse known-stream candidate coverage and purity relative to recurrent-EOM, but its complete hierarchy contains nested variants of the same modal structure. In the previously frozen intrinsic ranking, those related variants can consume multiple early positions while other surviving modes have not yet been represented.

V2 tests one discrete architectural hypothesis:

> Preserve every #1284 candidate and its already-frozen intrinsic priority, but interleave the ranked list so each distinct surviving-mode lineage receives one report before any lineage receives a second nested report, then one second report before any lineage receives a third, and so on.

There is no overlap threshold, diversity coefficient, lineage quota, candidate deletion, fitted weight, learned model, or truth-dependent decision.

## 2. Firewall

Use only target-excluded GMN 2022+2023 development data. Inclusive solar longitude `[20.0,55.0]` is removed before any geometry, hierarchy, lineage assignment, ranking, or truth evaluation.

Forbidden:

- OrbitTrace target information or target-region events;
- SonotaCo scientific/event-row access in the GMN experiment;
- ASFN or EFN event-level access;
- AMOS scientific access;
- MAARSY or DMS scientific access;
- any result-informed radius, density transform, hierarchy subset, lineage definition, score, tie-break, sample subset, truth metric, or gate change.

## 3. Exact sparse panels

Reuse exactly the already-frozen `ORBITTRACE_SCALE_STRESS_V1` subsets:

`H(eid) = uint64_be(SHA256('ORBITTRACE_SCALE_STRESS_V1|' + eid)[0:8])`.

Exactly eight pooled GMN 2022+2023 subsets:

- denominator `128`, buckets `0,1,2,3`;
- denominator `1024`, buckets `0,1,2,3`.

No new salt, bucket, denominator, bootstrap, or replicate is authorized.

## 4. Candidate generator — complete exact #1284 hierarchy

Candidate generation is unchanged from #1284 / `orbittrace_topomodal_hierarchy_scale_v1`:

- physical embedding with `h_sol = 2 sin(5°/2)`, `h_rad = 2 sin(4°/2)`, `h_logv = ln(1.1)`;
- exact symmetric Euclidean radius graph, `r=1.0`;
- density `rho_i = |N_i|/n`, including self;
- GUDHI `3.12.0` ToMATo, manual graph/manual density;
- every leaf, internal merge-node, and connected-component-root membership;
- exact membership deduplication;
- reporting support floor `4` only after the complete hierarchy exists.

Before truth, each subset must reproduce the authoritative #1284 structural artifact exactly: candidate count and complete sorted `(family_hash, member_count, first_node, is_root)` rows.

## 5. Frozen intrinsic order — reused byte-for-byte scientifically

The base priority is **exactly** `orbittrace_topomodal_sparse_recovery_v1.topomodal_ranked` from source blob

`752df8212ce601227f6e9170b0fe994ba06b515d`

on branch commit

`312b1b718ae105813de242355142a74e7d377d65`.

V2 must call that frozen implementation or prove byte-for-byte-equivalent candidate IDs, candidate metadata, and complete intrinsic order for every subset before any lineage rescheduling.

No field or tie-break in that order may change. In particular, V2 does not invent a replacement for the old intrinsic prominence-span order even though that old global order failed its MRR gates; it uses that exact order as the within-lineage prior.

For each candidate store `intrinsic_rank`, equal to its exact rank from the frozen source above.

## 6. Exact surviving-mode lineage

Lineage assignment is label-free and uses only the already-fixed ToMATo hierarchy and radius-count density.

For each ToMATo leaf:

- `mode_peak` = maximum `rho` among events in that leaf;
- `mode_key` = lexicographically smallest event ID attaining that maximum.

For each internal `children_` merge node:

- inherit the lineage of the child with larger `mode_peak`;
- if peaks are exactly equal, inherit the lexicographically smaller `mode_key`.

Thus every hierarchy node has exactly one `lineage_key = mode_key` corresponding to the density mode that survives through that node. No persistence-to-node pairing and no raw density-level lifetime is used.

For an exact membership deduplicated candidate, use the lineage of its authoritative `first_node`.

Pretruth invariants:

- every eligible #1284 candidate maps to exactly one hierarchy node and one lineage;
- every lineage key is the peak event of one actual ToMATo leaf;
- no candidate membership changes;
- lineage assignment is deterministic under the frozen event-ID ordering.

## 7. Lineage-interleaved ranking

Within each lineage, sort candidates by `intrinsic_rank` ascending — therefore preserving the exact prior order from the already-frozen sparse-recovery successor.

Assign

`lineage_round = 1,2,3,...`

within each lineage in that order.

The final V2 rank is lexicographic:

1. `lineage_round` ascending;
2. `intrinsic_rank` ascending.

Because `intrinsic_rank` is globally unique, no additional tie-break exists or is needed.

Interpretation: round 1 contains the intrinsically highest-ranked available candidate from every lineage; round 2 contains the second-highest from every lineage that has one; etc. The full candidate universe is preserved exactly.

No result-dependent stopping rule is permitted. Evaluation simply truncates this immutable complete ranking at the same comparator budget as before.

## 8. Recurrent-EOM comparator

Use selected recurrent-EOM HDBSCAN v1 unchanged on each exact subset:

- GEO6;
- `min_cluster_size=10`;
- `min_samples=10`;
- Euclidean;
- ordinary condensed tree;
- annual-normalized recurrent quality;
- FOSC/EOM extraction using recurrent stability.

Rank comparator candidates exactly as selected parent:

1. recurrent stability descending;
2. ordinary stability descending;
3. member count descending;
4. deterministic family ID.

Comparator membership summaries must match the authoritative #1284 structural artifact before truth.

## 9. Immutable prelabel boundary

Before shower truth can be loaded, serialize for all eight subsets:

- event-universe hash;
- every successor candidate event ID and unchanged #1284/intrinsic metadata;
- `intrinsic_rank`, `lineage_key`, `lineage_round`, and final V2 rank;
- every comparator candidate and rank;
- exact #1284 membership-summary match;
- exact frozen intrinsic-order match;
- source/artifact hashes and firewall flags.

Write `TOPOMODAL_LINEAGE_INTERLEAVED_V2_PRELABEL.json`, compute and print SHA-256, and verify it in a separate workflow step. Only after that step may shower labels be evaluated.

## 10. Truth metric and equal budget

Use the selected recurrent-EOM parent's existing `metrics(...)` semantics unchanged, separately for 2022 and 2023 inside every pooled subset.

For each subset:

- `K = number of recurrent-EOM comparator candidates`;
- evaluate all `K` comparator candidates;
- evaluate exactly first `K` V2 candidates;
- complete V2 candidate coverage may be reported diagnostically only, never as a promotion gate.

Truth semantics remain:

- annual shower eligibility at least 4 events;
- positive candidate/shower match requires precision `>=0.5` and overlap `>=4`;
- qualified matches, recovered@25/@50/@100/@500, top-100 dominant precision, MRR, and median top-500 fragmentation.

## 11. Frozen ten gates — unchanged

Use exactly the same ten aggregate gates as `topomodal sparse-recovery v1`, map-equation ranking, support-resolved cut, and lineage-balanced v1 intended to use.

### Fine sparse scale `d=1024`

1. successor qualified total strictly greater than recurrent-EOM;
2. successor qualified matches nonlower in at least 6/8 panels;
3. successor mean MRR not lower;
4. successor mean top-100 dominant precision not lower;
5. successor mean fragmentation not higher.

### Coarse scale `d=128`

6. successor qualified total not lower;
7. successor qualified matches nonlower in at least 6/8 panels;
8. successor mean MRR not lower;
9. successor mean top-100 dominant precision not lower;
10. successor mean fragmentation not higher.

All ten must pass for `PASS_TOPOMODAL_LINEAGE_INTERLEAVED_V2`. Otherwise `FAIL_TOPOMODAL_LINEAGE_INTERLEAVED_V2`.

No gate relaxation, weighted aggregate, rank rescue, or post-result variant is authorized.

## 12. Conditional exposed transfer

A SonotaCo 2013/2014 direct-transfer protocol must be frozen **before** this GMN result is opened. It must reuse the historical four-panel matched evaluator, budgets, and selected recurrent-EOM controls. SonotaCo remains exposed development only.

Only a GMN PASS authorizes executing that transfer benchmark.

## 13. Interpretation

A PASS would be the first evidence that the #1284 architecture can combine its demonstrated sparse recovery/purity advantage with noninferior early ranking by removing exact lineage redundancy from early report order, without changing candidate construction or learning a new score.

A FAIL closes this exact lineage-interleaving schedule. Do not change lineage assignment, intrinsic ordering, round schedule, radius, density, support floor, candidate universe, truth metric, or gates after outcome.