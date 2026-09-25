# OrbitTrace fixed support-resolved TopoModal → SonotaCo transfer v1

## Status

**FROZEN BEFORE THE FIRST SONOTACO TRUTH SCORE OF THIS EXACT TRANSFER.**

This endpoint tests whether the exact support-resolved TopoModal catalogue architecture previously frozen and evaluated only on target-excluded GMN transfers to the stronger SonotaCo benchmark on which tuned ordinary HDBSCAN currently leads recurrent-EOM.

The transferred method is not retuned, rescored, or modified using SonotaCo. Its source code, physical scales, support floor, cut recursion, and modal-contrast ranking were all fixed in the earlier GMN experiment, whose firewall explicitly denied SonotaCo access. The SonotaCo literature competitors retain their already-binding opposite-year tuned results from symmetric tuned literature benchmark v2.

A valid negative result closes only this exact fixed transfer; it does not authorize post-result alteration of the transferred method.

## Immutable transferred method

Use exact source files:

1. support-resolved cut implementation
   - branch: `agent/orbittrace-topomodal-support-resolved-cut-v1`
   - path: `orbittrace_topomodal_support_resolved_cut_v1/generate_prelabel.py`
   - Git blob: `4988997c023d9df2b504372b4290dcab379a6dcc`.
2. underlying physical TopoModal hierarchy
   - branch: `agent/orbittrace-topomodal-hierarchy-scale-v1`
   - path: `orbittrace_topomodal_hierarchy_scale_v1/run_diagnostic.py`
   - Git blob: `c1efa8da34dea140726a4c2fe4943eb29a304538`.

The exact inherited method has:

- physical embedding bandwidths: solar-longitude chord scale for 5°, radiant-direction chord scale for 4°, and `log(v_g)` scale `log(1.1)`;
- Euclidean radius graph `RADIUS = 1.0`;
- radius-count density;
- manual-graph ToMATo hierarchy;
- minimum reportable support `MIN_SUPPORT = 4`;
- support-resolved cut recursion: descend only when both children have support >=4, otherwise retain the reportable parent;
- pairwise-disjoint selected candidates partitioning every reportable root;
- ranking by active-mode `modal_contrast` descending, then exact frozen membership hash.

There is no SonotaCo parameter grid. In particular, do not tune radius, support floor, embedding bandwidths, density definition, hierarchy, cut recursion, rank score, tie-breaks, or candidate budgets from SonotaCo labels.

## SonotaCo universe

Use the exact immutable label-free preparation from workflow run `31354363306`, artifact `9050107352` (`orbittrace-final-sonotaco-label-free-preparation-v2`).

Reproduce the same event universe as symmetric tuned literature benchmark v2: for each of 2013 and 2014, intersect event IDs available to both the frozen Sugar and HDBSCAN routes, merge only nonconflicting row fields, and pool the two years label-free. Expected common counts:

- 2013: 15,988 events;
- 2014: 13,258 events;
- pooled: 29,246 events.

For the transferred physical method map each merged row as follows, without fitting or calibration:

- `id` = common event ID;
- `year` = 2013 or 2014;
- `sol` = row solar longitude;
- `lon` = frozen row `sun_lon`;
- `lat` = frozen row `ecl_lat`;
- `vg` = row geocentric speed.

All candidate generation and ranking use the pooled 2013+2014 rows with **no shower labels**.

## Truth and evaluator

Use the same route-agreed truth maps and exact evaluator already frozen in symmetric tuned literature benchmark v2 from workflow run `31405109267`, artifact `9069505548`.

For each test year independently, intersect each pooled candidate with that year's truth IDs and evaluate using the unchanged Hungarian one-to-one shower/candidate F1 evaluator at common candidate budgets `K = 10,20,30,40`, plus the native complete catalogue.

The primary score is the unweighted mean of the four budget macro-F1 values (`auc_macro_f1`). Aggregate the fixed transferred method by the mean of its 2013 and 2014 AUC macro-F1 values, exactly as the existing benchmark aggregates opposite-year test folds.

The immutable tuned HDBSCAN comparator is the existing symmetric-v2 result:

- mean test AUC macro-F1 `0.345475559012312`;
- mean K40 macro-F1 `0.46086713246967964`;
- total recovered showers at K40 `52`;
- mean native macro-F1 `0.4762894120871253`.

No existing literature result is recomputed or weakened for this transfer.

## Binding verdict

Form a four-method ranking consisting of the exact existing symmetric-v2 aggregates for tuned HDBSCAN, recurrent-EOM, and Sugar plus this fixed support-resolved TopoModal transfer. Use the same existing ranking key:

1. mean test AUC macro-F1;
2. total recovered showers at K40;
3. mean K40 macro-F1.

`PASS_FIXED_TOPOMODAL_SONOTACO_TRANSFER_V1` requires the transferred method to rank first **and** to have mean AUC macro-F1 strictly greater than tuned HDBSCAN's `0.345475559012312`.

Otherwise the verdict is `FAIL_FIXED_TOPOMODAL_SONOTACO_TRANSFER_V1`.

Secondary/native metrics are reported but are not retroactive rescue criteria.

The first technically valid result is binding. After outcome, do not alter any transferred-method constant, source, ranking, event universe, truth map, evaluator, budget, comparator value, or verdict rule for v1.

## Claim boundary

A PASS would be strong evidence that an unchanged method developed on target-excluded GMN transfers to SonotaCo and beats the already-tuned literature competitors on the same generic catalogue-recovery metric. It would not by itself prove universal state of the art or pristine-survey generalization.

A FAIL means no benchmark improvement from this exact fixed transfer. It must be preserved even if a later separately preregistered, method-native tuning experiment is attempted.
