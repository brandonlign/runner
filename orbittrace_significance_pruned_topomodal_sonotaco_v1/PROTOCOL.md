# Significance-pruned fixed-graph topomodal v1 — conditional exposed SonotaCo transfer

## Status

**FROZEN BEFORE THE FIRST TECHNICALLY VALID GMN TRUTH OUTCOME OF `SIGNIFICANCE_PRUNED_TOPOMODAL_V1`.**

Execute only if target-excluded GMN returns full `PASS_SIGNIFICANCE_PRUNED_TOPOMODAL_V1`, including candidate-budget sufficiency, both cross-scale structural gates, and all ten sparse truth gates.

SonotaCo 2013/2014 is **EXPOSED DEVELOPMENT ONLY**, never pristine validation. Protected OrbitTrace target access, MAARSY, and DMS remain forbidden.

## Exact successor transfer

For each historical matched SonotaCo route, pool its 2013+2014 label-free rows and apply the GMN successor without scientific modification:

1. reconstruct exact GEO6;
2. compute third nearest-other-event Euclidean distance `r3` on the pooled route;
3. sort ascending `(r3,event_id)` and assign `q=1-rank/(n+1)`;
4. construct exact #1284 physical embedding at 5 deg solar / 4 deg radiant / 10% log-speed scale;
5. construct exact symmetric Euclidean radius-1 graph;
6. fit observed GUDHI 3.12.0 manual-graph/manual-q ToMATo;
7. run exactly `B=199` deterministic q-over-graph permutations using route-specific seeds
   `uint64_be(SHA256('ORBITTRACE_SIGPRUNE_TM_SONOTACO_V1|' + route + '|' + b)[0:8])`;
8. for each null fit record maximum finite ToMATo prominence, or zero for an empty finite diagram;
9. set `tau` to the strict max-statistic FWER 0.05 threshold, exactly the 10th largest of the 199 null maxima;
10. set observed `merge_threshold_=tau` and use the resulting simplified flat partition;
11. identify surviving finite/root modes exactly as in the GMN protocol;
12. require support >=4 only after simplification;
13. rank finite significant candidates before roots by the exact GMN p-value/prominence/peak-q rule, then roots by peak q/member count/family hash.

No route-specific alpha, B, k, physical scale, density transform, significance correction, ranking, root rule, or support adjustment is permitted.

## Exact label-free inputs

Reuse historical label-free preparation artifact `9050107352`, `orbittrace-final-sonotaco-label-free-preparation-v2`, digest `sha256:1296d757b5ea1dd94f9c9077fd769fdc8f00ec06d0881d8548fd1df4608344cc`.

Sugar-matched route:
- 2013 SHA-256 `47fb0b700fbf710c7b061eead343016bd8d182756eb0c7f406507c5739e4c4f8`, 18,638 events;
- 2014 SHA-256 `bc83c113e9a14b1c6e1ef460ca9a40e05df77f3a449fec6064f8910add04c912`, 15,400 events.

HDBSCAN-matched route:
- 2013 SHA-256 `2433b556d4a859580ef5431d2307ef34c8fa4c15d42841a2ec7b0c11e5f1f158`, 16,028 events;
- 2014 SHA-256 `206692292b2ca252777e40c13c367880740d8e2576d27615f7ea94b7790e3f55`, 13,283 events.

Inclusive `[20.0,55.0]` rows remain forbidden and fail closed.

## Mandatory pretruth freeze

Before SonotaCo truth or comparator-result files are loaded, serialize and SHA-256 seal for both routes:

- exact label-free input hashes and pooled/annual totals;
- r3/q/density-order hashes;
- physical graph configuration/hash;
- all 199 null maximum prominences and ordered hash;
- exact `tau`, alpha, B, and observed finite-mode mapping audit;
- every simplified candidate membership, survivor-mode metadata, p-value/prominence/root status, and final rank;
- source/artifact/firewall hashes.

Candidate generation, null calibration, simplification, and ranking may not run after truth opens.

## Exact historical evaluator

After pretruth seal only, use historical exposed truth/evaluation artifact `9069505548`, files `truth_{route}_{year}.json` and `evaluation_{route}_{year}.json`.

For each of four panels:

1. restrict every frozen pooled successor candidate to that panel year's truth IDs;
2. preserve frozen pooled rank order;
3. truncate to the historical panel budget;
4. include showers with >=4 truth events;
5. build shower-by-candidate F1 matrix;
6. exact Hungarian maximum-F1 one-to-one assignment;
7. report macro-F1 and assigned-shower count with F1>0.5.

Exact budgets:
- Sugar 2013: 34;
- Sugar 2014: 46;
- HDBSCAN 2013: 11;
- HDBSCAN 2014: 9.

If the frozen successor produces fewer candidates than a panel budget, use all available candidates and automatically fail that panel's primary transfer gate; no discarded hierarchy nodes may be added.

## Frozen primary controls

Selected recurrent-EOM parent, binding run `31829200215`, artifact `9230008341`, result SHA-256 `c2395a86be5ba8a8b801210ac6e64b97c446e724991207aef85062ee00b89f12`:
- Sugar 2013 `0.3752906816276458 / 23`;
- Sugar 2014 `0.43773122295664196 / 24`;
- HDBSCAN 2013 `0.1914598192215768 / 11`;
- HDBSCAN 2014 `0.1685878550176112 / 9`.

Also report descriptive v31 and matched-literature comparisons, but neither may replace the recurrent-EOM primary gate.

V31:
- Sugar 2013 `0.2719801488280529 / 16`;
- Sugar 2014 `0.31529041952487225 / 17`;
- HDBSCAN 2013 `0.14888037368183737 / 9`;
- HDBSCAN 2014 `0.15198123772301594 / 9`.

Matched literature:
- Sugar 2013 `0.2037265747 / 13`;
- Sugar 2014 `0.2590152773 / 15`;
- HDBSCAN 2013 `0.1681302505 / 10`;
- HDBSCAN 2014 `0.1568959558 / 9`.

## Frozen transfer gate

`PASS_SIGNIFICANCE_PRUNED_TOPOMODAL_SONOTACO_V1` requires **all four panels** to satisfy both versus selected recurrent-EOM:

- successor macro-F1 strictly greater;
- successor recovered F1>0.5 count at least recurrent-EOM;
- successor candidate count at least the frozen panel budget.

Any primary-panel failure closes the exact transfer benchmark. No averaging, route exception, aggregate rescue, alpha/B change, alternate budget, or comparator substitution is permitted.

## Firewall / role

Every output records `sonotaco_role='EXPOSED_DEVELOPMENT_ONLY'`, `conditional_on_gmn_pass=true`, `blind_exclusion=[20.0,55.0]`, `target_information_access=false`, `target_region_events_accessed=false`, `maarsy_scientific_access=false`, `dms_scientific_access=false`, and `post_result_parameter_search=false`.