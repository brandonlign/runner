# OrbitTrace label-free sparse-support v6 — SAAMER 2020–2021 external validation

## Status

Frozen before the first scientific-value access to the SAAMER 2020 or 2021 meteor records.

This is a one-shot external validation of the already-passed label-free sparse-support multiplicity v6 architecture. It is not a new development grid and it may not be altered after SAAMER scientific values are read.

## Prerequisites frozen before external access

The run must verify all of the following before parsing a SAAMER meteor value:

- label-free v6 development run `31207688016` completed with verdict `PASS_LABEL_FREE_SPARSE_SUPPORT_V6_DEVELOPMENT`;
- v6 artifact `9005846925`, recorded ZIP digest `sha256:3c636b05cbfc88c6d6b2b8289b309412174b0025c305ae2f2532678927b2232b`;
- corrected full-history SAAMER freshness audit run `31206214148`, artifact `9004812755`, verdict `PASS_SAAMER_2020_2021_REPO_SCIENTIFIC_FRESHNESS_AUDIT`;
- the prior structure-only run `31206815422` read no scientific or shower-label values and established identical 16-token monthly DAT structure in both years. Its only failed requested-field condition was absence of a native `Sh` field, which label-free v6 does not require;
- immutable SAAMER archive SHA-256 values are:
  - 2020: `208938b6ed6c504d77eb96ae1d9a867f5957fcba48076fd1bac9632c24ff4933`;
  - 2021: `41a1aa7d568c98f273087fd2648cf6e9aa365373bf25b3db36d54ea987dd727c`;
- immutable schema legend SHA-256: `afb3f9f7a3b753234db8dbb7219d14095510265293485fc1e744f659a857f48b`;
- each meteor row has exactly the documented 16 fields:
  `IC, Yr, Mn, Day, LS, HM, RA, DEC, Vg, Vh, q, e, a, i, arg, nod`.

Official archive transport is frozen as:

- `https://ceres.ta3.sk/iaumdcdb/dataDBs/radio_offline/iaumdcSAAMER2020.zip`
- `https://ceres.ta3.sk/iaumdcdb/dataDBs/radio_offline/iaumdcSAAMER2021.zip`

## Blindness

- years: exactly 2020 and 2021;
- only January–December records belonging to their nominal year are used; the December 2019 member packaged with the 2020 archive is excluded;
- every event with solar longitude from 20.0° through 55.0° inclusive is discarded immediately after reading `LS` and before radiant/speed/orbit use;
- no OrbitTrace coordinates, members, activity measurements, HDBSCAN assignments, targeted-recovery result, or target-region event is available to this validation;
- SAAMER orbital elements `q,e,a,i,arg,nod` may not be interpreted until every candidate family and every ranking has been frozen.

## Frozen SAAMER geometry parser

For each nominal-year monthly DAT row after the blind exclusion:

- require exactly 16 whitespace-separated fields;
- require finite `LS`, `RA`, `DEC`, and `Vg`;
- `0 <= LS < 360`, `0 <= RA < 360`, `-90 <= DEC <= 90`, `5 < Vg < 75 km/s`;
- transform `RA,DEC` with the exact frozen support-code `equatorial_to_ecliptic` conversion;
- define Sun-centered radiant longitude as `wrap180(ecliptic_longitude - LS)`;
- candidate/ranking geometry contains only event id, year, solar longitude, Sun-centered ecliptic longitude, ecliptic latitude, and geocentric speed.

No orbital element enters candidate generation, family construction, multiplicity, Brown, v3, or persistence ranking.

## Frozen density normalization

SAAMER is roughly an order of magnitude denser than the GMN development corpus. To preserve the development search scale without looking at SAAMER value distributions:

- divide each year into the same 36 fixed 10° solar-longitude bins;
- after blindness and geometry-quality gates, retain at most **10,000 events per bin**;
- when a bin exceeds 10,000 events, retain the 10,000 smallest SHA-256 hashes of the fixed identity string `SAAMER|year|member|physical_row_number`;
- the hash contains no meteor scientific value;
- no density/cap alternative is evaluated.

