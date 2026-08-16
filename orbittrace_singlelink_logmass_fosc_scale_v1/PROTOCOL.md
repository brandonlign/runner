# OrbitTrace scale-free log-mass FOSC pruning diagnostic v1

## Status

**FROZEN BEFORE IMPLEMENTATION AND BEFORE ANY DIAGNOSTIC OUTCOME.**

This is a zero-label structural diagnostic only. It is not a scientific successor and cannot promote a clustering method. It follows PRs #1272–#1274.

PR #1272 showed that exact recurrent-EOM HDBSCAN `10/10` becomes extraction-inert as the same target-excluded GMN geometry is reduced to small-survey sample sizes. PR #1273 isolated a joint finite-support bottleneck. PR #1274 then showed that support-free Euclidean single-link branch lifetime

`L(C) = log(d_parent(C) / d_form(C))`

is materially less sample-size-sensitive than raw linkage distance across all four frozen branch-size bands.

The present diagnostic asks the next necessary question: **can that scale-free hierarchy be pruned without a tuned persistence threshold while preserving branch identity under an 8× sample-size reduction better than the exact selected recurrent-EOM `10/10` hierarchy?**

## 1. Parent and firewall

Lineage starts from the exact PR #1274 positive diagnostic head, itself descended unchanged from selected recurrent-EOM PR #1243.

Use only target-excluded GMN 2022+2023 geometry under exact GEO6. Remove inclusive solar longitude `[20.0,55.0]` before geometry.

Forbidden:

- OrbitTrace target information or target-region events;
- shower labels/truth in any statistic, selection, gate, or interpretation;
- SonotaCo scientific access;
- ASFN or EFN event-level access;
- AMOS scientific access;
- MAARSY or DMS scientific access;
- tuning a threshold, support count, branch-size range, score weight, salt, subset, or tie rule from the result.

## 2. Frozen subsets

Reuse the exact PR #1272 hash rule:

`H(eid) = uint64_be(SHA256('ORBITTRACE_SCALE_STRESS_V1|' + eid)[0:8])`.

Use exactly four nested pairs:

- coarse: denominator `128`, buckets `0,1,2,3` (~5.8k events);
- fine: denominator `1024`, same bucket `0,1,2,3` (~0.7k events).

For each bucket, the denominator-1024 sample is a strict subset of the denominator-128 sample.

No other denominator, bucket, salt, or replicate is authorized.

## 3. Scale-free hierarchy

Construct exact Euclidean single linkage using the already-audited scalable implementation:

- `hdbscan==0.8.43`;
- `min_samples=1` so mutual reachability is ordinary Euclidean distance;
- `min_cluster_size=2` only to expose the complete linkage tree, not as a scientific support threshold;
- `algorithm='boruvka_kdtree'`;
- `approx_min_span_tree=False`;
- `gen_min_span_tree=True`.

PR #1274's follow-up implementation audit proved exact equality to sklearn Euclidean single linkage on all eight frozen subsets: same merge-distance multiset and same 4–63-member branch memberships.

## 4. Parameter-free pruning objective

For every non-root internal branch `C`:

- `m(C)` = number of sample events in the branch;
- `d_form(C)` = branch's own single-link merge distance;
- `d_parent(C)` = distance at which the branch merges into its parent;
- `L(C) = log(d_parent(C) / d_form(C))`.

A branch is output-eligible only if `m(C) >= 4`. The value 4 is inherited from the project's established minimum truth-support definition and affects only output eligibility; it does **not** alter construction of the support-free tree.

Define dimensionless local quality

`Q(C) = [m(C) / n] * L(C)`.

The factor `1/n` is common to every node in a dataset and therefore cannot alter extraction; it is retained only to make reported quality comparable across sample sizes.

Apply ordinary FOSC-style bottom-up extraction with no threshold:

1. For an eligible node, compare `Q(C)` with the sum of the optimal extracted qualities of its two child subtrees.
2. Select the parent if `Q(C) >= child_sum`; otherwise select the children's optimal selections.
3. Ties select the parent for deterministic parsimony.
4. The root is never selected; extraction starts from its children.
5. Leaves and internal nodes with fewer than four members contribute zero own quality but may pass through eligible descendants (none can exist beneath a <4 node).

This exact objective and tie rule are frozen before outcome. No persistence cutoff exists.

## 5. Exact recurrent-EOM comparator

On every one of the same eight subsets, reconstruct exact selected recurrent-EOM HDBSCAN v1 with unchanged:

- GEO6;
- `min_cluster_size=10`;
- `min_samples=10`;
- Euclidean;
- ordinary HDBSCAN condensed hierarchy;
- exact annual-normalized recurrent-EOM kernel and FOSC extraction.

No shower truth is opened.

## 6. Cross-scale identity metric

For each bucket and each method separately:

1. Let `F` be the selected candidate memberships on denominator 1024.
2. Let `C` be selected memberships on denominator 128.
3. Restrict each coarse membership `c in C` to the denominator-1024 event universe and discard restricted sets with fewer than four events.
4. For every fine membership `f in F`, compute its best Jaccard similarity to any retained restricted coarse membership.
5. Record:
   - event-weighted mean best Jaccard: `sum(|f|*J_best(f))/sum(|f|)`;
   - unweighted median best Jaccard;
   - exact restricted-match fraction (`J_best = 1`).

This evaluates whether a cluster selected from the sparse observation corresponds to a cluster selected from the denser observation of the *same underlying event population*.

## 7. Frozen interpretation gate

Let `W_b^SL` and `W_b^REOM` be the event-weighted mean best Jaccard for log-mass FOSC single-link and recurrent-EOM respectively in bucket `b`.

Return

`SUPPORTS_LOGMASS_FOSC_CROSS_SCALE_PRUNING`

iff all of the following hold:

1. log-mass FOSC produces at least one eligible selected branch in all eight subsets;
2. the pooled event-weighted mean best Jaccard across all four nested pairs is strictly greater for log-mass FOSC than recurrent-EOM;
3. the median of the four bucket-level `W_b` values is strictly greater for log-mass FOSC than recurrent-EOM; and
4. log-mass FOSC has strictly greater `W_b` in at least three of four buckets.

Otherwise return

`REFUTES_LOGMASS_FOSC_CROSS_SCALE_PRUNING`.

There is no numerical Jaccard threshold and no post-result rescue.

## 8. Consequences

A positive result authorizes designing one separately frozen scientific successor around the same support-free hierarchy/pruning family. It does not authorize choosing a persistence threshold, changing the minimum output support, changing the FOSC objective, or opening external validation data.

A negative result closes this exact log-mass FOSC pruning architecture for OrbitTrace. No score exponent, mass transform, lifetime transform, tie rule, or threshold variant may be rescued from the result.
