# OrbitTrace v8 external validation — Harvard 1968–1969 recurrence-eligibility adjudication

## Status
Frozen after the Harvard zero-data freshness and pre-scientific structure audits, and **before `har6869.tab` has ever been opened or decompressed**.

This stage decides only whether the reserved Harvard product can instantiate v8's already-frozen cross-year recurrence semantics. It may use public catalogue/literature metadata and the structure-audit artifact; it may not inspect a scientific event record, radiant, speed, orbit value, source label, or OrbitTrace target information.

## Immutable prerequisites
- Harvard freshness run `31226182783`, artifact `9012163636`, verdict `PASS_HARVARD_1968_1969_REPO_SCIENTIFIC_FRESHNESS_AUDIT`, zero exposure hits.
- Harvard structure run `31226367693`, artifact `9012222394`, ZIP SHA-256 `b87b47593a60c1ce3ee8e568a0760e87ce9f7527fb5683d11171fb2af10f2f7c`, verdict `PASS_HARVARD_1968_1969_STRUCTURE_AUDIT`.
- Structure result declares exactly 19,818 records in `meteoroid.steel.orbits/data/har6869.tab` and records that the table member was not opened.
- Promoted v8 retains the passed-v6 connected-family semantics: an external recurrent family must span two genuine observing-year panels; changing that semantic or treating arbitrary calendar partitions as independent years is forbidden.

## Public metadata evidence fixed before event access
Use only the following already-identified public sources:
1. NASA PDS `Meteoroid Orbits V1.0` dataset profile (`EAR-A-VARGBDET-5-METORB-V1.0`), which identifies `har6869.tab` as the Harvard Radar Meteor Project 1968–1969 survey with 19,818 orbits.
2. NASA NTRS record `19760042403` for Sekanina (1976), which describes the stream search as using a **synoptic-year sample** of 19,698 radio meteors observed by the Havana Radio Meteor Project.
3. Galligan & Baggaley (2004), MNRAS 353, 422, which describes the HRMP **synoptic year study**, refers to the **synoptic year 1969 data set**, and states that close to 2×10^4 orbits were reduced during this synoptic year.

These sources are used only to adjudicate temporal panel structure. No event value is requested from any catalogue.

## Frozen recurrence requirement
For a two-panel v8 external test, each panel must represent a separate observing-year opportunity for the same annual meteor-stream population to recur. A file that is one continuous/synoptic observing year crossing a civil-year boundary does **not** become two independent recurrence panels by splitting records at January 1.

The following are prohibited:
- declaring calendar 1968 and calendar 1969 independent v8 years solely because both year numbers occur in a single synoptic-year program;
- selecting a split date after looking at event counts or solar-longitude coverage;
- mixing another Harvard/Steel survey into one side after Harvard values are seen;
- changing v8's two-year connected-family semantics.

## Decision rule
- `PASS_HARVARD_1968_1969_V8_RECURRENCE_ELIGIBILITY` only if the fixed public metadata establishes two repeated observing-year cycles suitable for annual recurrence.
- `FAIL_HARVARD_1968_1969_V8_RECURRENCE_ELIGIBILITY` if the product is one synoptic observing year spanning two civil years.
- Transport failure in retrieving public metadata is recorded separately and does not authorize scientific table access.

A FAIL is a **catalogue/interface incompatibility**, not a v8 scientific failure. It permanently blocks `har6869.tab` as the powered external panel for the promoted v8 and preserves its scientific event values unopened.

## Continuation after FAIL
If Harvard fails, perform one further zero-data catalogue search for the strongest genuinely unused coherent event-level survey with at least two repeated annual cycles. Do not lower `N >= 100` or `Q >= 30`, and do not cycle through scientific event tables.
