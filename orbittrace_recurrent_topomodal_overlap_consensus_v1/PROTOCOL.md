# OrbitTrace recurrent-TopoModal overlap consensus v1 — frozen protocol

## Status

**FROZEN BEFORE IMPLEMENTATION AND BEFORE ANY SHOWER-TRUTH OUTCOME FOR THIS SUCCESSOR.**

This is one genuinely new target-excluded GMN successor motivated by two already-sealed findings:

1. fixed-scale support-resolved TopoModal repeatedly generates substantially more known-stream candidates than Recurrent-EOM, but several exact ranking/membership successors were closed under their preregistered contracts;
2. the subsequently frozen `orbittrace_mrr_definition_audit_v1` established that the historical OrbitTrace conditional-MRR gate excludes eligible-but-unrecovered showers from its denominator and is therefore non-monotone when recovery counts differ. No prior scientific verdict is reopened by that audit.

This successor does **not** rerun a closed method under a new metric. It defines a different catalogue architecture before outcome: retain only TopoModal modes independently corroborated by exact event overlap with Recurrent-EOM, preserve their full TopoModal memberships, and order them by the corroborating Recurrent-EOM parent rank.

## 1. Firewall

Use only the already-frozen target-excluded GMN 2022+2023 sparse development panels.

Inclusive solar longitude `[20.0,55.0]` remains excluded.

Forbidden throughout this experiment:

- OrbitTrace target information or target-region events;
- SonotaCo 2013/2014 scientific access;
- ASFN/EFN event-level access;
- AMOS scientific access;
- MAARSY or DMS scientific access;
- truth-informed overlap thresholds, rank changes, source quotas, weights, candidate budgets, or post-result rescue.

## 2. Immutable zero-label source

Use only the Stage-1 recurrent-orphan-completion prelabel:

- workflow run `32043362123`;
- artifact `9292356070`;
- file `SUPPORT_CUT_RECURRENT_ORPHAN_COMPLETION_V1_PRELABEL.json`;
- SHA-256 `278d659542668e52033a5369f9afdf685e010a2c14c7ff5211b0b60dd73f2d4a`.

That file was sealed before shower truth and contains for each of eight frozen sparse panels:

- exact Recurrent-EOM candidate memberships and ranks;
- the complete support-resolved TopoModal cut, represented by rows with `catalogue_source in {'support_projection','support_append'}` while retaining each row's original support-cut `rank`;
- exact annual event identities;
- exact equal candidate budget `K`.

The later orphan-completion and support-mask truth results are **not inputs** to candidate construction.

## 3. Sole successor — exact-overlap corroborated TopoModal catalogue

For one frozen panel let:

- `P_1,...,P_K` be the Recurrent-EOM candidates in exact original rank order;
- `S_1,...,S_M` be the complete support-resolved TopoModal cut in exact original support-cut rank order.

For every TopoModal candidate `S_j`, define its corroborating Recurrent-EOM set

`A_j = { r : |S_j intersect P_r| > 0 }`.

No overlap fraction, Jaccard, F1, centroid distance, density threshold, persistence threshold, or fitted score is used.

The sole catalogue rule is:

1. retain `S_j` iff `|A_j| = 1`;
2. discard `S_j` iff `|A_j| = 0`;
3. if any `|A_j| > 1`, the pretruth endpoint is invalid and aborts before shower truth rather than choosing a parent;
4. every retained row keeps the **full original TopoModal membership `S_j`**; membership is not intersected with the Recurrent-EOM parent;
5. assign each retained row the unique corroborating parent rank `a_j`;
6. order retained rows lexicographically by:
   - ascending `a_j` (Recurrent-EOM parent rank),
   - ascending original support-cut rank `j`,
   - ascending deterministic `family_hash` as final tie-break;
7. assign successor ranks `1..N` in that order.

There is no parent candidate in the successor list, no recurrent orphan insertion, no support-only insertion, no membership union/intersection, no learned ranker, and no post-hoc score.

The equal reporting budget remains exactly the Recurrent-EOM candidate count `K`; truth evaluation uses the first `K` successor candidates and the complete `K`-candidate Recurrent-EOM list. Therefore pretruth requires `N >= K` for every panel.

## 4. Zero-label structural authorization gate

Before any shower truth is opened, persist `RECURRENT_TOPOMODAL_OVERLAP_CONSENSUS_V1_PRELABEL.json` containing all exact successor memberships/ranks and audit fields.

All eight panels must satisfy:

