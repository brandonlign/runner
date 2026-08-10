# OrbitTrace current methodology state

## Authoritative scientific status

### Final GMN-developed catalogue method: M0 / #839

GMN 2022/2023 methodology selection is closed under the preregistered #848/#861 decision chain.

The final GMN-developed method is **M0 / PR #839 URC union ranking**:

- candidate universe: 4,504 families = 226 hard-v8 + 1,075 P19-soft + 3,203 P20-soft;
- ranking: strict same-shower grouped ExtraTrees quality regression plus diversity;
- fixed ranker parameters: depth 4, min leaf 5, diversity lambda 0.8, scale 1.0;
- selected order SHA-256: `ffc97f7bc4fbc8f13170ffe8a71260e1596190e39e9324c24e8ba7719f427449`;
- recovery@25/50/100/500 = 22/40/75/159;
- qualified known streams = 256;
- top-100 dominant precision = 0.7645689180574315;
- best-membership macro F1 = 0.17953659309876194.

The immutable catalogue proposal/rank architecture is #839 with the original frozen M0 memberships. No new GMN candidate generator, ranker, membership rule, threshold family, or score combination may be introduced from these final development outcomes.

## Final membership adjudication

M1/#845 is a permanent scientific no-go.

Corrected admissible #846 M2 produced a real initial membership improvement with selected policy `ET_d4_l10`, threshold 0.4, cap Infinity; OOF membership macro F1 0.352413; 95 qualified streams; r100 60; and 36/280 preregistered variants passing.

However the already-frozen #850 five-salt repeated same-shower-group stress, run `31346362800`, returned **`FAIL_EVENT_LEVEL_P12_FIXED_GROUP_STRESS`**. Panels A-D passed, but panel E retained only **94 qualified streams**, below the immutable floor of 95. Its macro F1 remained 0.349308 and annual all-shower gains stayed positive, but the qualification failure is decisive.

Under #848/#850/#861:

- M2 is a permanent no-go for promotion;
- no threshold/model/cap rescue or reselection is allowed;
- #852 full-URC integration is not authorized;
- M0/#839 is the final GMN-developed method.

## Deployment / transport state

### Ranker transport

PR #860 passed exact GMN equivalence for the year-portable #839 ranker adapter:

- exact 4,504 x 34 feature matrix reproduced;
- feature SHA-256 `5d215c5562c0ccce967d81ff0a087ca83b1afda95a269888d2219ef669d198d1`;
- portable features match the original frozen #839 feature construction cell-for-cell on identical GMN input;
- serialized model and final diversity ordering are preserved;
- no truth labels are required at application time.

This is implementation equivalence, not additional scientific evidence.

### Proposal-generator transport

PR #862 is the active transport-only proof for exact pair-portable hard-v8/P19/P20 generation. Its first equivalence execution reproduced hard-v8 exactly but failed at P19-soft structural equality. The failure was traced to an execution-context mismatch: the verifier replaced the frozen layer-specific `support.CORPUS` while original P19/P20 executions set their own contexts before catalogue parsing/generation.

The adapter has been corrected to preserve P19/P20 frozen support contexts and explicitly rebind the shared v6 year globals. A new exact-GMN structural-equivalence run is in progress. No scientific rule changed.

Until exact generator equivalence passes, #839 is not yet declared deployable on SonotaCo 2013/2014.

## Permanent data roles

Dataset roles are fixed:

- **Development/train:** GMN 2022 + 2023.
- **Single final matched literature test:** SonotaCo 2013 + 2014.
- **Single scored no-retuning external validation endpoint:** MAARSY 2022.
- **Fixed unlabeled external recurrence support:** MAARSY 2021 only, used solely as the immediately preceding annual scan required by #839's exact two-year recurrence mechanism; no 2021 truth/performance may ever be opened.
- **Diagnostic/history only:** scientifically consumed historical panels such as SonotaCo 2023/2025.

