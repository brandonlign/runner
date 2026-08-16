# OrbitTrace theory-scaled robust single linkage structural diagnostic v1

## Status

**FROZEN BEFORE IMPLEMENTATION AND BEFORE ANY DIAGNOSTIC OUTCOME.**

This is a zero-label structural viability diagnostic only. It is not a scientific successor, does not evaluate known showers, and cannot promote a final clustering method.

It follows the exact findings of PRs #1272–#1275:

- fixed HDBSCAN `10/10` becomes recurrence-inert under small-survey sample sizes;
- both fixed core smoothing and fixed branch condensation contribute to that collapse;
- support-free Euclidean single-link branch lifetime `log(d_parent/d_form)` is much less sample-size-sensitive than raw linkage scale;
- ordinary single-link plus threshold-free additive FOSC pruning fails because chaining can make near-root giant branches dominate.

The present question is therefore upstream of pruning: **does a theory-scaled robust-single-link hierarchy reduce ordinary-single-link chaining while retaining a dimensionless branch-lifetime coordinate that remains more scale-stable than its raw merge scale?**

## 1. Firewall and data

Use only target-excluded GMN 2022+2023 geometry under exact GEO6. Inclusive solar longitude `[20.0,55.0]` is removed before geometry.

Forbidden:

- OrbitTrace target information or target-region events;
- shower labels/truth in any statistic, gate, or interpretation;
- SonotaCo scientific access;
- ASFN or EFN event-level access;
- AMOS scientific access;
- MAARSY or DMS scientific access;
- selecting any parameter, threshold, subset, salt, metric, or gate from the outcome.

## 2. Frozen subsets

Reuse the exact PR #1272 hash rule:

`H(eid) = uint64_be(SHA256('ORBITTRACE_SCALE_STRESS_V1|' + eid)[0:8])`.

Use exactly eight subsets:

- denominator `128`, buckets `0,1,2,3` (~5.8k events);
- denominator `1024`, buckets `0,1,2,3` (~0.7k events).

No other denominators, buckets, salts, or replicates are authorized.

## 3. Ordinary single-link comparator

Construct exact Euclidean single linkage using the already-audited scalable implementation:

- `hdbscan==0.8.43`;
- `HDBSCAN(min_samples=1, min_cluster_size=2)` only to expose the complete Euclidean single-link tree;
- Euclidean metric;
- `algorithm='boruvka_kdtree'`;
- `approx_min_span_tree=False`;
- `gen_min_span_tree=True`.

PR #1274's follow-up equivalence audit proved this tree is exactly equal to sklearn Euclidean single linkage on all eight frozen subsets.

## 4. Theory-scaled robust single linkage

Use the public `hdbscan.robust_single_linkage` implementation of Chaudhuri–Dasgupta robust single linkage only to obtain its hierarchy. Flat labels are ignored.

For a subset with `n` events and GEO6 dimension `d=6`, freeze:

- `k(n) = ceil(d * ln(n))`;
- `alpha = sqrt(2)`;
- Euclidean metric;
- `algorithm='boruvka_kdtree'`;
- `core_dist_n_jobs=1`;
- `cut=0.0` and `gamma=1` solely because the public function requires flat-clustering arguments; neither enters the returned hierarchy comparison.

The sample-size dependence is frozen from the theoretical rate family before outcome. The unit multiplicative constant in `ceil(d ln n)` is a diagnostic anchor only and cannot be altered or tuned from this result. A negative result closes this exact anchor.

## 5. Chaining metrics

For each binary linkage tree reconstruct every internal-node size from its two children.

### 5.1 Root largest-child fraction

For the root's two children define

`R = max(size_left, size_right) / n`.

A chain-like hierarchy tends toward `R -> 1`. Lower is structurally less dominated by one giant branch plus a tiny attachment.

### 5.2 Mass-weighted internal split imbalance

For every non-root internal node `C` with `size(C) >= 4`, let child sizes be `a,b` and define local imbalance

`I(C) = |a-b|/(a+b)`.

Define the mass-weighted tree imbalance

`I_mass = sum_C (a+b)*I(C) / sum_C (a+b) = sum_C |a-b| / sum_C (a+b)`.

The minimum size 4 is inherited from the project's established minimum evaluable shower support and is used only to avoid letting two- and three-point mechanical merges dominate this structural summary. It does not alter either hierarchy.

Lower `I_mass` means less chain-like splitting at scientifically relevant support.

## 6. Robust-tree branch-lifetime scale test

For every non-root robust-single-link internal node in the four inherited dyadic branch-size bins:

- 4–7;
- 8–15;
- 16–31;
- 32–63;

compute:

- formation distance `d_form`;
- parent merge distance `d_parent`;
- dimensionless lifetime `L = log(d_parent/d_form)`;
- raw negative-control coordinate `log(d_form)`.

Pool the four denominator-128 buckets and four denominator-1024 buckets within each size bin. A bin is supported iff both pooled scales contain at least 30 branches, inherited exactly from PR #1274.

For each supported bin compare denominator 128 vs 1024 using:

- two-sample KS statistic;
- absolute median shift;
- absolute p90 shift.

The robust lifetime coordinate wins a bin iff all three are strictly smaller for `L` than for raw `log(d_form)`.

## 7. Frozen interpretation gate

Return

`SUPPORTS_THEORY_RSL_CHAIN_AND_SCALE_HYPOTHESIS`

iff all of the following hold:

1. robust single linkage has strictly lower root largest-child fraction than ordinary single linkage in at least 7 of 8 frozen subsets;
2. the median robust root largest-child fraction is strictly lower than the median ordinary value;
3. robust single linkage has strictly lower mass-weighted internal split imbalance than ordinary single linkage in at least 7 of 8 subsets;
4. the median robust mass-weighted split imbalance is strictly lower than the median ordinary value;
5. at least 3 of the 4 branch-size bins are supported; and
6. every supported bin is a strict robust-lifetime scale-normalization win under all three inherited PR #1274 comparisons.

The 7/8 paired-win requirement is frozen because under an exchangeable 50/50 sign null it is the smallest nontrivial count with one-sided exact sign probability below 0.05 (`P[X>=7 | n=8,p=.5]=0.03515625`).

Otherwise return

`REFUTES_THEORY_RSL_CHAIN_AND_SCALE_HYPOTHESIS`.

No mixed interpretation and no post-result rescue are authorized.

## 8. Consequence

A positive result only establishes structural viability of this theory-scaled robust hierarchy. It would authorize one separately frozen follow-up that designs statistically justified branch selection/pruning without shower truth first.

A negative result closes this exact `k(n)=ceil(6 ln n), alpha=sqrt(2)` robust-single-link structural anchor. It cannot be rescued by changing the constant, log base, alpha, k schedule, branch-size bins, or structural gates after seeing the result.
