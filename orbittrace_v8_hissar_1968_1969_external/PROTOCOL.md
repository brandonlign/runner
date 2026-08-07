# OrbitTrace pooled-year-centroid v8 — Hissar 1968/1969 external validation

## Status
Frozen before the first Hissar catalogue form submission and before any Hissar meteor-row scientific value is read.

**Pre-access coverage-integrity amendment.** The first protocol commit accidentally omitted the already-frozen external coverage gate `MIN_SCANNABLE_BINS=24` per year even though the authoritative v6/AMOR/SAAMER implementation retains it. This amendment restores that exact pre-existing gate before any Hissar catalogue form submission or meteor-row access. No Hissar scientific value has been read, and no detector, family, scoring, ranking, power, or post-ranking criterion changes.

This is a one-shot external validation of the already-promoted **v8 pooled-year-centroid label-free sparse-support multiplicity** method. It is not a development grid. Nothing in the detector, family construction, pooling, scoring, ranking, power floors, coverage floors, or post-ranking validation rule may be changed after the first Hissar scientific row is returned.

## Immutable prerequisites
### Promoted v8
- development run `31217916558`;
- artifact `9009728299`, ZIP SHA-256 `88d2d607e05d027015c338f7e23b64a6195e55ae24f1b2ac745f5e9bc6df599e`;
- verdict `PASS_POOLED_YEAR_CENTROID_V8_DEVELOPMENT`;
- 226 recurrent development families;
- multiplicity/Brown/persistence recovery@100 = 58/55/59;
- exact v6 connected recurrent-family graph;
- exact v8 pooled same-year unique-event centroid statistic: circular mean solar longitude, circular mean Sun-centered ecliptic longitude, median ecliptic latitude, median Vg.

Frozen source guards:
- `orbittrace_pooled_year_centroid_v8/PROTOCOL.md` blob `8b0a1dc8565a702af6188d42dcebe6b1b71002b6`;
- `orbittrace_pooled_year_centroid_v8/run_development.py` blob `f248df78e1258b132b41aecca6a985a5eb782654`;
- `orbittrace_label_free_sparse_support_v6/run_development.py` blob `7995fc6b75d1fd51eb4b304ace39db28a5a1e876`;
- frozen fixed4 wrapper source SHA-256 `fa18a19c08c6824c66606cbd92095dc3605cbcc30f17a468c9e525e7c6ff4a62`;
- frozen blind-catalogue source SHA-256 `48434df612f790924e6efce45b6b8d4de1401880f398994bc58eef2fce0987e5`.

### Hissar freshness and structure
Freshness adjudication:
- run `31227612252`, artifact `9012644763`, ZIP SHA-256 `31f50436e7dfad5a2768d12e559942a1ee5dd0f96816d71226151ed381701598`;
- verdict `PASS_HISSAR_1968_1969_ZERO_DATA_FRESHNESS_ADJUDICATION`;
- conservative raw FAIL remains preserved; exactly one metadata-only explicit-nonuse hit; zero additional hits forgiven.

Pre-scientific interface audit:
- first run `31227806541` failed before any network access because `pdftotext` was absent; preserve it;
- corrected run `31227873768`, artifact `9012730620`, ZIP SHA-256 `5bd31024a86067ebd4d1258ce769602bd98064b9558bbebe75385d45c0f118b3`;
- verdict `PASS_HISSAR_1968_1969_STRUCTURE_AUDIT`;
- official page/documentation hashes were recorded;
- no form was submitted and no Hissar event row was accessed.

The structure audit froze the exact public form:
- method: `POST`;
- action: `https://ceres.ta3.sk/iaumdcdb/home/catalog/radio`;
- Hissar selector: `u_database[]=iaumdcHIS1`;
- time controls: `from_yr`, `to_yr`, `from_dt`, `to_dt`;
- selected-column control: `u_column[]`;
- literal form values are `Dayy` for day and `DECL` for declination.

Official Hissar documentation fixes:
- 8,916 radio-meteor records;
- observations from 1968-12-12 through 1969-12-24, with the 1968 panel therefore prospectively much shorter;
- positional parameters referred to equinox 2000.0;
- `LS` solar longitude;
- `RA`,`DEC` geocentric radiant;
- `Vg` geocentric speed;
- `q`,`e`,`i,arg,nod` orbital elements;
- unique IAU MDC identification code `#IC`.

