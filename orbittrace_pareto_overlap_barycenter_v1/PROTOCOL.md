# OrbitTrace overlap-barycenter Pareto v1

## Status

**FROZEN BEFORE IMPLEMENTATION, BEFORE ANY D=64 ZERO-LABEL OUTCOME, AND BEFORE ANY D=64 SHOWER-TRUTH OUTCOME.**

This is one new mechanism only. It addresses the single structural failure exposed by the closed d=64 translation of recurrent–TopoModal Pareto-prominence v1: at higher density, a support-resolved TopoModal candidate can overlap more than one Recurrent-EOM parent, so the former scalar `corroborating_parent_rank` is undefined.

No result-informed threshold, parent choice, splitting rule, membership edit, budget change, or truth-aware ranking is permitted.

## Scientific hypothesis

The successful sparse Pareto method uses Recurrent-EOM rank as one objective and TopoModal modal prominence as the other. Its dense failure is a correspondence failure, not evidence that either ordering signal is invalid.

For a TopoModal candidate `s`, let the pairwise-disjoint Recurrent parents it overlaps be `p_j` with Recurrent ranks `r_j`, and let `n_j = |s ∩ p_j|`.

Define the **overlap-barycenter parent rank**

`R_bar(s) = sum_j n_j * r_j / sum_j n_j`.

Rules:
- retain a TopoModal candidate iff it overlaps at least one Recurrent parent;
- use every overlapping parent with its exact integer event-overlap count;
- do not choose a best parent;
- do not split, trim, intersect, union, or otherwise alter TopoModal membership;
- unmatched events inside `s` do not create an artificial parent and do not enter the normalized barycenter;
- if `s` overlaps exactly one parent, `R_bar(s)` must equal that parent rank exactly. Thus on the previously successful sparse panels the mechanism reduces exactly to the original Pareto parent-rank objective.

This is a deterministic many-to-many correspondence statistic, not a fitted score.

## Prior-work distinction

This is not:
- the closed exact unique-parent overlap-consensus/Pareto rule, which aborts on >1 parent;
- child-per-parent selection, round-robin, interleaving, Jaccard/overlap thresholds, or parent insertion;
- support-mask membership replacement;
- component-union expansion;
- truth-searched membership switching;
- representative-share supervision;
- a global reranking learned from labels.

Repository search before freeze found no prior exact overlap-weighted parent-rank barycenter mechanism.

## Data/firewall

Use only target-excluded GMN 2022+2023 development data. Inclusive protected solar longitude `[20.0,55.0]` is excluded before geometry, sampling, candidate construction, correspondence, ranking, prelabel serialization, or truth evaluation.

Forbidden during this experiment:
- protected target information/events;
- SonotaCo event/truth access;
- AMOS, MAARSY, DMS, ASFN/EFN event-level data;
- orbital elements or shower labels in candidate construction/ranking;
- post-result parameter or rule changes.

## Test scale

Use the already-frozen scale-stress hash exactly:

`H(eid)=uint64_be(SHA256('ORBITTRACE_SCALE_STRESS_V1|' + eid)[0:8])`.

Test only denominator `d=64`, buckets `0,1,2,3`, the scale where the exact unique-parent method structurally failed. No other denominator or salt is authorized in this binding experiment.

## Candidate construction

For each d=64 panel, reconstruct without modification:
1. the frozen support-resolved TopoModal cut (`r=1.0`, support floor 4, same GUDHI ToMATo hierarchy/cut);
2. the frozen Recurrent-EOM comparator on the identical events;
3. full pairwise event-overlap counts between each TopoModal candidate and every Recurrent parent.

Retain every TopoModal candidate with positive overlap mass. Preserve its full membership and native support rank.

For each retained candidate serialize:
- all overlapping parent ranks;
- all exact overlap counts;
- total overlap mass;
- `R_bar`;
- minimum/maximum overlapping parent rank for audit only.

## Pareto ranking

The second objective is unchanged from the positive Pareto-prominence source:

`M(s)` = ordinal rank under modal contrast descending, then native support rank ascending, then family hash ascending.

Use ordinary non-dominated layers minimizing `(R_bar, M)`.

Final deterministic order:
1. Pareto layer ascending;
2. `M` ascending;
3. `R_bar` ascending;
4. native support rank ascending;
5. family hash ascending.

No coefficients, thresholds, transforms, crowding distance, quotas, learned model, or alternate tie order.

## Mandatory zero-label pretruth gates

Before truth can open, SHA-256 seal the complete d=64 prelabel. All must pass:
1. exact firewall, d=64 hash selection, and source hashes;
2. support-cut memberships pairwise disjoint in all four panels;
3. Recurrent memberships pairwise disjoint and continuously ranked;
4. every retained candidate has positive overlap mass and every discarded candidate has zero overlap mass;
5. full TopoModal membership is unchanged for every retained candidate;
6. `R_bar` is finite and lies within the min/max ranks of overlapping parents;
7. exact unique-parent identity: for every one-parent candidate, `R_bar == parent_rank`;
8. modal prominence ranks are a permutation;
9. Pareto dominance/layers and final order are deterministic and continuous;
10. candidate capacity is at least equal-budget `K = number of Recurrent candidates` in every panel;
11. at least one multi-parent candidate exists, proving the new mechanism is active;
12. sparse-source compatibility audit: applying this formula to the frozen positive d=128/d=1024 Pareto source would leave all `R` values and final orders unchanged because all retained source candidates are unique-parent.

Only `PASS_PARETO_OVERLAP_BARYCENTER_V1_PRETRUTH` authorizes truth.

## Binding truth metrics/gates

For d=64 bucket × year (8 annual panels), use the exact established annual truth semantics and equal budget K. Report recovery, recovered@25/50/100/500, top-100 dominant precision, median top-500 fragmentation, zero-filled eligible-query MRR, reciprocal-rank mass, and historical conditional MRR diagnostically.

Mandatory five gates, inherited from the closed d=64 translation:
1. qualified total not lower than Recurrent-EOM;
2. qualified recovery nonlower in at least 6/8 annual panels;
3. mean zero-filled eligible-query MRR not lower;
4. mean top-100 dominant precision not lower;
5. mean fragmentation not higher.

All five required for `PASS_PARETO_OVERLAP_BARYCENTER_V1`; otherwise binding `FAIL_PARETO_OVERLAP_BARYCENTER_V1`.

A PASS would show the correspondence failure is fixable without sacrificing the frozen GMN retrieval/precision contract and authorize only a separately frozen denser/full-GMN stage. A FAIL closes this exact barycenter rule; no rescue by alternate overlap powers, best-parent choice, Jaccard weighting, unmatched penalties, harmonic/geometric rank means, thresholds, or result-informed transforms.