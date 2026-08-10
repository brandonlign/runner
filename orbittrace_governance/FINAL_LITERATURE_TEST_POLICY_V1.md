# OrbitTrace final matched literature-test policy — v1

## Scope

This policy governs the single permanent **SonotaCo 2013 + 2014** literature test defined by `FIXED_DATA_SPLIT_V1.md`. It is frozen before any SonotaCo 2013/2014 scientific archive value, known-shower truth value, comparator cluster result, or OrbitTrace candidate score is opened.

It carries forward the strongest pre-result matched-comparison logic already established in the repository and tightens the overall-nonregression requirement to match the project goal: a sparse-stream advantage is not enough if ordinary-stream performance is materially sacrificed.

## 1. Exact comparator boundary

The required catalogue comparators are:

1. **Sugar**, using the faithful frozen catalogue implementation appropriate to the exact SonotaCo row universe;
2. **catalogue HDBSCAN**, using the faithful frozen catalogue implementation appropriate to the exact SonotaCo row universe.

Sugar and HDBSCAN may have different structurally eligible row universes. Denominators must therefore remain **pairwise**: OrbitTrace-vs-Sugar is evaluated only on their common exact-row universe, and OrbitTrace-vs-HDBSCAN only on their common exact-row universe. Cross-comparator denominator mixing is forbidden.

No comparator threshold, clustering hyperparameter, row filter, mapping rule, or postprocessing choice may be changed after SonotaCo 2013/2014 scientific access.

## 2. Information parity

A final superiority claim requires detector-input information parity.

Before scientific test access, the final candidate and each comparator receive the same underlying eligible meteor rows and the same raw observable fields available on that pairwise universe. Algorithms may of course use different transformations of those observables, but OrbitTrace may not receive known-shower labels, native shower/background designations, target identity, catalogue mapping truth, or any equivalent one-bit supervision that is withheld from the comparator.

Known-shower truth is opened only after all candidate/comparator outputs for the pairwise universe are frozen.

A method that requires privileged survey-native truth information may still be scientifically described as an operational pipeline, but it is **ineligible for the final same-information literature-superiority claim** and therefore cannot unlock the OrbitTrace target under this project goal.

## 3. Single primary catalogue output

The final candidate must emit exactly **one primary catalogue output** before known-shower truth is opened. That output freezes, for every reported family:

- the family identifier;
- the final event/member-ID set used to represent that family;
- the final catalogue rank/order;
- any deterministic family suppression, merging, or deduplication already applied by the method.

All final literature-test precision, recall, F1, size-stratum, recovered-shower, and uncertainty calculations for OrbitTrace must use those **same frozen final member sets**. The benchmark may not score a smaller discovery core while treating a larger halo as the method's real membership output, nor score a halo for characterization while reverting to a core for superiority.

An architecture may internally use seeds, cores, envelopes, halos, or multiple representations. If so, it must freeze a deterministic, label-free rule that produces the one primary member set per output family before truth access. Secondary representations may be reported only as diagnostics and cannot replace the primary member set in the superiority calculation after results are visible.

No result-dependent core/halo switch, member-set substitution, family filtering, or alternative ranking is permitted. This rule explicitly supersedes historical P13/P18-style dual-output evaluation semantics for the final test; those historical results remain unchanged and are not retroactively reinterpreted.

The same principle applies to comparators: each comparator's frozen primary catalogue output is what is scored.

## 4. Integrity gates

Every final-test result must satisfy all of the following before performance is interpreted:

- exact frozen final-candidate source and configuration reproduced;
- exact frozen Sugar source/configuration reproduced;
- exact frozen catalogue-HDBSCAN source/configuration reproduced;
- SonotaCo 2013 and 2014 are both evaluated;
- solar longitude 20°–55° is removed before any target-sensitive processing or truth access;
- output candidates/families/members/ranks are frozen before known-shower truth is opened;
- the primary catalogue output satisfies Section 3 and is the sole OrbitTrace output used for superiority scoring;
- pairwise exact-row manifests and hashes are preserved;
- no target information is present in source, inputs, parameters, logs, or evaluation logic;
- no post-result thresholding, family filtering, remapping, or manual adjudication is allowed.

An integrity failure produces no scientific superiority verdict.

## 5. Catalogue-burden parity and one-to-one scoring

A method may not obtain a superiority claim merely by emitting many more candidate fragments than a comparator and thereby receiving more chances to overlap a known shower.

For each **comparator × test-year** pair, define the comparator candidate budget `B` before known-shower truth is opened as the number of frozen primary comparator families having at least one member in that test year on the exact pairwise row universe.

The superiority calculation for that comparator/year then uses:

- **Comparator:** all of its `B` frozen primary families for that year;
- **OrbitTrace:** the first `B` frozen primary OrbitTrace families in catalogue rank order that have at least one member in that year. If OrbitTrace emits fewer than `B`, all available OrbitTrace families are used and no padding is permitted.

Thus candidate-budget parity is determined entirely by pre-truth outputs and cannot be tuned to the result. The full untruncated catalogues must still be preserved and may be reported diagnostically, but full-catalogue performance cannot substitute for the budget-matched superiority calculation.