## Exact first and only catalogue request
Submit exactly one POST to the frozen radio-page action with form fields:
- `u_database[]=iaumdcHIS1`;
- `from_yr=1968`;
- `to_yr=1969`;
- `from_dt=` empty;
- `to_dt=` empty;
- repeated `u_column[]` values, in this exact order:
  `DB, IC, Yr, Mn, Dayy, LS, RA, DECL, Vg, q, e, i, arg, nod`.

No alternative column set, date range, endpoint, format, query retry with changed parameters, or result/download link may be tried after scientific access. Ordinary transport retries of the identical POST are allowed only for connection/5xx failures and must send byte-for-byte equivalent form fields.

## Frozen response parser
The response must be HTML. Parse tables generically without interpreting numeric cell values. Find exactly one table with a header containing the requested logical fields after these fixed aliases only:
- `#IC` or `IC` -> `IC`;
- `Dayy` or `Day` -> `Day`;
- `DECL` or `DEC` -> `DEC`;
- case-insensitive exact matching for all other requested fields.

No fuzzy column inference is allowed. Every accepted data row must have exactly one cell for each requested logical field. The response must yield exactly **8,916 unique nonempty IC values**; otherwise the verdict is `FAIL_V8_HISSAR_EXTERNAL_INTEGRITY` and no parser repair may be learned from row values.

No `Sh`/source-label field is requested or used.

## Blindness and event-quality ordering
For each structurally accepted row:
1. retain cells as uninterpreted strings;
2. **interpret `LS` first and no other scientific numeric value first**;
3. require finite `0 <= LS < 360`;
4. immediately discard the row if `20.0 <= LS <= 55.0`, inclusive;
5. only after that exclusion interpret identity/date:
   - nonempty unique `IC`;
   - integer `Yr` in `{1968,1969}`;
   - integer `Mn` in `1..12`;
   - finite `Day` with `1 <= Day < 32`;
6. only then interpret discovery geometry:
   - finite `0 <= RA < 360`;
   - finite `-90 <= DEC <= 90`;
   - finite `5 < Vg < 75 km/s`;
7. transform the J2000 geocentric equatorial radiant with the exact frozen fixed4 `equatorial_to_ecliptic` conversion;
8. define Sun-centered radiant longitude as `wrap180(ecliptic_longitude - LS)`;
9. discovery data contain only event ID, year, LS, Sun-centered ecliptic longitude, ecliptic latitude, and Vg.

The raw orbital cells `q,e,i,arg,nod` may be retained as uninterpreted strings keyed by IC, but may not be converted to numbers until **after all families and all four rankings are frozen and SHA-256 digested**.

No OrbitTrace coordinate, member, activity value, target identity, or event inside the excluded interval may enter any proposal/family/ranking calculation or output.

## Frozen density normalization
Reuse the already-frozen external normalization unchanged:
- 36 fixed 10° LS bins per year;
- after blindness and geometry-quality gates, retain at most **10,000 events per bin**;
- if a bin exceeds 10,000, retain the 10,000 smallest SHA-256 hashes of `HISSAR|IC`;
- no scientific value enters the hash;
- no cap alternative is evaluated.

Because the official catalogue contains only 8,916 total records, this cap is prospectively known not to bind, but the exact existing rule is still executed and audited rather than removed.

## Exact v8 proposal/family/pooling/multiplicity implementation
No Hissar-specific detector adaptation is permitted. Reuse the frozen v6/v8 stack exactly:
- fixed 4° candidate scale;
- 36 fixed 10° solar-longitude bins;
- anchor pool ±15°;
- 64-neighbor first shortlist and 128-neighbor audit;
- one anchored quartet per anchor;
- identical-quartet consolidation;
- minimum anchor multiplicity 2;
- no empirical/null score threshold;
- top 512 quartets per bin by the frozen ordering;
- within-year component: at least 4 events and at least 2 retained quartets;
- cross-year family link radius exactly 1.5 in the frozen geometry;
- recurrent family must contain both 1968 and 1969;
- multiple same-year components are allowed exactly as v8 specifies;
- per-family-year centroid is recomputed from the union of unique events in that family/year using the exact v8 pooled statistic;
- deterministic local episode size exactly 128;
- multiplicity score exactly `M=(multi-anchor-v3-energy / Brown-peak)^2`;
- primary ranking: worst-year multiplicity descending, then two-year geometric-mean multiplicity descending, then stable family ID;
- comparator rankings: Brown, total-v3, and label-free structural persistence;
- no threshold, radius, quartet cap, episode size, pooling statistic, multiplicity formula, ranking weight, RRF, density-cap, or endpoint search.

