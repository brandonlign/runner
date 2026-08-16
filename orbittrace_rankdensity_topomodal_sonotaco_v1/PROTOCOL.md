# Rank-density fixed-graph topomodal v1 — conditional exposed SonotaCo transfer

## Status

**FROZEN BEFORE THE FIRST TECHNICALLY VALID GMN TRUTH OUTCOME OF RANKDENSITY_TOPOMODAL_V1.**

Execute only if target-excluded GMN returns `PASS_RANKDENSITY_TOPOMODAL_V1`, including both frozen cross-scale structural gates and all ten sparse truth gates.

SonotaCo 2013/2014 is **EXPOSED DEVELOPMENT ONLY**, never pristine external validation. Protected OrbitTrace target access, MAARSY, and DMS remain forbidden.

## Exact successor transfer

For each historical matched SonotaCo route, pool its 2013+2014 label-free rows and apply the GMN successor without scientific modification:

1. reconstruct exact GEO6 from solar longitude, Sun-centered ecliptic radiant longitude/latitude, and geocentric speed;
2. compute Euclidean distance to the third nearest other pooled event;
3. sort ascending `(r3,event_id)` and assign `q_i = 1-rank_i/(n+1)` exactly;
4. construct the exact #1284 physical embedding with 5 deg solar / 4 deg radiant / 10% log-speed scales;
5. construct exact symmetric radius-1 physical graph;
6. fit GUDHI 3.12.0 ToMATo manual graph/manual density using q;
7. expose complete leaf/internal/root hierarchy, exact membership dedupe, support >=4 only after hierarchy construction;
8. apply the exact inherited intrinsic ranking semantics pinned by the GMN protocol;
9. freeze the complete pooled candidate order before SonotaCo truth is loaded.

No annual-density coordinate or year-specific recurrence term is introduced. Year identity is irrelevant to successor construction and is used only for panelwise evaluation after the pooled pretruth order is sealed.

No k change, route-specific physical scale, threshold, prominence selection, ranking weight, density transform, or SonotaCo-informed modification is permitted.

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

- exact input hashes and pooled/annual totals;
- GEO6 r3 and q-vector hashes;
- fixed physical graph configuration/hash;
- every support-4 candidate membership, hierarchy/ranking fields, and final pooled rank;
- source/artifact/firewall hashes.

Candidate generation and ranking may not run after truth opens.

## Exact historical evaluator

After pretruth seal only, use historical exposed truth/evaluation artifact `9069505548`, files `truth_{route}_{year}.json` and `evaluation_{route}_{year}.json`.

For each of four panels:

1. restrict each frozen pooled candidate to that panel year's truth IDs;
2. preserve frozen pooled rank order;
3. truncate to the historical comparator budget;
4. include showers with >=4 truth events;
5. build shower-by-candidate F1 matrix;
6. exact Hungarian maximum-F1 one-to-one assignment;
7. report macro-F1 and number of assigned showers with F1 >0.5.

Exact budgets:
- Sugar 2013: 34;
- Sugar 2014: 46;
- HDBSCAN 2013: 11;
- HDBSCAN 2014: 9.

## Frozen primary controls

Selected recurrent-EOM parent, binding run `31829200215`, artifact `9230008341`, result SHA-256 `c2395a86be5ba8a8b801210ac6e64b97c446e724991207aef85062ee00b89f12`:
- Sugar 2013 `0.3752906816276458 / 23`;
- Sugar 2014 `0.43773122295664196 / 24`;
- HDBSCAN 2013 `0.1914598192215768 / 11`;
- HDBSCAN 2014 `0.1685878550176112 / 9`.

Also report descriptive comparisons versus frozen v31 and matched literature controls, but neither may replace the recurrent-EOM primary gate.

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

`PASS_RANKDENSITY_TOPOMODAL_SONOTACO_V1` requires **all four panels** to satisfy both versus selected recurrent-EOM:

- successor macro-F1 strictly greater;
- successor recovered F1>0.5 count at least recurrent-EOM.

No averaging, route exception, aggregate rescue, alternative budget, or comparator substitution is permitted.

Any primary-panel failure closes the exact transfer benchmark and authorizes no SonotaCo-informed successor.

## Firewall / role

Every output records `sonotaco_role='EXPOSED_DEVELOPMENT_ONLY'`, `conditional_on_gmn_pass=true`, `blind_exclusion=[20.0,55.0]`, `target_information_access=false`, `target_region_events_accessed=false`, `maarsy_scientific_access=false`, `dms_scientific_access=false`, and `post_result_parameter_search=false`.