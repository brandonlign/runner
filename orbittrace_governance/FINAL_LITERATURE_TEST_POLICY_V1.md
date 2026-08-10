# OrbitTrace final matched literature-test policy — v1

## Scope

This policy governs the single permanent **SonotaCo 2013 + 2014** literature test defined by `FIXED_DATA_SPLIT_V1.md`. It is frozen before any SonotaCo 2013/2014 scientific archive value, known-shower truth value, comparator cluster result, or OrbitTrace candidate score is opened.

It carries forward the strongest pre-result matched-comparison logic already established in the repository and requires sparse-stream advantage without meaningful sacrifice on ordinary streams.

## 1. Exact comparator boundary

The required catalogue comparators are:

1. **Sugar**, using the faithful frozen catalogue implementation appropriate to the exact SonotaCo row universe;
2. **catalogue HDBSCAN**, using the faithful frozen catalogue implementation appropriate to the exact SonotaCo row universe.

Sugar and HDBSCAN may have different structurally eligible row universes. Denominators remain **pairwise**: OrbitTrace-vs-Sugar is evaluated only on their common exact-row universe, and OrbitTrace-vs-HDBSCAN only on their common exact-row universe. Cross-comparator denominator mixing is forbidden.

No comparator threshold, clustering hyperparameter, row filter, mapping rule, or postprocessing choice may be changed after SonotaCo 2013/2014 scientific access.

## 2. Information parity

A final superiority claim requires detector-input information parity.

Before scientific test access, the final candidate and each comparator receive the same underlying eligible meteor rows and the same raw observable fields available on that pairwise universe. OrbitTrace may not receive known-shower labels, native shower/background designations, target identity, catalogue mapping truth, or equivalent supervision withheld from the comparator.

Known-shower truth is opened only after all candidate/comparator outputs for the pairwise universe are frozen.

## 3. Single primary catalogue output

The final candidate emits exactly **one primary catalogue output** before known-shower truth is opened. That output freezes, for every reported family:

- family identifier;
- final event/member-ID set;
- final catalogue rank/order;
- any deterministic family suppression, merging, or deduplication already applied by the method.

All literature-test precision, recall, F1, size-stratum, recovered-shower, and uncertainty calculations use those same frozen final member sets. No result-dependent core/halo switch, member-set substitution, family filtering, or alternative ranking is permitted.

The same principle applies to comparators: each comparator's frozen primary catalogue output is what is scored.

## 4. Integrity gates

Every final-test result must satisfy all of:

- exact frozen final-candidate source/configuration reproduced;
- exact frozen Sugar source/configuration reproduced;
- exact frozen catalogue-HDBSCAN source/configuration reproduced;
- SonotaCo 2013 and 2014 both evaluated;
- solar longitude 20°–55° removed before target-sensitive processing or truth access;
- output candidates/families/members/ranks frozen before known-shower truth is opened;
- the primary catalogue output is the sole OrbitTrace output used for superiority scoring;
- pairwise exact-row manifests/hashes preserved;
- no target information present in source, inputs, parameters, logs, or evaluation logic;
- no post-result thresholding, family filtering, remapping, or manual adjudication.

An integrity failure produces no scientific superiority verdict.

## 5. Catalogue-burden parity and one-to-one scoring

For each **comparator × test-year** pair, define comparator candidate budget `B` before known-shower truth is opened as the number of frozen primary comparator families with at least one member in that test year on the exact pairwise row universe.

The superiority calculation then uses:

- **Comparator:** all `B` frozen primary families for that year;
- **OrbitTrace:** the first `B` frozen primary OrbitTrace families in catalogue rank order with at least one member in that year. If OrbitTrace emits fewer than `B`, all available are used and no padding is permitted.

Within each budget-matched output, known showers and candidate families are scored by **maximum-total-F1 one-to-one bipartite assignment** for that test year:

- edge weight is ordinary event-membership F1;
- each candidate family matches at most one known shower;
- each known shower matches at most one candidate family;
- unmatched known showers receive F1/precision/recall = 0 for macro/stratum calculations;
- unmatched candidate families remain false catalogue outputs;
- equal-total-weight ties use a deterministic rule frozen before truth access.

All point metrics and bootstrap quantities use these budget-matched one-to-one scores. For each comparator/year, the number of one-to-one matched showers with F1 > 0.5 must be no lower than the comparator.

## 6. Broad catalogue superiority

`PASS_FINAL_BROAD_CATALOGUE_SUPERIORITY` requires independently against **each comparator in each test year**:

- budget-matched one-to-one macro F1 >= comparator + **0.05**;
- no nonempty shower-size stratum has mean F1 more than **0.05 below** comparator;
- at least two nonempty size strata per year improve mean F1 by >= **0.10**;
- F1 > 0.5 recovered-shower count is not lower than comparator;
- all integrity, information-parity, and catalogue-burden gates pass.

## 7. Sparse/weak-stream superiority without overall sacrifice

`PASS_FINAL_SPARSE_STREAM_SUPERIORITY` requires independently against **each comparator in each test year**:

- 4–9-member mean F1 >= comparator + **0.10**;
- combined 4–24-member mean F1 >= comparator + **0.10**;
- overall pairwise macro F1 >= comparator - **0.02**;
- F1 > 0.5 recovered-shower count is not lower than comparator;
- no nonempty >=25-member size stratum has mean F1 more than **0.05 below** comparator;
- all integrity, information-parity, and catalogue-burden gates pass.

## 8. Cross-year uncertainty check

A point-estimate pass is necessary but not sufficient. For whichever superiority route is claimed, a deterministic **10,000-replicate stratified bootstrap over known-shower-year evaluation units** runs separately for Sugar and HDBSCAN, preserving test-year strata and Section 5 semantics.

For broad superiority, the 95% bootstrap lower bound of pooled 2013/2014 pairwise macro-F1 advantage must be > 0.

For sparse superiority, the 95% bootstrap lower bounds of both pooled 4–9 mean-F1 advantage and combined 4–24 mean-F1 advantage must be > 0.

Seed, unit construction, missing-stratum behavior, aggregation formulas, and one-to-one-assignment resampling behavior must be frozen before scientific truth access.

## 9. Final literature verdict

The final matched literature stage returns exactly one of:

- `PASS_FINAL_BROAD_CATALOGUE_SUPERIORITY`;
- `PASS_FINAL_SPARSE_STREAM_SUPERIORITY`;
- `FAIL_FINAL_LITERATURE_SUPERIORITY`;
- `INVALID_FINAL_LITERATURE_TEST_INTEGRITY`.

A pass requires the same route against **both Sugar and HDBSCAN across both 2013 and 2014**, plus its uncertainty check. A mixed route is diagnostic only and does not pass.

## 10. Consequence

Only a final literature PASS may activate the permanent **MAARSY 2022 scored no-retuning external validation**, using **MAARSY 2021 only as the already-frozen unlabeled annual-recurrence support scan** required by #839.

A final literature failure is final for that frozen candidate on SonotaCo 2013/2014. The candidate may not be tuned to the result and re-tested as fresh, and no replacement SonotaCo year may be opened because the result was unfavorable.

OrbitTrace remains sealed until both final literature superiority and scored MAARSY 2022 external generalization are satisfied.
