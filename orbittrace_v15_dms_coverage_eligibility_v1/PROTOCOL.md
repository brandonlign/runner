# OrbitTrace v15 DMS 1991–1998 coverage-only external eligibility audit

## Purpose

Determine whether the currently published Dutch Meteor Society video catalogue `DMS1991-1998` can supply a scientifically usable **prospective two-year external panel** for the already-frozen v15 methodology.

This audit is deliberately pre-scientific. It may inspect only catalogue identity plus event year/date and solar longitude needed to quantify temporal/annual coverage and to enforce the sealed target interval. It must not inspect or emit radiant coordinates, speed, orbital elements, shower labels, family structure, detector scores, known-shower matches, or any OrbitTrace target information.

The result of this audit can only be:

- `ELIGIBLE_DMS_PAIR_RESERVED_PRE_SCIENCE`, with one deterministic consecutive-year pair permanently reserved; or
- `INELIGIBLE_DMS_NO_ADEQUATE_CONSECUTIVE_PAIR`, ending the DMS route without scientific use.

No alternate DMS pair may be chosen after a scientific DMS run begins.

## Provenance known before access

Official IAU MDC Version 2026 metadata lists DMS as a distinct video catalogue containing 908 orbits spanning 1991–1998. Repository-history searches before this protocol found no prior OrbitTrace PR or code reference to `DMS1991-1998`, `DMSVID98`, or the Dutch Meteor Society video catalogue. EDMOND is excluded because it has prior OrbitTrace supplementary/scientific use.

The audit must retrieve only the official IAU MDC `DMS1991-1998` archive linked from the current Video Catalogs page. The workflow discovers the archive URL by anchor text from that official page; no alternate mirror or search-result dataset is allowed.

## Allowed event fields

Only these concepts may be accessed from DMS rows:

- year (`Yr` or an exact case-insensitive equivalent);
- month (`Mn`) and day (`Day`) only for structural/date validation;
- solar longitude (`LS` or an exact case-insensitive equivalent).

Catalogue/source identity fields may be read only if needed to prove that every row belongs to DMS, but their values must not be emitted.

All other columns are forbidden for this audit, including RA, DEC, Vg/Vi/Vh, q, e, i, argument of perihelion, node, shower/classification fields, and uncertainties in those scientific quantities.

The audit output must contain only aggregate coverage statistics, archive/member hashes, schema confirmation for the four allowed fields, the deterministic pair decision, and firewall booleans.

## Frozen structural parser rule

The first two live execution attempts established **only a structural fact** before any DMS event value was parsed: the official ZIP is reachable, but its data member does not expose a delimited `Yr/Mn/Day/LS` header in the initial preamble. No coverage statistic or DMS scientific value was obtained from those attempts.

The current official IAU MDC Video Catalogs page publicly defines the database parameter order beginning:

`DB, IC, Ano, Yr, Mn, Day, delta_Day, LS, ...`

Therefore the coverage parser is frozen to the following two-stage schema rule before any DMS coverage values are accepted:

1. **Named-header mode:** if exactly one header line resolves the four allowed concepts, use those named columns.
2. **Headerless official-order mode:** only if named-header mode finds no candidate, test delimited table members against the official parameter order above and interpret **only** zero-based positions `3,4,5,7` as `Yr,Mn,Day,LS`.

Headerless official-order mode is accepted only if exactly one member/delimiter combination passes all of these fail-closed structural checks using only the four allowed columns:

- at least 8 columns per nonblank row;
- constant row width across the parsed table;
- every parsed year is an integer in 1991–1998;
- every parsed month is an integer 1–12;
- every parsed day is finite and in `(0,32)`;
- every parsed solar longitude is finite;
- the number of parsed rows equals **908**, the already-public official DMS orbit count.

No value from any other column may be converted, compared, logged, hashed separately, or used to choose the delimiter/member. If more than one member/delimiter satisfies the allowed-column structural checks, fail closed rather than selecting one.

This parser repair changes no eligibility threshold, year/pair rule, sealed interval, or scientific permission.

## Sealed target interval

Solar longitude 20°–55° inclusive remains sealed. Rows in that interval are ignored immediately after LS parsing and before any coverage statistic is updated. The audit must not report how many rows were removed from the sealed interval or any statistic specific to that interval.

## Year eligibility gates

For each calendar year 1991–1998, using only target-excluded rows with finite year/date/LS:

1. at least **80** usable rows;
2. at least **12 distinct 10° solar-longitude bins** represented, using bins `[0,10), [10,20), ... [350,360)` after sealed-interval removal;
3. at least **3 distinct 90° solar-longitude quadrants** represented.

These thresholds are frozen before DMS event access. They are intended to reject campaign-like or highly seasonal years that cannot support an annual catalogue comparison, while remaining compatible with v15's preregistered low-cardinality validation down to nominal episode size 32.

A year failing any gate is ineligible. Its aggregate statistics may be reported; no radiant/orbit/shower value may be used to reconsider it.

## Consecutive-pair requirement

External recurrence must use two **consecutive** eligible years. Candidate pairs are `(1991,1992)` through `(1997,1998)` for which both years pass every year gate.

If no consecutive eligible pair exists, DMS is permanently ineligible for this v15 external route.

If one or more pairs are eligible, reserve exactly one pair by the following deterministic label-free ordering:

1. maximize the smaller occupied-10°-bin count of the two years;
2. then maximize the smaller usable-row count;
3. then maximize the combined occupied-10°-bin count;
4. then maximize the combined usable-row count;
5. then choose the chronologically earliest pair.

No other DMS years may later replace the reserved pair because of method/comparator/truth outcomes.

## Firewall

During this coverage audit:

- v15 source/model/scorer must not run;
- Sugar/HDBSCAN or any other comparator must not run;
- known-shower mapping/truth must not be loaded;
- no target-containing search/reveal may occur;
- MAARSY must not be accessed;
- SonotaCo 2013/2014 must not be accessed;
- DMS scientific fields beyond year/date/LS must not be inspected or emitted.

If the archive/schema cannot be parsed using only the allowed fields and the frozen structural rule above, fail closed as an integrity/transport failure rather than broadening access.

## Authorization after a pass

`ELIGIBLE_DMS_PAIR_RESERVED_PRE_SCIENCE` authorizes only a subsequent **separately preregistered dormant v15 external runner** for that exact reserved DMS pair. Before any DMS scientific field is opened, the subsequent protocol must freeze:

- exact v15 implementation/source identities;
- exact external normalization and field mapping;
- comparator(s), parameters, seeds, and versions if a literature comparison is attempted;
- pairwise event universe rules;
- known-shower truth mapping;
- power/futility gates;
- output-before-truth ordering;
- target/MAARSY/SonotaCo firewalls.

A coverage pass is not an external-validation result.
