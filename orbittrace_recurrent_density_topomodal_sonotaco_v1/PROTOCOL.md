# Recurrent-density topomodal v1 — conditional exposed SonotaCo transfer

## Status

**FROZEN BEFORE THE FIRST TECHNICALLY VALID GMN TRUTH OUTCOME OF RECURRENT-DENSITY TOPOMODAL V1.**

Execute only if target-excluded GMN sparse development returns `PASS_RECURRENT_DENSITY_TOPOMODAL_V1`.

SonotaCo 2013/2014 is **EXPOSED DEVELOPMENT ONLY**, never pristine external validation. No protected OrbitTrace target access, MAARSY, or DMS is authorized.

## 1. Exact successor

Use these exact frozen source blobs:

- scientific protocol: `ebe2ec01a1b306efceba7c721e2df45568e01b7f`;
- prelabel generator: `12a811d5e8d64ace6b6fe90115b552e3682c0c46`;
- sealed evaluator: `dac5ca719b17a155d91884a61357c56aec390ad5`;
- inherited #1284 helper source: `752df8212ce601227f6e9170b0fe994ba06b515d` from commit `312b1b718ae105813de242355142a74e7d377d65`.

Method is unchanged from GMN:

1. exact #1284 physical embedding and radius-1.0 graph;
2. for each pooled route catalogue, compute annual normalized local radius densities `rho_2013=d_2013/N_2013`, `rho_2014=d_2014/N_2014`;
3. ToMATo manual weight is `min(rho_2013,rho_2014)` at every point;
4. no point deletion for zero recurrent density;
5. complete leaf/internal/root ToMATo hierarchy;
6. reporting support >=4 only after hierarchy construction;
7. exact #1284 native prominence/root ranking applied to this recurrent density field.

No SonotaCo outcome, truth label, comparator value, fitted weight, alternate annual combiner, pseudocount, or threshold may enter candidate generation or ranking.

## 2. Exact label-free SonotaCo inputs

Reuse the historical label-free preparation artifact exactly:

- artifact `9050107352`, `orbittrace-final-sonotaco-label-free-preparation-v2`;
- artifact digest `sha256:1296d757b5ea1dd94f9c9077fd769fdc8f00ec06d0881d8548fd1df4608344cc`.

Exact accessible rows:

### Sugar-matched route
- 2013 SHA-256 `47fb0b700fbf710c7b061eead343016bd8d182756eb0c7f406507c5739e4c4f8`, 18,638 events;
- 2014 SHA-256 `bc83c113e9a14b1c6e1ef460ca9a40e05df77f3a449fec6064f8910add04c912`, 15,400 events.

### HDBSCAN-matched route
- 2013 SHA-256 `2433b556d4a859580ef5431d2307ef34c8fa4c15d42841a2ec7b0c11e5f1f158`, 16,028 events;
- 2014 SHA-256 `206692292b2ca252777e40c13c367880740d8e2576d27615f7ea94b7790e3f55`, 13,283 events.

Pool the two years separately within each route before graph/density/hierarchy construction. The recurrent-density formula substitutes years 2013/2014 symmetrically for GMN's 2022/2023.

Only ID, year, solar longitude, Sun-centered ecliptic radiant longitude/latitude, and geocentric speed may enter the method. Protected inclusive `[20°,55°]` rows are forbidden and must fail closed if encountered.

## 3. Mandatory pretruth boundary

Before SonotaCo truth or comparator results are loaded, for both pooled routes serialize and SHA-256 seal:

- input row hashes and annual totals;
- exact radius graph configuration;
- recurrent-density vector hash;
- full ToMATo hierarchy summary;
- every support-4 candidate membership and complete deterministic order;
- source/artifact hashes and firewall flags.

No candidate may be regenerated, removed, or reranked after truth opens.

## 4. Exact historical evaluator

After pretruth seal only, use historical exposed truth/evaluation artifact `9069505548` with `truth_{route}_{year}.json` and `evaluation_{route}_{year}.json`.

For every panel:

1. restrict each frozen pooled candidate membership to the panel year's truth IDs;
2. preserve frozen pooled ranking;
3. truncate to the historical comparator budget;
4. include showers with >=4 truth events;
5. build shower-by-candidate F1 matrix;
6. Hungarian maximum-F1 one-to-one assignment;
7. report macro-F1 and recovered count with assigned F1 >0.5.

Exact budgets:

- Sugar 2013: 34;
- Sugar 2014: 46;
- HDBSCAN 2013: 11;
- HDBSCAN 2014: 9.

## 5. Frozen controls

Selected recurrent-EOM parent — binding run `31829200215`, artifact `9230008341`, result SHA-256 `c2395a86be5ba8a8b801210ac6e64b97c446e724991207aef85062ee00b89f12`:

- Sugar 2013: `0.3752906816 / 23`;
- Sugar 2014: `0.4377312230 / 24`;
- HDBSCAN 2013: `0.1914598192 / 11`;
- HDBSCAN 2014: `0.1685878550 / 9`.

V31 binding controls:

- Sugar 2013: `0.2719801488280529 / 16`;
- Sugar 2014: `0.31529041952487225 / 17`;
- HDBSCAN 2013: `0.14888037368183737 / 9`;
- HDBSCAN 2014: `0.15198123772301594 / 9`.

Historical literature controls, descriptive only:

- Sugar 2013: `0.2037265747 / 13`;
- Sugar 2014: `0.2590152773 / 15`;
- HDBSCAN 2013: `0.1681302505 / 10`;
- HDBSCAN 2014: `0.1568959558 / 9`.

## 6. Frozen primary gate

`PASS_RECURRENT_DENSITY_TOPOMODAL_SONOTACO_V1` requires **all four panels** to satisfy both versus recurrent-EOM:

- macro-F1 strictly greater;
- recovered F1>0.5 count at least as high.

No route averaging, panel exception, aggregate rescue, or alternate comparator may replace this gate.

Also report the identical pairwise comparison against v31 and literature on every panel.

Any primary-panel failure closes the exposed transfer result and does not authorize SonotaCo-informed modification.

## 7. Role/firewall

Every output records:

- `sonotaco_role='EXPOSED_DEVELOPMENT_ONLY'`;
- `conditional_on_gmn_pass=true`;
- `blind_exclusion=[20.0,55.0]`;
- `target_information_access=false`;
- `target_region_events_accessed=false`;
- `maarsy_scientific_access=false`;
- `dms_scientific_access=false`;
- `post_result_parameter_search=false`.