## Frozen matched-coverage integrity gate
Restore and enforce the exact existing external-application coverage floor from the frozen v6/AMOR/SAAMER evaluator:
- `MIN_SCANNABLE_BINS = 24` **for each year**;
- there are exactly 36 fixed 10° solar-longitude bins;
- a bin is scannable only when its own 10° anchor bin contains at least the frozen minimum number of anchors and its frozen ±15° candidate pool contains at least the 128-neighbor audit requirement;
- the count is evaluated after the blind interval and event-quality/density-normalization steps, exactly as in the frozen external evaluator;
- if either 1968 or 1969 has fewer than 24 scannable bins, the panel fails matched external-coverage integrity and must not be interpreted as a powered v8 scientific test.

This is not a Hissar-specific new floor. It is the pre-existing external integrity rule accidentally omitted from the first Hissar protocol commit and restored before any Hissar catalogue submission. It must not be relaxed because Hissar 1968 has short documented coverage.

## Frozen post-ranking orbital corroboration
Only after every ranking is frozen:
- convert `q,e,i,arg,nod` only for events belonging to recurrent families;
- require finite physical orbit values: `q>0`, `e>=0`, `0<=i<=180`, with `arg,nod` wrapped to `[0,360)`;
- use the already-frozen Southworth-Hawkins `D_SH` comparator;
- threshold exactly `D_SH < 0.05`;
- a family is orbitally corroborated only under the already-frozen rule requiring at least 4 valid orbital members in **each** year and an orbital coherent component containing at least 50% of the family events (the frozen SAAMER external evaluator implementation is authoritative for this calculation).

Orbital elements cannot change family formation, pooled centroids, scoring, or ranking.

## Frozen external power criteria
Let:
- `N` = number of recurrent v8 families spanning both years;
- `Q` = number of those families satisfying the frozen orbital corroboration rule.

A test is powered only if both:
- `N >= 100`;
- `Q >= 30`.

These floors are fixed before Hissar access and **must not be lowered**, including because the 1968 observing interval is short.

## Frozen scientific criterion if powered
Let `K=min(100,N)` and define corroborated@K for each ranking.

The Hissar external test passes scientifically only if all three are true:
1. multiplicity corroborated@K >= Brown corroborated@K + 1;
2. multiplicity corroborated@K >= `ceil(0.90 * persistence corroborated@K)`;
3. multiplicity hypergeometric enrichment p-value <= 0.05 under the same frozen evaluator.

## Verdict rules
Apply in this order:
1. `FAIL_V8_HISSAR_EXTERNAL_INTEGRITY` if any frozen source/artifact/interface/parser/blindness/ranking-order gate fails **or either year has fewer than 24 scannable bins under the frozen external coverage rule**;
2. `INCONCLUSIVE_V8_HISSAR_EXTERNAL_POWER` if integrity passes but `N < 100` or `Q < 30`;
3. `PASS_V8_HISSAR_EXTERNAL_VALIDATION` if powered and all three scientific gates pass;
4. `FAIL_V8_HISSAR_EXTERNAL_VALIDATION` if powered but one or more scientific gates fail.

A coverage-integrity failure is a panel/data-availability limitation, not evidence that v8 performs poorly. A power-inconclusive result is not a v8 failure. A powered scientific fail is a genuine external failure and must be preserved without tuning v8 to Hissar.

## Claim boundary
This protocol remains frozen before any Hissar scientific-row access. It does not reveal or inspect OrbitTrace target information. The 20°–55° interval would be removed before radiant, speed, orbit, or identity/date scientific interpretation beyond LS itself. The objective is an honest powered external verdict; no result is forced. If official pre-scientific metadata already proves that the immutable matched-coverage gate is impossible, Hissar must be rejected without burning the fresh event panel.
