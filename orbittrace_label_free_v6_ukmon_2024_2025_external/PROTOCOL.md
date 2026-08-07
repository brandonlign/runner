# OrbitTrace label-free v6 — UKMON 2024–2025 external validation

## Status
Frozen before the first UKMON 2024 or 2025 meteor-data request.

UKMON 2024 and 2025 were reserved before any UKMON access and passed a full-repository freshness audit. The parser/interface was then developed only on the UKMON-published example date 2022-08-14. No 2023, 2024, or 2025 UKMON scientific data entered development.

This is a one-shot external validation of the already-passed label-free sparse-support multiplicity v6 architecture. No scientific gate may be changed after reserved-year access begins.

## Immutable prerequisites
- v6 development run `31207688016`, artifact `9005846925`, verdict `PASS_LABEL_FREE_SPARSE_SUPPORT_V6_DEVELOPMENT`;
- v6 artifact ZIP SHA-256 `3c636b05cbfc88c6d6b2b8289b309412174b0025c305ae2f2532678927b2232b`;
- UKMON 2024/2025 freshness run `31213731631`, artifact `9007677623`, verdict `PASS_UKMON_2024_2025_REPO_SCIENTIFIC_FRESHNESS_AUDIT`;
- freshness artifact ZIP SHA-256 `fb2f8122066fa63e7128610256ea91a692de089c7a1f4539a560fd1b4bd86617`;
- corrected 2022 live-interface run `31214751332`, artifact `9008043772`, verdict `PASS_UKMON_2022_LIVE_INTERFACE_DEVELOPMENT`;
- interface artifact ZIP SHA-256 `0f8fce906c9d35b9bcb50cc01d656f66b8c833612a653fca5c3c8c0757dcfd16`;
- frozen D_SH comparator source blob `ab17e1205d72d8ab8361d8ba6cdad2e4c31fdcb2`.

## Frozen UKMON interface
Use exactly:
- daily summary route: `https://api.ukmeteors.co.uk/matches?reqtyp=summary&reqval=YYYYMMDD`;
- trajectory id: `orbname`;
- solar longitude: `_sol`;
- geocentric radiant: `_ra_t`, `_dc_t`;
- geocentric speed: `_vg`;
- post-ranking orbit fields: `_q`, `_e`, `_incl`, `_peri`, `_node`.

The corrected 2022 interface audit established complete required-field coverage on 653 matched trajectories and verified `_vg` in 10.45–73.24 km/s with physically usable orbital fields.

## Exact reserved corpus
- every calendar date from 2024-01-01 through 2024-12-31;
- every calendar date from 2025-01-01 through 2025-12-31;
- no 2026 data;
- no 2022/2023 data in scientific evaluation.

For each date, request the daily summary once. If and only if the daily route fails transport or returns a non-list error payload, deterministically retry the same date as four disjoint documented period requests `0-6`, `6-12`, `12-18`, `18-24`; concatenate them in that fixed order. No date may be skipped because it is scientifically inconvenient.

## Blindness boundary
For every returned matched row:
1. `orbname` is treated as opaque identity metadata;
2. `_sol` is the first scientific field converted to a number;
3. if `20.0 <= _sol <= 55.0`, discard the row immediately;
4. only after that exclusion may `_ra_t`, `_dc_t`, or `_vg` be converted;
5. source shower/classification fields, if present, are never read;
6. `_q`, `_e`, `_incl`, `_peri`, `_node` are not interpreted until every discovery family and every ranking has been frozen.

No OrbitTrace coordinates, identity, members, activity measurements, HDBSCAN assignments, targeted recovery, or target-region event enters candidate generation/ranking.

## Frozen quality and geometry
After blind exclusion require:
- nonempty unique `orbname` within year;
- finite `0 <= _sol < 360`;
- finite `0 <= _ra_t < 360`;
- finite `-90 <= _dc_t <= 90`;
- finite `5 < _vg < 75 km/s`.

