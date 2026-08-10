# OrbitTrace final literature evaluator freeze — v1

## Status

This file resolves the remaining evaluator choices left open by `FINAL_LITERATURE_TEST_POLICY_V1.md` before any SonotaCo 2013/2014 scientific archive value, known-shower truth, comparator output, or final-candidate output is opened.

It changes no candidate, comparator, superiority threshold, row-universe rule, or dataset assignment.

## 1. Point-estimate one-to-one assignment

For each comparator × year pair independently:

1. candidate budget `B` is fixed from the comparator output exactly as specified by `FINAL_LITERATURE_TEST_POLICY_V1.md`;
2. the comparator uses its `B` frozen primary families;
3. OrbitTrace uses its first `B` frozen primary ranked families having at least one member in that year, or all available families if fewer than `B` exist;
4. known-shower truth on the already-frozen common-row manifest is opened only after both outputs are frozen;
5. event-membership F1 for candidate family `c` and known shower `s` is computed exactly as the rational number `2*TP/(|c|+|s|)` on that pairwise common-row universe;
6. a maximum-total-F1 one-to-one assignment is solved exactly with rational arithmetic. Known showers are sorted by stable canonical truth label. Candidate families are sorted by frozen catalogue rank, then stable family ID. Unmatched known showers are represented by distinct zero-weight dummy columns placed after all real candidates;
7. the frozen exact-rational Hungarian implementation in `orbittrace_final_literature_evaluator_v1.py` is authoritative. Its deterministic first-column tie behavior on the stable ordering is the tie-break. No floating perturbation, random tie-break, manual remapping, or post-result alternate assignment is allowed.

Every known shower therefore has exactly one scored outcome: its assigned real family's precision/recall/F1, or zero if assigned a dummy. A real candidate can be used at most once.

## 2. Size strata

Known-shower size is the number of truth-member events surviving the exact comparator/year pairwise common-row manifest. The frozen strata are:

- `4-9`: 4 through 9 members inclusive;
- `10-24`: 10 through 24;
- `25-49`: 25 through 49;
- `50-99`: 50 through 99;
- `100+`: at least 100.

Showers with fewer than four surviving members are not eligible evaluation showers and cannot enter any macro, stratum, recovered-count, or bootstrap denominator. The combined `4-24` set is exactly the union of `4-9` and `10-24`.

A required point-estimate stratum that is empty is treated as not applicable only where the parent policy explicitly says `nonempty`. For the sparse-superiority route, `4-9` and `4-24` must each be nonempty in both 2013 and 2014 for the route to be eligible; otherwise sparse superiority cannot pass for that comparator.

## 3. Recovered-shower count

The `F1 > 0.5` recovered-shower count is computed only from the frozen one-to-one assignment. The inequality is strict. An F1 exactly equal to 0.5 is not counted.

## 4. Bootstrap unit and pairing

The uncertainty check is a paired bootstrap over **known-shower-year evaluation units**, after the point-estimate one-to-one assignment has been frozen.

For one comparator, each unit contains:

- year;
- canonical known-shower label;
- truth size and frozen size stratum;
- OrbitTrace assigned precision/recall/F1;
- comparator assigned precision/recall/F1;
- their paired F1 difference.

The point-estimate one-to-one assignments and candidate budgets are **held fixed** through all bootstrap replicates. They are not recomputed after resampling. This makes the bootstrap estimate uncertainty in the observed per-shower performance differences rather than granting either method new assignment opportunities in synthetic resamples.

## 5. Stratified resampling

Bootstrap seed: integer **2026081001** using NumPy `Generator(PCG64)`.

Replicates: exactly **10,000**.

Strata are the Cartesian groups actually present among eligible units:

`year × {4-9, 10-24, 25-49, 50-99, 100+}`.

Within every nonempty stratum containing `n` units, each replicate samples exactly `n` units with replacement from that same stratum. The sampled strata are then concatenated. This preserves both year and truth-size composition exactly in replicate sample counts.

No empty stratum is synthesized, borrowed from another year, pooled to create support, or assigned pseudo-observations.

## 6. Bootstrap estimands

For each replicate, compute from the paired sampled units:

- `macro_advantage`: ordinary mean of `OrbitTrace F1 - comparator F1` over all sampled eligible units;
- `sparse_4_9_advantage`: mean paired F1 difference over sampled units whose frozen stratum is `4-9`;
- `sparse_4_24_advantage`: mean paired F1 difference over sampled units whose frozen stratum is `4-9` or `10-24`.

The pooled 2013/2014 estimand is therefore a shower-year macro quantity with the observed year×size-stratum sample counts preserved in every replicate. It does not average year-level means with equal year weights unless the two years happen to contain equal numbers of eligible units.

## 7. Confidence bound

The one-sided quantity used by the parent policy is the **2.5th percentile** of the 10,000 bootstrap replicate advantages, computed with NumPy quantile method `linear`. This is the lower endpoint of the ordinary two-sided 95% percentile interval.

A required lower bound passes only when it is strictly greater than zero.

- Broad route: lower bound of `macro_advantage` > 0.
- Sparse route: lower bounds of both `sparse_4_9_advantage` and `sparse_4_24_advantage` > 0.

No alternative confidence interval, seed, replicate count, quantile interpolation rule, unit definition, reweighting, or assignment recomputation may be substituted after truth access.

## 8. Comparator independence

Sugar and HDBSCAN are evaluated and bootstrapped separately on their own exact pairwise common-row universes. No bootstrap unit, denominator, candidate budget, assignment, or confidence bound is mixed across comparators.

The same superiority route must still pass against both comparators in both years as required by the parent policy.

## 9. Integrity

The executable evaluator must preserve hashes of:

- pairwise common-row manifest;
- frozen candidate output;
- frozen comparator output;
- truth manifest opened only after those outputs;
- point-assignment record;
- bootstrap unit table;
- 10,000-replicate advantage arrays;
- final verdict record.

The evaluator itself receives no OrbitTrace target information and contains no target-specific constant. Solar longitude 20°–55° remains excluded upstream before all candidate/comparator/truth construction.

## 10. Claim boundary

This freeze is evaluation infrastructure, not scientific evidence and not authorization to open SonotaCo 2013/2014. The final candidate-specific runner still must be frozen and declared `FINAL_FOR_LITERATURE_TEST` before final-test scientific access.
