# OrbitTrace label-free v6 — final fresh SAAMER 2022–2023 external validation

## Status

Frozen before any SAAMER 2022 or 2023 meteor scientific value is decoded.

This is the final scientifically fresh SAAMER year pair available in the IAU MDC annual series. The prior frozen 2020/2021 v6 external run was integrity-clean but preregistered-power-inconclusive (69 recurrent families <100; 29 orbitally corroborated families <30). That result is preserved and does not alter any scientific rule here.

## Immutable prerequisites

- label-free v6 development run `31207688016`, verdict `PASS_LABEL_FREE_SPARSE_SUPPORT_V6_DEVELOPMENT`, artifact `9005846925`, ZIP SHA-256 `3c636b05cbfc88c6d6b2b8289b309412174b0025c305ae2f2532678927b2232b`;
- SAAMER 2022/2023 full-history freshness run `31211359126`, verdict `PASS_SAAMER_2022_2023_REPO_SCIENTIFIC_FRESHNESS_AUDIT`, artifact `9006805714`, ZIP SHA-256 `07483caffb678c808f514f25a3350364d1282c4232897d68ad4f959e20db46a0`;
- first zero-value structure run `31211663133`, artifact `9006922387`, preserved failure solely because the 2023 archive ends after October; it decoded no meteor token values;
- artifact-only common-coverage adjudication run `31211931923`, verdict `PASS_SAAMER_2022_2023_COMMON_COVERAGE_ADJUDICATION`, artifact `9007013042`, ZIP SHA-256 `d12ae6071639fc7c73d588bf1ef9eb4a19c1c6527167ec0a81b0cf1232810480`;
- official archive SHA-256 values pinned before scientific access:
  - 2022: `8347c4fde8d1035702f74002321e55d66df42055a0d3bf46424fd286b6e861f7`;
  - 2023: `0220c5cb32eb4fdaaaca8773de03512864246c7a91c8211e68cc5d5f54f16f8a`;
- legend SHA-256: `afb3f9f7a3b753234db8dbb7219d14095510265293485fc1e744f659a857f48b`;
- exact 16-field schema: `IC, Yr, Mn, Day, LS, HM, RA, DEC, Vg, Vh, q, e, a, i, arg, nod`.

## Frozen common coverage

Use exactly nominal months January through October in **both** years.

- 2022 November and December are excluded by ZIP member identity before any row in those files is decoded.
- 2023 contains exactly January–October in the official archive.
- No alternate month subset is evaluated.
- This coverage rule was determined from archive-member metadata only, before any 2022/2023 meteor value was read.

Official archive transport:

- `https://ceres.ta3.sk/iaumdcdb/dataDBs/radio_offline/iaumdcSAAMER2022.zip`
- `https://ceres.ta3.sk/iaumdcdb/dataDBs/radio_offline/iaumdcSAAMER2023.zip`

## Blindness and parser

- exact years 2022 and 2023;
- for each selected Jan–Oct DAT row, require exactly 16 tokens;
- `LS` is the first scientific field interpreted;
- immediately discard `20.0° <= LS <= 55.0°` before `RA`, `DEC`, `Vg`, year/month identity, or orbital-element interpretation;
- then require nominal year/month identity, finite `RA`, `DEC`, `Vg`, `0<=RA<360`, `-90<=DEC<=90`, `5<Vg<75 km/s`;
- reuse the exact frozen support-code equatorial-to-ecliptic conversion and Sun-centered longitude `wrap180(ecliptic_lon - LS)`;
- candidate/ranking geometry contains only event id, year, LS, Sun-centered ecliptic longitude, ecliptic latitude, and Vg;
- no source shower label exists or is used;
- `q,e,a,i,arg,nod` may not be interpreted until every candidate family and every ranking is frozen;
- no OrbitTrace coordinates, activity values, members, HDBSCAN assignments, targeted-recovery result, or target-region event may enter this run.

## Frozen density normalization

