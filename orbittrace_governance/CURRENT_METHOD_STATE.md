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

The immutable catalogue proposal/rank architecture is therefore #839 with the original frozen M0 memberships. No new GMN candidate generator, ranker, membership rule, threshold family, or score combination may be introduced from these final development outcomes.

## Final membership adjudication

### M1

M1/#845 is a permanent scientific no-go.

### M2

Corrected admissible #846 (source `e5733a57488b7b8dff26c15ff76f679810efac9c`, run `31344902186`) produced a genuine membership improvement and passed its initial strict-group feasibility gate:

- selected frozen policy: `ET_d4_l10`, threshold 0.4, cap Infinity;
- OOF membership macro F1 = 0.352413;
- qualified streams = 95;
- recovery@100 = 60;
- 36/280 preregistered variants passed.

However the required already-frozen #850 five-salt repeated same-shower-group stress, run `31346362800`, returned **`FAIL_EVENT_LEVEL_P12_FIXED_GROUP_STRESS`**. Panels A-D passed, but panel E retained only **94 qualified streams**, below the immutable floor of 95. Its macro F1 remained 0.349308 and annual all-shower gains stayed positive, but the qualification failure is decisive.

Under the preregistered #848/#850/#861 stop rule:

- M2 is a permanent no-go for promotion;
- no threshold/model/cap rescue or reselection is allowed;
- #852 full-URC integration is not authorized;
- M0/#839 is the final GMN-developed method.

This is a scientific no-go, not a technical failure.

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

PR #862 is the active transport-only proof for exact pair-portable hard-v8/P19/P20 generation. Its first equivalence execution reproduced hard-v8 exactly but failed at P19-soft structural equality. The failure was diagnosed as an execution-context mismatch: the verifier replaced the frozen layer-specific `support.CORPUS`, while original P19/P20 executions set their own corpus contexts before catalogue parsing/generation.

The adapter has been corrected to preserve P19/P20 frozen support contexts and explicitly rebind the shared v6 year globals. A new exact-GMN structural-equivalence run is in progress. No scientific proposal rule, radius, membership, ranking, or threshold changed.

Until this exact generator-equivalence proof passes, #839 is not yet declared deployable on SonotaCo 2013/2014.

## Permanent data roles

Dataset roles are fixed and may not be swapped after outcomes are observed:

- **Development/train:** GMN 2022 + 2023, with solar longitude 20°–55° excluded during development/evaluation.
- **Single final matched literature test:** SonotaCo 2013 + 2014.
- **No-retuning external validation:** MAARSY 2022.
- **Diagnostic/history only:** scientifically consumed historical panels such as SonotaCo 2023/2025.

No SonotaCo 2013/2014 or MAARSY event-level scientific value has been opened for the final method.

## Final literature gate

`FINAL_LITERATURE_TEST_POLICY_V1.md` and the frozen #820/#854 comparator/evaluator machinery govern the one-shot SonotaCo 2013/2014 test.

The frozen candidate must be compared independently against **Sugar** and **catalogue HDBSCAN** on pairwise exact-row universes with detector-input information parity, candidate-budget parity, one-to-one maximum-total-F1 assignment, fixed size strata, and the preregistered 10,000-replicate stratified bootstrap.

The final literature stage must produce either:

- `PASS_FINAL_BROAD_CATALOGUE_SUPERIORITY`, or
- `PASS_FINAL_SPARSE_STREAM_SUPERIORITY`

against both comparators across both 2013 and 2014 under the same route. No failure authorizes retuning or a replacement SonotaCo year.

**#839 has not yet been scientifically tested against Sugar or catalogue HDBSCAN.**

## External-validation compatibility finding

The schema/source-only MAARSY preflight in `MAARSY_2022_SCHEMA_PREFLIGHT_V1.md` found that MAARSY exposes the relevant trajectory/geocentric-velocity/orbit observable class, but the frozen #839 proposal architecture is intrinsically a **two-distinct-annual-scan recurrence method**:

- hard/P19/P20 application expects two distinct annual scans;
- P19 and P20 encode cross-year recurrence;
- P20 families are exact reciprocal 4+4 constructions across the two years.

The currently fixed external panel, **MAARSY 2022 alone**, contains only one calendar-year scan for this purpose. Splitting 2022 into pseudo-years would replace independent annual recurrence with within-year subsampling and therefore change the scientific family-existence mechanism rather than merely transport it.

Preaccess result:

`MAARSY_2022_SINGLE_YEAR_FULL_URC_PREFLIGHT = INCOMPATIBLE`

This is not a scientific-performance failure and does not consume MAARSY 2022. It does mean that #839, although final under the GMN development stop rule, is **not yet a project-final deployable method capable of satisfying the required no-retuning MAARSY 2022 generalization gate**. This incompatibility must be resolved defensibly before SonotaCo 2013/2014 scientific access; it may not be hidden by a post hoc proxy or silent dataset switch.

## Final blind OrbitTrace gate

OrbitTrace remains inaccessible. `FINAL_BLIND_SEARCH_POLICY_V1.md` permits target-containing execution only after both final literature superiority and external generalization pass.

Stage A must freeze the complete ranking without target-reference access. Stage B may receive only withheld stable event-ID sets and perform exact set intersection. An eligible recovery requires >=4 exact withheld IDs in each year and >=8 total.

Only primary rank <=25 counts as `PASS_FINAL_BLIND_ORBITTRACE_DISCOVERY`. Rank 26-100 is partial only and cannot authorize target-informed retuning.

## Current authorization state

- GMN methodology selection: **closed; M0/#839 selected**.
- Literature superiority: **not established**.
- SonotaCo 2013/2014 scientific access: **not authorized**.
- MAARSY scientific validation: **not authorized**.
- OrbitTrace target access: **not authorized**.
- Solar longitude 20°–55° and all OrbitTrace target information remain sealed.

## Next required work

1. Complete exact #862 GMN generator-transport equivalence.
2. Freeze one deployable #839 application package only if all transport identities pass.
3. Resolve the pre-result MAARSY-2022 structural incompatibility without using SonotaCo/MAARSY performance values, post hoc proxies, or a silent dataset switch.
4. Only after those prerequisites are defensibly resolved may the one-shot SonotaCo 2013/2014 Sugar/HDBSCAN literature test be opened.