Within each budget-matched output, known showers and candidate families are scored by a **maximum-total-F1 one-to-one bipartite assignment** for that test year:

- edge weight is the ordinary event-membership F1 between one frozen candidate family and one known shower on the exact pairwise row universe;
- each candidate family may match at most one known shower;
- each known shower may match at most one candidate family;
- unmatched known showers receive F1 = 0, precision = 0, and recall = 0 for macro/stratum calculations;
- unmatched candidate families remain false catalogue outputs and may not be reassigned manually;
- deterministic tie-breaking for equal-total-weight assignments must be frozen before truth access.

This one-to-one rule prevents a single broad cluster from counting as multiple recovered showers and prevents a cloud of fragments around one shower from yielding multiple scientific recoveries.

All Section 6/7 point metrics and Section 8 bootstrap quantities use these **budget-matched, one-to-one** scores. In addition, for each comparator/year the number of one-to-one matched showers with F1 > 0.5 must be no lower than the comparator. Because the candidate budgets are equal, this also enforces non-inferior high-confidence catalogue yield per reported family.

## 6. Broad catalogue superiority

`PASS_FINAL_BROAD_CATALOGUE_SUPERIORITY` requires, independently against **each comparator in each test year**:

- budget-matched one-to-one macro F1 >= comparator macro F1 + **0.05**;
- no nonempty shower-size stratum has mean F1 more than **0.05 below** the comparator;
- at least two nonempty size strata per year improve mean F1 by >= **0.10**;
- the number of one-to-one matched known showers recovered with F1 > 0.5 is **not lower** than the comparator;
- all integrity, information-parity, and catalogue-burden gates pass.

These are the pre-existing broad-superiority effect bars carried forward from the earlier frozen literature protocol, now evaluated under the stricter catalogue-burden rules in Section 5.

## 7. Sparse/weak-stream superiority without overall sacrifice

`PASS_FINAL_SPARSE_STREAM_SUPERIORITY` requires, independently against **each comparator in each test year**:

- budget-matched one-to-one 4–9-member shower mean F1 >= comparator + **0.10**;
- budget-matched one-to-one combined 4–24-member shower mean F1 >= comparator + **0.10**;
- budget-matched one-to-one overall pairwise macro F1 >= comparator - **0.02**;
- the number of one-to-one matched known showers with F1 > 0.5 is **not lower** than the comparator;
- no nonempty >=25-member size stratum has mean F1 more than **0.05 below** the comparator;
- all integrity, information-parity, and catalogue-burden gates pass.

The first two effect-size bars are inherited from the earlier preregistered sparse-superiority definition. The tightened macro-F1/shower-count conditions implement the current project requirement that sparse superiority must not be purchased by a meaningful loss of overall catalogue performance.

## 8. Cross-year uncertainty check

A point-estimate pass is necessary but not sufficient. For whichever superiority route is claimed, a deterministic **10,000-replicate stratified bootstrap over known-shower-year evaluation units** must be run separately for Sugar and HDBSCAN, preserving test-year strata and the Section 5 budget-matched one-to-one semantics.

For broad superiority, the 95% bootstrap lower bound of the pairwise macro-F1 advantage pooled across 2013/2014 must be > 0.

For sparse superiority, the 95% bootstrap lower bounds of both the pairwise 4–9 mean-F1 advantage and combined 4–24 mean-F1 advantage pooled across 2013/2014 must be > 0.

Bootstrap seed, unit construction, missing-stratum behavior, aggregation formulas, and whether the one-to-one assignment is held fixed or recomputed within each resample must be frozen in the final-candidate test implementation before scientific truth access. Bootstrap results may confirm or reject a point-estimate pass; they may not be used to change the method or gate.

## 9. Final literature verdict

The final matched literature stage returns exactly one of:

- `PASS_FINAL_BROAD_CATALOGUE_SUPERIORITY`;
- `PASS_FINAL_SPARSE_STREAM_SUPERIORITY`;
- `FAIL_FINAL_LITERATURE_SUPERIORITY`;
- `INVALID_FINAL_LITERATURE_TEST_INTEGRITY`.

A pass requires the same route (broad or sparse) against **both Sugar and HDBSCAN across both 2013 and 2014**, plus its uncertainty check. A mixture such as broad-vs-one-comparator and sparse-vs-the-other is diagnostic only and does not pass the final gate.

## 10. Consequence

Only a final literature PASS may activate the permanent **MAARSY 2022** scored no-retuning external validation. The frozen #839 transport may use **MAARSY 2021 only as the predeclared unlabeled annual-recurrence support scan**; no 2021 truth or performance endpoint is permitted.

A final literature failure is final for that frozen candidate on this panel. The candidate may not be tuned to the result and re-tested on SonotaCo 2013/2014 as if fresh, and no replacement SonotaCo year may be opened because the result was unfavorable.

OrbitTrace remains sealed regardless of any diagnostic improvement until both the final literature requirement and external-generalization requirement are satisfied.