Unchanged from the 2020/2021 external protocol:

- 36 fixed 10° solar-longitude bins;
- retain at most **10,000** eligible events per year/bin;
- if a bin exceeds 10,000, keep the 10,000 smallest SHA-256 hashes of `SAAMER|year|member|physical_row_number`;
- hash selection uses no scientific value;
- no alternate density cap is evaluated.

## Frozen v6 discovery architecture

Unchanged from the passed v6 development and 2020/2021 external protocol:

- fixed4 geometry and scales;
- 64-neighbor first shortlist and 128-neighbor exact audit;
- one anchored quartet per anchor;
- consolidate identical quartets;
- anchor multiplicity >=2;
- no empirical/null score threshold;
- top 512 quartets per bin by frozen anchor-count / quartet-score / identifier ordering;
- within-year components: >=4 events and >=2 retained quartets;
- cross-year family link radius 1.5 in the frozen geometry;
- recurrent family must span both years;
- deterministic 128-event local episode per family/year;
- primary multiplicity `M=(multi-anchor-v3-energy / Brown-peak)^2`;
- primary rank: worst-year M descending, geometric-mean M descending, family id;
- comparators: label-free structural persistence, Brown minimum-year score, total-v3 minimum-year score;
- no multiplicity p-value, RRF, threshold search, density search, cap search, link-radius search, weight search, or endpoint search.

## Frozen independent orbital corroboration

Only after all four rankings are frozen, re-read orbital elements for recurrent-family events and use the exact previously frozen Southworth–Hawkins implementation from `orbittrace_literature_comparison/literature_comparators.py`, blob `ab17e1205d72d8ab8361d8ba6cdad2e4c31fdcb2`, with `D_SH < 0.05`.

For each family:

1. construct the D_SH<0.05 single-link graph;
2. find the largest connected component with >=4 events from 2022 and >=4 from 2023;
3. orbital corroboration precision = component size / full family size;
4. family is orbitally corroborated iff such a component exists and precision >=0.50.

The orbital validator cannot alter, merge, split, filter, or rerank a discovery family.

## Frozen endpoints and gates

Let `N` be recurrent families, `Q` orbitally corroborated families, and `K=min(100,N)`.

Report for every ranking: top-K corroborated count/fraction, median corroborated-family rank, MRR, and one-sided hypergeometric enrichment p-value.

### Integrity / power — all required

1. exact prerequisite source/artifact/freshness/common-coverage guards;
2. exact archive and legend hashes;
3. exactly Jan–Oct members opened in both years;
4. target interval removed before radiant/speed/orbit access;
5. orbital elements interpreted only after ranking freeze;
6. exact 10,000/bin identity-hash normalization;
7. >=24 scannable bins/year;
8. zero 64→128 shortlist audit mismatches after reconciliation;
9. every recurrent family spans both years;
10. every local episode exactly 128 events;
11. Brown equivalence error <=1e-10;
12. `N >= 100` recurrent families;
13. `Q >= 30` orbitally corroborated families.

### Scientific — unchanged from 2020/2021

1. multiplicity top-K corroborated count >= Brown top-K count + 1;
2. multiplicity top-K corroborated count >= `ceil(0.90 * persistence top-K count)`;
3. multiplicity top-K hypergeometric enrichment p <=0.05.

A powered all-gate pass is `PASS_LABEL_FREE_V6_SAAMER_2022_2023_EXTERNAL_VALIDATION`.
A powered scientific failure is `FAIL_LABEL_FREE_V6_SAAMER_2022_2023_EXTERNAL_VALIDATION`.
An integrity or power failure is reported separately.

## Terminal continuation rule

This is the final fresh SAAMER pair. If it is underpowered, external v6 validation remains inconclusive; no power gate is relaxed and no further SAAMER year-pair cycling is permitted. If it fails scientifically, the failure is binding. Only a powered pass authorizes a separately committed final target-free GMN v6 discovery protocol before the 20°–55° OrbitTrace region is opened.
