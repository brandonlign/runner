# OrbitTrace support-cut × annual-density internal-mass — SonotaCo development v1

## Status and claim boundary

**FROZEN BEFORE THE FIRST SONOTACO SCORE OF THIS EXACT INTERNAL-MASS ORDERING.**

This is a **development benchmark**, not a pristine independent transfer. The already-binding fixed modal-contrast SonotaCo transfer exposed that the GMN-frozen support-resolved candidate set has very high native catalogue macro-F1 but loses tuned HDBSCAN at top-K. That aggregate outcome motivated testing another ranking mechanism that had itself already been frozen and evaluated on target-excluded GMN with SonotaCo inaccessible. Because the choice to run this ranking occurs after the earlier SonotaCo aggregate was known, any positive result here must later be validated on a separate untouched endpoint before being called independent generalization.

The method itself receives no SonotaCo parameter fitting. This protocol does not authorize a score blend, threshold search, radius search, support search, budget search, or ranking-family search after outcome.

## 1. Fixed support-resolved candidate architecture

Use the exact GMN-frozen support-resolved TopoModal method:

- support source `orbittrace_topomodal_support_resolved_cut_v1/generate_prelabel.py`, Git blob `4988997c023d9df2b504372b4290dcab379a6dcc`;
- underlying physical hierarchy source `orbittrace_topomodal_hierarchy_scale_v1/run_diagnostic.py`, Git blob `c1efa8da34dea140726a4c2fe4943eb29a304538`.

Constants remain fixed:

- solar-longitude chord scale for 5°;
- radiant-direction chord scale for 4°;
- speed scale `log(1.1)`;
- Euclidean radius `1.0`;
- manual-graph ToMATo on radius-count density;
- minimum support `4`;
- support-resolved cut recursion unchanged.

On the exact symmetric-v2 SonotaCo common universe this architecture must reproduce the same **888 pairwise-disjoint candidate memberships** as the binding fixed-transfer run `32229294081`. Candidate generation is not reopened.

## 2. Fixed annual-density bifiltration evidence

Use the exact annual-density bifiltration definition previously frozen on target-excluded GMN:

- source `orbittrace_annual_density_bifiltration_scale_v1/run_diagnostic.py`, Git blob `d8486a55661bd71e92932b290e0b7550688f3b46`;
- internal-mass source `orbittrace_support_cut_bifiltration_internal_mass_v1/run_structural.py`, Git blob `be74fad29268fa6465e1ca1e6a8d082780c5b28b`.

Only the year labels are transported mechanically from GMN `(2022,2023)` to SonotaCo `(2013,2014)`; no numerical constant changes.

For every event in the same fixed radius graph, define annual radius degrees `d_2013` and `d_2014`. For every pair of positive integer annual-density thresholds, retain vertices meeting both thresholds and take connected components of the induced fixed graph. Every reportable component `B` with support >=4 receives persistence area equal to the sum of the normalized threshold-cell areas on which its exact membership persists. Equivalently, the original implementation's positive-level widths are retained exactly.

No shower labels enter this construction.

## 3. Fixed internal two-density persistence mass

For each fixed support-resolved candidate `S`, define exactly

`M_2D(S) = (1 / |S|) * sum_{B: E(B) subseteq E(S)} |E(B)| * A(B)`

where `A(B)` is the frozen two-dimensional annual-density persistence area of exact component membership `B`.

This is the exact GMN-frozen formula. An implementation may use a mathematically equivalent direct accumulator to avoid serializing every bifiltration component, but equivalence must be established from the formula and must reproduce the original algorithm on a smaller deterministic zero-label audit case before the full SonotaCo score is opened.

Forbidden changes:

- no maximum instead of integrated mass;
- no unnormalized mass;
- no support exponent;
- no pseudocount/floor;
- no Jaccard or approximate containment;
- no modal-contrast numeric blend;
- no thresholding positive evidence;
- no quota/interleaving;
- no route-specific exception.

## 4. Fixed catalogue order

Rank all 888 support-resolved candidates lexicographically by:

1. `M_2D` descending;
2. inherited `modal_contrast` descending for exact `M_2D` ties;
3. inherited `family_hash` ascending.

Candidate memberships are unchanged. The only scientific difference from the binding fixed modal-transfer result is this already-GMN-frozen ranking evidence.

Before any shower truth score, serialize a pretruth manifest containing every candidate membership, `M_2D`, modal contrast, and final rank, plus source hashes and annual-density structural diagnostics.

## 5. SonotaCo universe and evaluator

Use the exact symmetric tuned literature v2 common universe:

- 2013 common events: 15,988;
- 2014 common events: 13,258;
- pooled: 29,246.

Rows come only from label-free preparation run `31354363306`, artifact `9050107352`.

Use the exact route-agreed truth maps and unchanged Hungarian one-to-one F1 evaluator from the existing symmetric-v2 benchmark. Budgets are `K=10,20,30,40`; primary score is mean budget macro-F1 (`auc_macro_f1`).

The immutable tuned-HDBSCAN benchmark remains:

- mean AUC macro-F1 `0.345475559012312`;
- mean K40 macro-F1 `0.46086713246967964`;
- total recovered @40 `52`;
- mean native macro-F1 `0.4762894120871253`.

The binding fixed modal-transfer result remains preserved:

- mean AUC macro-F1 `0.33211204306639563`;
- mean K40 macro-F1 `0.4455723912337259`;
- total recovered @40 `50`;
- mean native macro-F1 `0.7266723655790133`.

## 6. Development verdict

`PASS_INTERNAL_MASS_SONOTACO_DEVELOPMENT_V1` requires all of:

1. mean AUC macro-F1 strictly greater than tuned HDBSCAN `0.345475559012312`;
2. mean AUC macro-F1 strictly greater than the fixed modal-transfer `0.33211204306639563`;
3. total recovered @40 at least `52`;
4. candidate memberships exactly reproduce the fixed 888-candidate support-resolved catalogue;
5. no SonotaCo labels were used in candidate generation, internal-mass computation, or ranking.

Otherwise verdict is `FAIL_INTERNAL_MASS_SONOTACO_DEVELOPMENT_V1`.

This is deliberately stricter than merely improving the prior TopoModal rank. A PASS would be **real development benchmark progress** but, because SonotaCo has already been exposed at aggregate level, would still require a separate untouched external test before a generalization claim.

The first technically valid result is binding. No parameter or ranking change is permitted as a rescue of v1 after outcome.
