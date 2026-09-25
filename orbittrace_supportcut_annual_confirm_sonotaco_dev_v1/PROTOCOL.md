# OrbitTrace support-resolved cut × annual topology confirmation — SonotaCo development v1

## Status

**FROZEN BEFORE THE FIRST SONOTACO SCORE OF THIS EXACT COMBINATION.**

This is a development benchmark, not pristine independent validation. The fixed support-resolved TopoModal SonotaCo transfer has already been scored at aggregate level, so SonotaCo is no longer an untouched endpoint for method-family selection. The two components combined here were nevertheless frozen earlier on target-excluded GMN with SonotaCo inaccessible:

1. support-resolved TopoModal candidate extraction;
2. independent annual-topology confirmation as a ranking principle.

The combination below is fixed before its first score. No SonotaCo labels may influence its geometry, candidates, annual topologies, confirmation score, or ordering.

## Pooled candidate universe

Use the exact support-resolved TopoModal method from:

- `orbittrace_topomodal_support_resolved_cut_v1/generate_prelabel.py`, Git blob `4988997c023d9df2b504372b4290dcab379a6dcc`;
- `orbittrace_topomodal_hierarchy_scale_v1/run_diagnostic.py`, Git blob `c1efa8da34dea140726a4c2fe4943eb29a304538`.

Constants remain:

- physical solar-longitude scale = 5° chord;
- physical radiant-direction scale = 4° chord;
- speed scale = `log(1.1)`;
- Euclidean radius graph `r=1.0`;
- radius-count density;
- manual-graph ToMATo;
- minimum reportable support 4;
- support-resolved cut recursion unchanged.

On the exact 29,246-event symmetric-v2 SonotaCo common universe, candidate memberships must reproduce the previously observed fixed-transfer catalogue exactly: 888 pairwise-disjoint candidates. Candidate membership is not reopened.

## Independent annual topology

For each year separately, 2013 and 2014:

1. restrict the same common event universe to that year;
2. use the exact same fixed physical embedding and radius graph;
3. compute annual radius-count density using only that year's event count;
4. fit the same manual-graph/manual-density ToMATo hierarchy;
5. retain every complete annual hierarchy membership with support >=4.

No annual support threshold, persistence threshold, cluster count, HDBSCAN overlap, station weighting, or truth-derived filter is allowed.

This transports the already-frozen annual-topology-confirmation principle mechanically from GMN years 2022/2023 to SonotaCo years 2013/2014.

## Confirmation score

For every fixed pooled support-resolved candidate `C` and year `y`:

- let `C_y` be candidate members from year `y`;
- if `|C_y| < 4`, set `J_y(C)=0`;
- otherwise compute the Jaccard similarity between `C_y` and every reportable complete annual TopoModal family `A_y`;
- define `J_y(C)=max_A Jaccard(C_y,A_y)`.

The sole ranking coordinate is

`J_rec(C) = min(J_2013(C), J_2014(C))`.

Rank all 888 fixed pooled candidates by:

1. `J_rec` descending;
2. inherited `family_hash` ascending.

No pooled modal contrast, support, root status, member count, year balance, recurrent-EOM overlap, HDBSCAN score, orbit information, or numeric blend enters ranking.

## Zero-label pretruth requirement

Before any shower labels are parsed, serialize and SHA-256 seal:

- exact pooled candidate memberships;
- exact annual topology memberships or a complete deterministic membership summary sufficient for reproduction;
- `J_2013`, `J_2014`, `J_rec` for every pooled candidate;
- final rank;
- source hashes and common-universe counts.

The truth evaluator must consume this sealed ranking unchanged and may not import the topology generator.

## SonotaCo universe and evaluator

Use the exact symmetric-v2 common universe from label-free preparation run `31354363306`, artifact `9050107352`:

- 2013: 15,988 events;
- 2014: 13,258 events;
- pooled: 29,246 events.

Use the same route-agreed truth maps and exact Hungarian one-to-one F1 evaluator used in symmetric tuned literature benchmark v2. Candidate budgets remain `K=10,20,30,40`; primary score remains the unweighted mean budget macro-F1 (`auc_macro_f1`).

Immutable references:

Tuned HDBSCAN:
- AUC `0.345475559012312`;
- K40 macro-F1 `0.46086713246967964`;
- recovered @40 `52`;
- native macro-F1 `0.4762894120871253`.

Fixed modal-contrast support-resolved transfer:
- AUC `0.33211204306639563`;
- K40 macro-F1 `0.4455723912337259`;
- recovered @40 `50`;
- native macro-F1 `0.7266723655790133`.

## Development verdict

`PASS_SUPPORTCUT_ANNUAL_CONFIRM_SONOTACO_DEV_V1` requires all of:

1. mean AUC macro-F1 strictly greater than tuned HDBSCAN `0.345475559012312`;
2. mean AUC macro-F1 strictly greater than fixed modal transfer `0.33211204306639563`;
3. total recovered @40 at least `52`;
4. exactly 888 pooled candidate memberships, identical to the fixed support-resolved catalogue;
5. no SonotaCo labels used before the ranking was sealed.

Otherwise verdict is `FAIL_SUPPORTCUT_ANNUAL_CONFIRM_SONOTACO_DEV_V1`.

A PASS is real SonotaCo development-benchmark improvement, but because SonotaCo is already exposed at aggregate level it is not independent generalization. A later untouched external endpoint would still be mandatory for a portability claim.

The first technically valid score is binding. No change to support, radius, embedding, annual topology, Jaccard, `min`, tie-break, candidate universe, budgets, evaluator, or gates is allowed after outcome.