1. the immutable source prelabel SHA and firewall flags reproduce exactly;
2. exact Recurrent-EOM ranks are `1..K`;
3. exact original support-cut ranks are unique and recoverable for every support row;
4. support-cut candidates are pairwise disjoint;
5. every retained successor overlaps **exactly one** Recurrent-EOM parent by at least one exact event;
6. every discarded support candidate overlaps **zero** Recurrent-EOM parents;
7. every successor membership is byte-for-byte the full source support membership;
8. successor candidates are pairwise disjoint;
9. successor capacity `N >= K`;
10. the first `K` successor rows contain at least one corroborating parent and are deterministic under the frozen lexicographic order.

Additionally compute on the four already-frozen nested `d=1024 -> d=128` bucket pairs the same membership-only mean-best-Jaccard stability diagnostic used in prior TopoModal structural work. Before truth, require:

11. successor mean-best-Jaccard is at least Recurrent-EOM in **all 4/4** bucket pairs;
12. successor aggregate mean-best-Jaccard is at least Recurrent-EOM.

These structural requirements were selected without shower truth. No structural result may alter the catalogue rule.

Only `PASS_RECURRENT_TOPOMODAL_OVERLAP_CONSENSUS_V1_PRETRUTH` authorizes the binding truth job.

## 5. Truth semantics and corrected reciprocal-rank metric

Use exactly the established target-excluded GMN 2022/2023 sparse truth runtime and the frozen parent match semantics:

- annual shower eligibility requires at least 4 events in that panel-year;
- a candidate/shower match is positive only at precision `>= 0.5` with overlap `>= 4`;
- equal candidate budget `K` per panel;
- report qualified matches, recovered@25/@50/@100/@500, top-100 dominant precision, historical conditional MRR, and median top-500 fragmentation.

### Historical conditional MRR — diagnostic only

Continue reporting the frozen evaluator's existing conditional MRR for audit continuity, but it is **not a promotion gate** for this new successor.

### Pre-frozen zero-filled eligible-query MRR

For every eligible shower label `q`, let `r_q` be its first positive candidate rank. Define

- `RR(q) = 1/r_q` if recovered;
- `RR(q) = 0` if unrecovered.

Then

`MRR_zero = (1 / |E|) * sum_{q in E} RR(q)`.

Equivalently, for the frozen evaluator output when `eligible_labels > 0`,

`MRR_zero = MRR_conditional * qualified_matches / eligible_labels`.

This denominator convention was frozen before this successor outcome and matches the standard reciprocal-rank treatment of an eligible query with no relevant retrieved result as zero. The confirmed audit does not retroactively change any previous result.

For each scale aggregate `MRR_zero` by the same unweighted mean across its eight annual bucket-year panels used by the historical aggregate MRR calculation. Also report pooled reciprocal mass per eligible query as a non-gating diagnostic.

## 6. Binding ten-gate promotion contract

There are eight annual panels per scale.

### Fine sparse scale (`d=1024`)

1. successor qualified-total is **strictly greater** than Recurrent-EOM;
2. successor qualified matches are nonlower in at least `6/8` annual panels;
3. successor mean **zero-filled eligible-query MRR** is at least Recurrent-EOM;
4. successor mean top-100 dominant precision is at least Recurrent-EOM;
5. successor mean median top-500 fragmentation is no higher than Recurrent-EOM.

### Coarse sparse scale (`d=128`)

6. successor qualified-total is at least Recurrent-EOM;
7. successor qualified matches are nonlower in at least `6/8` annual panels;
8. successor mean **zero-filled eligible-query MRR** is at least Recurrent-EOM;
9. successor mean top-100 dominant precision is at least Recurrent-EOM;
10. successor mean median top-500 fragmentation is no higher than Recurrent-EOM.

All ten gates are mandatory.

Return exactly one binding verdict:

- `PASS_RECURRENT_TOPOMODAL_OVERLAP_CONSENSUS_V1`, or
- `FAIL_RECURRENT_TOPOMODAL_OVERLAP_CONSENSUS_V1`.

The first technically valid truth execution is binding.

## 7. Interpretation and closure

A PASS means exact cross-generator corroboration can convert TopoModal's broader candidate coverage into a better joint retrieval/ranking catalogue at equal reporting budget on target-excluded sparse GMN. It authorizes only a separately frozen scale/full-GMN translation stage; it does not authorize protected target access or declare a final champion by itself.

A valid FAIL permanently closes this exact architecture. Do not rescue it by:

- changing exact overlap to a thresholded overlap/Jaccard/F1/containment rule;
- adding centroid distance;
- admitting zero-overlap support candidates;
- selecting only one TopoModal child per parent;
- merging children or using parent memberships;
- adding recurrent orphans;
- source quotas or alternating slots;
- learned or hand-weighted fusion;
- changing support rank tie-breaking;
- changing K;
- tuning separately by scale/bucket/year;
- replacing the pre-frozen zero-filled MRR gate after outcome;
- relaxing any recovery/precision/fragmentation gate.

Any later method must be genuinely distinct and separately frozen before truth.