Convert `_ra_t,_dc_t` through the exact frozen support-code equatorial-to-ecliptic transform and define Sun-centered longitude `wrap180(ecliptic_lon - _sol)`.

Candidate geometry contains only event id, year, solar longitude, Sun-centered ecliptic longitude, ecliptic latitude, and Vg.

## Frozen density normalization
Unchanged from the SAAMER external protocols:
- 36 fixed 10° solar-longitude bins/year;
- retain at most **10,000** eligible events per bin;
- if a bin exceeds 10,000, retain the 10,000 smallest SHA-256 hashes of `UKMON|year|YYYYMMDD|orbname`;
- the hash contains no scientific value;
- no alternate density cap is evaluated.

## Frozen v6 discovery architecture
Unchanged from passed v6:
- fixed4 geometry/scales;
- 64-neighbor first shortlist and 128-neighbor exact audit;
- one anchored quartet per anchor;
- identical-quartet consolidation;
- minimum anchor multiplicity 2;
- no empirical/null score threshold;
- top 512 quartets per bin by frozen anchor-count / quartet-score / identifier order;
- components require >=4 events and >=2 retained quartets;
- cross-year family link radius 1.5;
- recurrent family must span both 2024 and 2025;
- deterministic 128-event local episode per family/year;
- primary `M=(multi-anchor-v3-energy / Brown-peak)^2`;
- primary rank: worst-year M descending, geometric-mean M descending, family id;
- comparators: label-free persistence, Brown minimum-year score, total-v3 minimum-year score;
- no multiplicity p-value, RRF, threshold search, density search, cap search, link-radius search, weight search, or endpoint search.

## Frozen post-ranking orbital corroboration
Only after all rankings are frozen, re-read the already-downloaded daily summary payloads and interpret `_q,_e,_incl,_peri,_node` for recurrent-family events only.

Use the exact frozen Southworth–Hawkins implementation with `D_SH < 0.05`.

A family is orbitally corroborated iff its largest `D_SH<0.05` single-link connected component:
- contains >=4 events from 2024;
- contains >=4 events from 2025;
- contains at least 50% of the full discovery-family events.

Orbital validation cannot alter, merge, split, remove, or rerank a discovery family.

## Frozen endpoints
Let `N` be recurrent families, `Q` orbitally corroborated families, and `K=min(100,N)`.

For multiplicity, persistence, Brown, and total-v3 report:
- top-K corroborated count/fraction;
- median corroborated-family rank;
- MRR;
- one-sided hypergeometric enrichment p-value.

### Integrity / power gates — all required
1. exact frozen prerequisite artifacts/source blobs;
2. no UKMON year outside 2024/2025 is queried by the external runner;
3. all 731 calendar dates are attempted under the frozen daily/fallback transport rule;
4. target interval is removed before radiant/speed/orbit interpretation;
5. zero source-label use;
6. orbital elements interpreted only after ranking freeze;
7. exact 10,000/bin identity-hash normalization;
8. >=24 scannable bins/year;
9. zero 64→128 shortlist mismatches after reconciliation;
10. every recurrent family spans both years;
11. every local episode exactly 128 events;
12. Brown-equivalence error <=1e-10;
13. `N >= 100` recurrent families;
14. `Q >= 30` orbitally corroborated families.

### Scientific gates — identical to SAAMER external standard
1. multiplicity top-K corroborated count >= Brown top-K count + 1;
2. multiplicity top-K corroborated count >= `ceil(0.90 * persistence top-K count)`;
3. multiplicity top-K hypergeometric enrichment p <=0.05.

A powered all-gate pass is `PASS_LABEL_FREE_V6_UKMON_2024_2025_EXTERNAL_VALIDATION`.
A powered scientific failure is `FAIL_LABEL_FREE_V6_UKMON_2024_2025_EXTERNAL_VALIDATION`.
An integrity or power failure is reported separately and does not authorize OrbitTrace reveal.

## Continuation
Only a powered pass authorizes freezing the final target-free GMN OrbitTrace discovery scan. No UKMON result may be used to lower these gates or alter v6 before that decision.