The MAARSY 2021 support scan is method input, **not** a second validation endpoint. The external scientific claim is scored only on MAARSY 2022.

No SonotaCo 2013/2014 or MAARSY event-level scientific value has been opened for the final method.

## Final literature gate

`FINAL_LITERATURE_TEST_POLICY_V1.md` and the frozen #820/#854 comparator/evaluator machinery govern the one-shot SonotaCo 2013/2014 test.

The frozen candidate is compared independently against **Sugar** and **catalogue HDBSCAN** on pairwise exact-row universes with detector-input information parity, candidate-budget parity, one-to-one maximum-total-F1 assignment, fixed size strata, and the preregistered 10,000-replicate stratified bootstrap.

The final literature stage must produce either `PASS_FINAL_BROAD_CATALOGUE_SUPERIORITY` or `PASS_FINAL_SPARSE_STREAM_SUPERIORITY` against both comparators across both 2013 and 2014 under the same route.

**#839 has not yet been scientifically tested against Sugar or catalogue HDBSCAN.**

## External-validation compatibility resolution

The schema/source-only preflight established two facts without opening MAARSY event values:

1. MAARSY provides the trajectory/geocentric-velocity/orbit observable class required for meteor-stream work and publicly documents multi-year coverage including 2021 and 2022.
2. #839 cannot run on a literal single 2022 scan because its hard/P19/P20 proposal architecture requires two distinct annual scans.

The pre-result candidate-specific transport therefore freezes the ordered pair **(MAARSY 2021 unlabeled support, MAARSY 2022 scored)**. This preserves #839's exact annual-recurrence mechanism without creating pseudo-years or changing the scored validation endpoint.

Rules:

- 2021 may supply only raw label-free recurrence input;
- no 2021 known-shower truth, mapping, performance metric, selection statistic, or success criterion may ever be opened/computed;
- detector outputs are frozen before 2022 truth opens;
- only 2022 members/truth are scored;
- no alternate support/scored year is allowed after any result.

Preaccess structural verdict: `MAARSY_2022_WITH_FIXED_2021_UNLABELED_SUPPORT_PREFLIGHT = STRUCTURALLY_COMPATIBLE`.

This is not an external scientific PASS. The exact MAARSY adapter, 2022 truth mapping, objective power floor, metrics, uncertainty rules, and PASS/FAIL gates still must be frozen before SonotaCo scientific access.

## Final blind OrbitTrace gate

OrbitTrace remains inaccessible. `FINAL_BLIND_SEARCH_POLICY_V1.md` permits target-containing execution only after both final literature superiority and `PASS_FINAL_MAARSY_2022_NO_RETUNING_GENERALIZATION`.

Stage A freezes the complete target-free ranking. Stage B may receive only withheld stable event-ID sets and perform exact set intersection. An eligible recovery requires >=4 exact withheld IDs in each year and >=8 total.

Only primary rank <=25 counts as `PASS_FINAL_BLIND_ORBITTRACE_DISCOVERY`. Rank 26-100 is partial only and cannot authorize target-informed retuning.

## Current authorization state

- GMN methodology selection: **closed; M0/#839 selected**.
- Literature superiority: **not established**.
- SonotaCo 2013/2014 scientific access: **not authorized**.
- MAARSY event-level scientific access: **not authorized**.
- OrbitTrace target access: **not authorized**.
- Solar longitude 20°–55° and all OrbitTrace target information remain sealed.

## Next required work

1. Complete exact #862 GMN generator-transport equivalence.
2. Freeze one deployable #839 application package if all transport identities pass.
3. Freeze the exact MAARSY `(2021 unlabeled support, 2022 scored)` adapter, 2022 truth mapping, power floor, metrics, uncertainty rules, and PASS/FAIL gate without event-level access.
4. Only then may the one-shot SonotaCo 2013/2014 Sugar/HDBSCAN literature test be opened.
