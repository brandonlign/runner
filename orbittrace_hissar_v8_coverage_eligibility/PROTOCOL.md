# OrbitTrace v8 — Hissar 1968/1969 pre-access coverage eligibility

## Status
Frozen after the Hissar zero-data freshness adjudication and successful pre-scientific interface/documentation audit, and **before the first Hissar catalogue form submission or meteor-row access**.

This stage asks only whether Hissar 1968/1969 can possibly satisfy the already-frozen v8 per-year solar-longitude coverage gate. It does not inspect a meteor record and cannot alter v8.

## Immutable prerequisites
- promoted v8 protocol source blob `8b0a1dc8565a702af6188d42dcebe6b1b71002b6`;
- Hissar structure run `31228363398`;
- Hissar structure artifact `9012889079`;
- Hissar structure artifact ZIP SHA-256 `ab150ddcfd2b279c43efa4dfe53ec659ce9d65d9f5a58bcf84b5b4fe3cc56e11`;
- structure verdict `PASS_HISSAR_1968_1969_STRUCTURE_AUDIT`;
- no Hissar form submission, result endpoint, meteor record, scientific value, source label, or OrbitTrace target information accessed.

The structure audit established from the official Hissar documentation:
- 8,916 radio-meteor records;
- observing period **December 1968 to October 1969 and in December 1969**;
- J2000 geocentric RA/DEC, geocentric `Vg`, solar longitude `LS`, and required orbital fields exist.

## Frozen v8 coverage requirement
The promoted architecture retains the general integrity floor of **at least 24 scannable fixed 10° solar-longitude bins in each year**. This floor may not be lowered for Hissar.

Years retain their ordinary calendar-year meaning. No custom “observing year,” December-to-December remapping, overlap window, duplicated 1969 subset, or other panel redefinition is allowed after reserving Hissar 1968/1969.

## Conservative 1968 upper bound
Official metadata confines every possible 1968 Hissar meteor to December 1968. For an intentionally loose astronomical upper bound:

- Earth orbital eccentricity `e = 0.01671`;
- mean angular motion `n = 360 / 365.2422 deg/day`;
- the Keplerian maximum true-longitude rate occurs at perihelion and is below `1.1 deg/day`;
- even granting all 31 days of December, the total possible solar-longitude span is therefore `< 34.1°`.

A continuous interval shorter than 34.1° can intersect at most **5** fixed 10° bins, even with an adversarial bin-boundary alignment. The actual Hissar 1968 coverage can only be equal or smaller, and the 20°–55° blind exclusion can only reduce it further.

Thus the 1968 panel has a metadata-only absolute upper bound of 5 scannable bins, versus the frozen requirement of 24.

## Decision rule
- If the official structure artifact no longer establishes the fixed temporal span or no-science boundary, fail integrity.
- If the conservative 1968 maximum is `<24`, return `INCONCLUSIVE_V8_HISSAR_1968_1969_EXTERNAL_POWER_COVERAGE` and **do not submit the catalogue form**.
- Only if the conservative maximum were `>=24` could a separately frozen scientific protocol be prepared before first row access.

A coverage-inconclusive result is not a scientific failure of v8. It establishes that Hissar cannot provide the powered two-calendar-year external test under the already-frozen methodology.

## Continuation
No Hissar scientific query is authorized after an inconclusive coverage verdict. Do not redefine the year panels or lower the 24-bin floor. This result contributes to the final external-data-availability limitation synthesis while OrbitTrace remains blinded.
