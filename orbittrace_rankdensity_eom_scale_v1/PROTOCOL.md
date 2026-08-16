# OrbitTrace rank-density EOM cross-scale structural diagnostic v1

## Status

**FROZEN BEFORE IMPLEMENTATION AND BEFORE ANY DIAGNOSTIC OUTCOME.**

This is a zero-label structural diagnostic only. It is not yet a shower-recovery successor and cannot promote a paper method.

It follows the target-excluded zero-label findings in PRs #1272–#1277:

- fixed HDBSCAN support becomes too coarse as catalogue size falls;
- absolute nearest-neighbor radii shift strongly with sample size;
- the same event's *ordering* by raw local compactness remains highly stable under an 8× thinning stress (overall median support Spearman ≈0.889 in #1277);
- event-level inner/outer spacing surprise is well calibrated in distribution but too resampling-sensitive;
- ordinary distance-single-link lifetime, additive FOSC, and the frozen robust-single-link anchor do not provide a reliable pruning layer.

The present diagnostic asks whether the stable object — **survey-relative local-density ordering** — can define a scale-normalized density cluster tree whose EOM-selected memberships are more coherent across sample size than exact recurrent-EOM HDBSCAN `10/10`.

This is a distinct upper-level-set density-tree architecture. It does not modify or rescue #1275's closed distance-single-link log-mass FOSC score.

## 1. Firewall

Use only target-excluded GMN 2022+2023 geometry under exact GEO6. Remove inclusive solar longitude `[20.0,55.0]` before geometry.

Forbidden:

- OrbitTrace target information or target-region events;
- shower labels/truth in any statistic, selection, gate, or interpretation;
- SonotaCo scientific access;
- ASFN or EFN event-level access;
- AMOS scientific access;
- MAARSY or DMS scientific access;
- tuning any support, score, percentile transform, tie rule, threshold, subset, salt, graph, or gate from the result.

## 2. Frozen subsets

Reuse exact PR #1272 hash rule:

`H(eid) = uint64_be(SHA256('ORBITTRACE_SCALE_STRESS_V1|' + eid)[0:8])`.

Use exactly four nested pairs:

- coarse denominator `128`, buckets `0,1,2,3` (~5.8k events);
- fine denominator `1024`, same buckets (~0.7k events).

No other denominator, bucket, salt, or replicate is authorized.

## 3. Local density ordering

For each subset independently:

1. compute exact Euclidean GEO6 distance from every event to its **3rd nearest other event** (`r3`);
2. the third-neighbor anchor corresponds to total local support four, the project's established minimum evaluable shower support;
3. sort events from densest to sparsest by ascending `(r3, event_id)`;
4. assign unique empirical density percentile

`q_i = 1 - rank_i/(n+1)`

with one-based `rank_i` in that deterministic ordering.

Thus `q_i` lies strictly in `(0,1)`, larger means locally denser, and every subset has the same uniform empirical set of percentile levels regardless of its absolute density scale.

No alternative k/support or percentile definition is authorized.

## 4. Parameter-free connectivity skeleton

Construct the exact Euclidean minimum-spanning tree (MST) on GEO6 using the already-audited HDBSCAN single-link implementation:

- `hdbscan==0.8.43`;
- `min_samples=1`;
- `min_cluster_size=2` only to expose the complete Euclidean MST/tree;
- Euclidean metric;
- `algorithm='boruvka_kdtree'`;
- `approx_min_span_tree=False`;
- `gen_min_span_tree=True`.

PR #1274's implementation-equivalence audit proved this construction exactly matches sklearn Euclidean single linkage on all eight frozen sparse-scale subsets.

The MST supplies connectivity only. Its edge lengths never enter density level, branch quality, pruning, or ranking.

## 5. Rank-density merge tree

Interpret each vertex `i` as becoming active when the descending density threshold reaches `q_i`. An MST edge `(u,v)` becomes active when both endpoints are active, at level

`ell(u,v) = min(q_u,q_v)`.

Sweep edge levels from high to low. At each unique level, merge all currently connected components induced by MST edges with that level **simultaneously** into one parent component. Equal-level binary ordering is forbidden.

This produces an upper-level-set merge tree of the empirical local-density-rank field over a parameter-free Euclidean connectivity skeleton.

For every non-root component branch `C`:

- `B(C)` = the percentile level at which the branch is created;
- `D(C)` = its parent branch's creation level;
- branch lifetime `L(C)=B(C)-D(C)`;
- branch mass `m(C)` = number of events in its constant membership during that branch interval.

Leaves have birth `q_i`. Internal branches are born at their simultaneous merge level.

The root is never selectable.

## 6. EOM-style pruning

A branch is output-eligible only if `m(C) >= 4`. This minimum affects selection only; it does not alter the MST or merge-tree construction.

Define dimensionless excess-mass quality

`Q(C) = [m(C)/n] * [B(C)-D(C)]`.

Apply bottom-up FOSC/EOM extraction on the rank-density merge tree:

1. compare eligible parent `Q(C)` with the sum of optimal selected qualities in all child subtrees;
2. select the parent iff `Q(C)` is **strictly greater** than child sum;
3. on equality, retain the child solution (or empty solution if there is no positive eligible child), preventing zero-lifetime/simultaneous merges from creating arbitrary candidates;
4. ineligible branches have zero own quality and pass through their optimal child solution;
5. the root always passes through its child solution and is never selected.

There is no persistence threshold, candidate-count target, or result-informed rescue.

## 7. Exact recurrent-EOM comparator

On every same subset reconstruct exact selected recurrent-EOM HDBSCAN v1 unchanged:

- GEO6;
- `min_cluster_size=10`;
- `min_samples=10`;
- Euclidean;
- exact annual-normalized recurrent-EOM kernel;
- exact FOSC extraction.

No truth is opened.

## 8. Cross-scale membership metric

Reuse the exact nested cross-scale identity metric frozen in PR #1275.

For each bucket and each method separately:

1. let `F` be selected memberships on denominator 1024;
2. let `C` be selected memberships on denominator 128;
3. restrict each coarse membership to the fine event universe and discard restricted sets with fewer than four events;
4. for every fine membership compute best Jaccard to any retained restricted coarse membership;
5. record event-weighted mean best Jaccard, unweighted median best Jaccard, and exact restricted-match fraction.

## 9. Frozen interpretation gate

Return

`SUPPORTS_RANKDENSITY_EOM_CROSS_SCALE_COHERENCE`

iff all of the following hold:

1. rank-density EOM produces at least one eligible selected branch in all eight subsets;
2. pooled event-weighted mean best Jaccard across all four nested pairs is strictly greater for rank-density EOM than recurrent-EOM;
3. median of the four bucket-level event-weighted mean best Jaccards is strictly greater for rank-density EOM;
4. rank-density EOM has a strictly greater bucket-level event-weighted mean best Jaccard in at least three of four buckets.

Otherwise return

`REFUTES_RANKDENSITY_EOM_CROSS_SCALE_COHERENCE`.

No numerical Jaccard threshold and no mixed verdict are authorized.

## 10. Consequence

A positive result establishes only cross-scale structural viability and authorizes one separately frozen GMN 2022+2023 scientific evaluation of the exact rank-density EOM architecture (with its ranking/extraction rules frozen before truth).

A negative result closes this exact third-neighbor empirical-rank + Euclidean-MST + percentile-EOM architecture. It may not be rescued by changing k/support, graph, rank transform, lifetime transform, mass exponent, EOM tie rule, branch-size threshold, subset, salt, or gate after seeing the result.
