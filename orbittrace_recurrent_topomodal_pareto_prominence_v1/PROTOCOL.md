# OrbitTrace recurrent–TopoModal Pareto-prominence v1 — frozen protocol

## Status

**FROZEN BEFORE IMPLEMENTATION, BEFORE THE ZERO-LABEL STRUCTURAL OUTCOME, AND BEFORE ANY SHOWER-TRUTH OUTCOME FOR THIS SUCCESSOR.**

This is one new target-excluded GMN successor motivated by the already-sealed sequence:

1. overlap-consensus v1 retained full TopoModal modes corroborated by one Recurrent-EOM parent and passed 9/10 truth gates, but failed coarse zero-filled MRR because multiple children of the same early parent crowded the equal-budget prefix;
2. component-union v1 preserved one slot per Recurrent-EOM parent but failed because merging the children back into the broad parent removed the modal isolation that made those children useful;
3. the binding component-union closure therefore requires a new architecture that preserves individual TopoModal modes while preventing parent rank alone from making every sibling appear early.

The source rows already contain a second independent, truth-free signal: `modal_contrast`, the TopoModal mode's density prominence (`active_mode_peak - outside_merge_level`). Persistence-based mode clustering uses such birth/death prominence to quantify the significance/prominence of density modes (Chazal, Guibas, Oudot & Skraba, *JACM* 60(6), 2013, DOI 10.1145/2535927). The new rule combines parent recurrence evidence and the child's own modal prominence by ordinary non-dominated sorting, a parameter-free Pareto construction rather than a learned or hand-weighted score (cf. Deb et al., *IEEE TEC* 6(2), 2002, DOI 10.1109/4235.996017).

No prior closed method is rerun under a new metric. Candidate order is genuinely different and is frozen here before outcome.

## 1. Firewall

Use only the already-frozen target-excluded GMN 2022+2023 sparse development panels.

Inclusive solar longitude `[20.0,55.0]` remains excluded.

Forbidden throughout this experiment:

- OrbitTrace target information or target-region events;
- SonotaCo 2013/2014 scientific access;
- ASFN/EFN event-level access;
- AMOS scientific access;
- MAARSY or DMS scientific access;
- shower-truth-informed thresholds, ranks, Pareto objectives, tie rules, source quotas, candidate budgets, or post-result rescue.

## 2. Immutable zero-label source

Use only the sealed overlap-consensus Stage-1 prelabel:

- workflow run `32072681272`;
- pretruth artifact ID `9302288262`;
- file `RECURRENT_TOPOMODAL_OVERLAP_CONSENSUS_V1_PRELABEL.json`;
- SHA-256 `bd0d28410d23bef0c5c8847ecd8d54e91b74e148ce62e8533407787d265e468f`.

For each of eight sparse panels this source contains:

- every uniquely Recurrent-overlap-confirmed TopoModal child;
- the exact child's full event membership;
- its unique `corroborating_parent_rank`;
- its frozen `modal_contrast`, `active_mode_peak`, `outside_merge_level`, and `native_support_rank`;
- exact Recurrent-EOM parent rows and equal reporting budget `K`;
- exact annual event identities.

The later overlap-consensus truth result and component-union truth result are not candidate-construction inputs.

## 3. Sole successor — two-view Pareto-prominence order

For one panel let the complete overlap-confirmed TopoModal child set be `S={s_1,...,s_N}`.

For each child `s` define two **truth-free** ordinal objectives, both minimized:

### Objective A — recurrence priority

`R(s) = corroborating_parent_rank(s)`.

This is the exact Recurrent-EOM rank of the unique parent corroborating `s` by exact event overlap. It is inherited only as one objective; it is not by itself the final ordering key.

### Objective B — intrinsic modal-prominence rank

Construct one deterministic total order of the N children by:

1. descending `modal_contrast` (larger mode prominence is better);
2. ascending frozen `native_support_rank`;
3. ascending `family_hash`.

Let `M(s)` be the one-indexed position in that order.

No normalization, coefficient, transform, threshold, quantile, or fitted calibration is applied to either objective.

### Pareto depth

For two distinct children `a,b`, say `a` dominates `b` iff

- `R(a) <= R(b)` and `M(a) <= M(b)`, and
- at least one inequality is strict.

Assign ordinary non-dominated layers:

1. layer 1 is the set not dominated by any other child;
2. remove layer 1;
3. layer 2 is the non-dominated set of the remainder;
4. continue until every child has exactly one positive integer layer `L(s)`.

Because siblings have the same `R`, a sibling with stronger intrinsic prominence rank necessarily dominates a weaker sibling. Thus the construction delays weaker siblings without a one-child-per-parent quota or deletion.

### Final total order

Order all N children lexicographically by:

1. ascending `L(s)`;
2. ascending `M(s)`;
3. ascending `R(s)`;
4. ascending frozen `native_support_rank`;
5. ascending `family_hash`.

All candidates are retained exactly once and all memberships remain byte-for-byte unchanged. The first `K` rows are the equal-budget successor catalogue.

There is:

- no parent candidate in the successor;
- no union/intersection or membership alteration;
- no child deletion;
- no one-child-per-parent quota;
- no alternating/round-robin source schedule;
- no component-best evidence transfer;
- no learned score;
- no weighted/Borda/geometric-mean rank fusion;
- no crowding-distance parameter or diversity coefficient;
- no year-, scale-, bucket-, or budget-specific exception.

