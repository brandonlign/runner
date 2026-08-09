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

## 5. Broad catalogue superiority

`PASS_FINAL_BROAD_CATALOGUE_SUPERIORITY` requires, independently against **each comparator in each test year**:

- pairwise macro F1 >= comparator macro F1 + **0.05**;
- no nonempty shower-size stratum has mean F1 more than **0.05 below** the comparator;
- at least two nonempty size strata per year improve mean F1 by >= **0.10**;
- the number of known showers recovered with F1 > 0.5 is **not lower** than the comparator;
- all integrity and information-parity gates pass.

These are the pre-existing broad-superiority effect bars carried forward from the earlier frozen literature protocol.

## 6. Sparse/weak-stream superiority without overall sacrifice

`PASS_FINAL_SPARSE_STREAM_SUPERIORITY` requires, independently against **each comparator in each test year**:

- 4–9-member shower mean F1 >= comparator + **0.10**;
- combined 4–24-member shower mean F1 >= comparator + **0.10**;
- overall pairwise macro F1 >= comparator - **0.02**;
- the number of known showers with F1 > 0.5 is **not lower** than the comparator;
- no nonempty >=25-member size stratum has mean F1 more than **0.05 below** the comparator;
- all integrity and information-parity gates pass.

The first two effect-size bars are inherited from the earlier preregistered sparse-superiority definition. The tightened macro-F1/shower-count conditions implement the current project requirement that sparse superiority must not be purchased by a meaningful loss of overall catalogue performance.

## 7. Cross-year uncertainty check

A point-estimate pass is necessary but not sufficient. For whichever superiority route is claimed, a deterministic **10,000-replicate stratified bootstrap over known-shower-year evaluation units** must be run separately for Sugar and HDBSCAN, preserving test-year strata.

For broad superiority, the 95% bootstrap lower bound of the pairwise macro-F1 advantage pooled across 2013/2014 must be > 0.

For sparse superiority, the 95% bootstrap lower bounds of both the pairwise 4–9 mean-F1 advantage and combined 4–24 mean-F1 advantage pooled across 2013/2014 must be > 0.

Bootstrap seed, unit construction, missing-stratum behavior, and aggregation formulas must be frozen in the final-candidate test implementation before scientific truth access. Bootstrap results may confirm or reject a point-estimate pass; they may not be used to change the method or gate.

## 8. Final literature verdict

The final matched literature stage returns exactly one of:

- `PASS_FINAL_BROAD_CATALOGUE_SUPERIORITY`;
- `PASS_FINAL_SPARSE_STREAM_SUPERIORITY`;
- `FAIL_FINAL_LITERATURE_SUPERIORITY`;
- `INVALID_FINAL_LITERATURE_TEST_INTEGRITY`.

A pass requires the same route (broad or sparse) against **both Sugar and HDBSCAN across both 2013 and 2014**, plus its uncertainty check. A mixture such as broad-vs-one-comparator and sparse-vs-the-other is diagnostic only and does not pass the final gate.

## 9. Consequence

Only a final literature PASS may activate the permanent MAARSY 2020/2021 no-retuning external validation.

A final literature failure is final for that frozen candidate on this panel. The candidate may not be tuned to the result and re-tested on SonotaCo 2013/2014 as if fresh, and no replacement SonotaCo year may be opened because the result was unfavorable.

OrbitTrace remains sealed regardless of any diagnostic improvement until both the final literature requirement and external-generalization requirement are satisfied.