The 10,000 cap was fixed from the already-exposed GMN v6 development density (pooled median roughly 8.8k anchors per scannable 10° bin) before any SAAMER scientific-value access.

## Frozen candidate and ranking architecture

Reuse label-free v6 unchanged:

- fixed4 geometry and scale;
- 64-neighbor first shortlist and 128-neighbor audit;
- one anchored quartet per anchor;
- identical-quartet consolidation;
- minimum anchor multiplicity 2;
- no empirical/null score threshold;
- top 512 quartets per bin by the frozen anchor-count / score / identifier ordering;
- within-year components: at least 4 events and at least 2 retained quartets;
- cross-year family link radius 1.5 under the frozen geometry;
- recurrent family must contain both years;
- deterministic 128-event local episode per family/year;
- primary multiplicity `M=(multi-anchor-v3-energy / Brown-peak)^2`;
- primary ranking: worst-year multiplicity descending, two-year geometric-mean multiplicity descending, family id;
- comparators: label-free structural persistence, Brown minimum-year score, total-v3 minimum-year score;
- no p-value for multiplicity, RRF, threshold search, cap search, link-radius search, weight search, density search, or endpoint search.

## Independent orbital corroboration — first allowed after rankings freeze

After all four rankings are frozen, re-read orbital elements only for events belonging to recurrent families.

Use the exact previously frozen Southworth–Hawkins implementation and its already-registered literature threshold `D_SH < 0.05` from `orbittrace_literature_comparison/literature_comparators.py` (blob `ab17e1205d72d8ab8361d8ba6cdad2e4c31fdcb2`).

For each recurrent family:

1. construct the `D_SH < 0.05` single-link graph using `q,e,i,arg,nod`;
2. find the largest connected component satisfying at least 4 events from 2020 and at least 4 events from 2021;
3. define orbital corroboration precision as component size / full family event count;
4. classify the family as **orbitally corroborated** iff such a component exists and precision is at least 0.50.

This orbital criterion is validation only. It cannot alter, merge, split, remove, or rerank any discovery family.

## Frozen external endpoints

Let `N` be recurrent families, `Q` the number orbitally corroborated in the entire frozen family universe, and `K=min(100,N)`.

For each ranking report:

- orbitally corroborated families in top K;
- top-K corroboration fraction;
- median rank and MRR of all orbitally corroborated families;
- one-sided hypergeometric enrichment p-value for observing at least that many corroborated families in K draws from N with Q successes.

### Integrity / power gates

All must pass:

1. exact prerequisite source/artifact/freshness guards;
2. exact archive and legend hashes;
3. no target-region event enters geometry or orbital validation;
4. no orbital element is interpreted before rankings freeze;
5. exactly the fixed 10,000-per-bin identity-hash normalization, with no alternate cap;
6. at least 24 nonempty/scannable bins per year;
7. zero 64→128 shortlist audit mismatches after reconciliation;
8. every recurrent family spans both years;
9. every local multiplicity episode has exactly 128 events;
10. Brown equivalence difference <=1e-10 everywhere;
11. at least 100 recurrent families;
12. at least 30 orbitally corroborated recurrent families in the full family universe.

### Scientific gates

All must pass:

1. multiplicity top-K orbital corroboration count >= Brown top-K count + 1;
2. multiplicity top-K orbital corroboration count >= `ceil(0.90 * label-free-persistence top-K count)`;
3. multiplicity top-K orbital-corroboration enrichment has one-sided hypergeometric `p <= 0.05`.

A powered pass is `PASS_LABEL_FREE_V6_SAAMER_EXTERNAL_VALIDATION`.
A powered scientific failure is `FAIL_LABEL_FREE_V6_SAAMER_EXTERNAL_VALIDATION`.
An integrity or power failure is reported separately and does not authorize target reveal.

## Continuation rule

Only a powered external pass authorizes a separately committed final target-free GMN discovery protocol. The final GMN protocol must freeze its candidate universe, rankings, and OrbitTrace reveal criterion before any previously excluded 20°–55° target-region event is opened.

A SAAMER pass does not itself establish that v6 beats every literature catalogue method. Catalogue-scale literature comparators must be run on a matched frozen benchmark separately.