This is distinct from the old exposed-SonotaCo v46 Pareto-component placement lane: v46 transferred another member/component's rank evidence onto fixed HDB candidates. Here the two coordinates belong directly to the retained TopoModal child: its unique Recurrent parent rank and its own topological prominence. No old SonotaCo component identity, graph, truth, selector, or candidate enters this experiment.

## 4. Zero-label structural authorization gate

Before shower truth is opened, persist `RECURRENT_TOPOMODAL_PARETO_PROMINENCE_V1_PRELABEL.json` containing the exact reordered children, ranks, layers, objective ranks, source memberships, and audit fields.

All eight panels must satisfy:

1. immutable source SHA and all firewall flags reproduce exactly;
2. candidate identity set is exactly the source overlap-confirmed candidate set;
3. every candidate membership is byte-for-byte unchanged;
4. all source `modal_contrast` values are finite and nonnegative and equal `active_mode_peak - outside_merge_level` within floating-point tolerance;
5. the modal-prominence rank is a permutation `1..N` under the frozen ordering;
6. Pareto layers are valid: every candidate is assigned exactly once and no candidate in a layer is dominated by a candidate remaining in that same layer;
7. final successor order is a deterministic permutation of all N source candidates;
8. successor candidates remain pairwise event-disjoint;
9. candidate capacity `N >= K` in all eight panels;
10. among the first K rows, the number of distinct corroborating Recurrent parents is **strictly greater than inherited-parent overlap-consensus v1 in all four coarse `d=128` panels**;
11. among the first K rows, distinct-parent count is **not lower than overlap-consensus v1 in all four fine `d=1024` panels**;
12. on the four frozen nested `d=1024 -> d=128` bucket pairs, top-K successor mean-best-Jaccard membership stability is at least Recurrent-EOM in all 4/4 pairs and in the aggregate mean.

The overlap-consensus distinct-parent controls are read directly from the immutable source ordering; no truth is needed to compute them.

Only `PASS_RECURRENT_TOPOMODAL_PARETO_PROMINENCE_V1_PRETRUTH` authorizes the truth job. A structural FAIL closes this exact rule without shower-truth access.

No structural result may alter the objectives, Pareto dominance relation, final tie order, or any gate.

## 5. Truth semantics and ranking metric

If and only if pretruth passes, use the same established target-excluded GMN sparse truth runtime and match semantics as overlap-consensus/component-union:

- annual shower eligibility requires at least 4 events in that panel-year;
- positive match requires precision `>= 0.5` and overlap `>= 4`;
- equal candidate budget `K` per panel;
- report qualified matches, recovered@25/@50/@100/@500, top-100 dominant precision, historical conditional MRR, zero-filled eligible-query MRR, and median top-500 fragmentation.

Historical conditional MRR is diagnostic only.

The preregistered ranking gate is zero-filled eligible-query MRR:

- `RR(q)=1/r_q` for an eligible recovered shower at first positive rank `r_q`;
- `RR(q)=0` for an eligible unrecovered shower;
- `MRR_zero = mean_q RR(q)` over all eligible showers.

For each scale, aggregate by the same unweighted mean across its eight annual bucket-year panels used in the previous frozen sparse endpoints.

## 6. Binding ten-gate promotion contract

### Fine sparse scale (`d=1024`)

1. successor qualified-total is **strictly greater** than Recurrent-EOM;
2. successor qualified matches are nonlower in at least `6/8` annual panels;
3. successor mean zero-filled eligible-query MRR is at least Recurrent-EOM;
4. successor mean top-100 dominant precision is at least Recurrent-EOM;
5. successor mean median top-500 fragmentation is no higher than Recurrent-EOM.

### Coarse sparse scale (`d=128`)

6. successor qualified-total is at least Recurrent-EOM;
7. successor qualified matches are nonlower in at least `6/8` annual panels;
8. successor mean zero-filled eligible-query MRR is at least Recurrent-EOM;
9. successor mean top-100 dominant precision is at least Recurrent-EOM;
10. successor mean median top-500 fragmentation is no higher than Recurrent-EOM.

All ten gates are mandatory.

Return exactly one binding verdict:

- `PASS_RECURRENT_TOPOMODAL_PARETO_PROMINENCE_V1`, or
- `FAIL_RECURRENT_TOPOMODAL_PARETO_PROMINENCE_V1`.

The first technically valid truth execution is binding.

## 7. Closure

A PASS authorizes only a separately frozen scale/full-GMN translation stage. It does not authorize protected target access, external-superiority claims, or parameter search.

A valid FAIL permanently closes this exact two-objective Pareto-prominence architecture. Do not rescue it by:

- replacing `modal_contrast` with another TopoModal score after outcome;
- changing Pareto objectives or dominance direction;
- normalizing or weighting objectives;
- using Pareto crowding distance, hypervolume, epsilon dominance, second-order thresholds, or frontier-only deletion;
- reversing the frozen within-layer tie order;
- imposing one-child-per-parent, per-parent quotas, round-robin scheduling, or source quotas;
- adding parent candidates, union/intersection candidates, or orphan candidates;
- changing K or tuning by scale/bucket/year;
- learning a reranker or using shower labels;
- post-result threshold/rank/window search.

Any later method must be scientifically distinct and separately frozen before truth.
