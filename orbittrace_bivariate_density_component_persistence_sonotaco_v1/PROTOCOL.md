# Bivariate annual-density component persistence v1 — conditional exposed SonotaCo transfer

## Status

**FROZEN BEFORE THE FIRST TECHNICALLY VALID GMN TRUTH OUTCOME OF BDCP1.** Execute only if target-excluded GMN sparse development returns `PASS_BIVARIATE_DENSITY_COMPONENT_PERSISTENCE_V1`.

SonotaCo 2013/2014 is **EXPOSED DEVELOPMENT ONLY**, never pristine external validation. No protected OrbitTrace target access, MAARSY, or DMS is authorized.

## Exact successor

Use these exact frozen source blobs:

- GMN scientific protocol `5fab9fee2cf868b98ac50dc16db1580977ae9a12`;
- prelabel generator `1f35236a23241bfa955e1cb1eae6386ae832d9ee`;
- sealed evaluator `d341eb97b30d8e70a948d38693e7a10893ec6d2e`;
- inherited fixed-geometry helper `752df8212ce601227f6e9170b0fe994ba06b515d` from commit `312b1b718ae105813de242355142a74e7d377d65`.

For each SonotaCo matched route, substitute years 2013 and 2014 symmetrically for GMN years 2022 and 2023:

1. exact #1284 physical embedding and radius-1.0 graph;
2. annual radius-neighbor counts `d_13`, `d_14` and annual-normalized coordinates `d_13/N_13`, `d_14/N_14`;
3. no scalarization of the two coordinates;
4. enumerate every integer threshold pair `(k13,k14)` from zero through the respective maximum annual neighbor counts;
5. at each pair take every connected component of the induced active subgraph `{d_13>=k13 AND d_14>=k14}`;
6. exact membership support-cell count across the complete two-dimensional threshold lattice;
7. retain memberships with >=4 events after complete enumeration;
8. score `support_cells/(N_13*N_14)`;
9. rank by that score descending, then deterministic family hash.

No threshold selection, Pareto threshold subset, diagonal slice, scalar annual combiner, smoothing, pseudocount, alternate area weighting, component-size bonus, or SonotaCo-informed ranking is allowed.

## Exact label-free inputs

Reuse historical label-free preparation artifact `9050107352`, `orbittrace-final-sonotaco-label-free-preparation-v2`, digest `sha256:1296d757b5ea1dd94f9c9077fd769fdc8f00ec06d0881d8548fd1df4608344cc`.

Sugar-matched route:
- 2013 SHA-256 `47fb0b700fbf710c7b061eead343016bd8d182756eb0c7f406507c5739e4c4f8`, 18,638 events;
- 2014 SHA-256 `bc83c113e9a14b1c6e1ef460ca9a40e05df77f3a449fec6064f8910add04c912`, 15,400 events.

HDBSCAN-matched route:
- 2013 SHA-256 `2433b556d4a859580ef5431d2307ef34c8fa4c15d42841a2ec7b0c11e5f1f158`, 16,028 events;
- 2014 SHA-256 `206692292b2ca252777e40c13c367880740d8e2576d27615f7ea94b7790e3f55`, 13,283 events.

Pool both years within each route before graph/filtration construction. Only ID, year, solar longitude, Sun-centered ecliptic radiant longitude/latitude, and geocentric speed may enter the method. Inclusive `[20°,55°]` rows are forbidden and fail closed.

## Mandatory pretruth freeze

Before SonotaCo truth or comparator results are loaded, for both routes serialize and SHA-256 seal:

- exact input hashes and annual totals;
- graph configuration and annual count-coordinate hashes;
- complete threshold-lattice dimensions;
- all support-4 component memberships, support-cell counts, scores, and final ranks;
- source/artifact/firewall hashes.

No candidate may be regenerated, filtered, or reranked after truth opens.

## Exact historical evaluator

After pretruth seal only, use historical exposed truth/evaluation artifact `9069505548`, files `truth_{route}_{year}.json` and `evaluation_{route}_{year}.json`.

For each of four panels:
1. restrict each frozen pooled candidate to that panel year's truth IDs;
2. preserve frozen pooled order;
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

## Frozen controls

Selected recurrent-EOM parent, binding run `31829200215`, artifact `9230008341`, result SHA-256 `c2395a86be5ba8a8b801210ac6e64b97c446e724991207aef85062ee00b89f12`:
- Sugar 2013 `0.3752906816 / 23`;
- Sugar 2014 `0.4377312230 / 24`;
- HDBSCAN 2013 `0.1914598192 / 11`;
- HDBSCAN 2014 `0.1685878550 / 9`.

V31 controls:
- Sugar 2013 `0.2719801488280529 / 16`;
- Sugar 2014 `0.31529041952487225 / 17`;
- HDBSCAN 2013 `0.14888037368183737 / 9`;
- HDBSCAN 2014 `0.15198123772301594 / 9`.

Historical literature controls, descriptive only:
- Sugar 2013 `0.2037265747 / 13`;
- Sugar 2014 `0.2590152773 / 15`;
- HDBSCAN 2013 `0.1681302505 / 10`;
- HDBSCAN 2014 `0.1568959558 / 9`.

## Frozen transfer gate

`PASS_BIVARIATE_DENSITY_COMPONENT_PERSISTENCE_SONOTACO_V1` requires **all four panels** to satisfy both versus selected recurrent-EOM:

- successor macro-F1 strictly greater;
- successor recovered F1>0.5 count at least recurrent-EOM.

No averaging, route exception, aggregate rescue, or alternate comparator may replace this gate. Also report the same pairwise comparison versus v31 and literature.

Any primary-panel failure closes this exact exposed transfer benchmark and authorizes no SonotaCo-informed modification.

## Role/firewall

Every output records `sonotaco_role='EXPOSED_DEVELOPMENT_ONLY'`, `conditional_on_gmn_pass=true`, `blind_exclusion=[20.0,55.0]`, `target_information_access=false`, `target_region_events_accessed=false`, `maarsy_scientific_access=false`, `dms_scientific_access=false`, and `post_result_parameter_search=false`.