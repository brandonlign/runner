# OrbitTrace v8 — Obninsk 1967/1968 external pre-access protocol

## Status

Frozen after the terminal v8 external-validation synthesis returned `INCONCLUSIVE_V8_EXTERNAL_VALIDATION_NO_POWERED_PRISTINE_PANEL` and before opening or parsing any Obninsk meteor-event row.

This is a genuinely new independent-dataset opportunity discovered from public NASA/PDS metadata after the exhausted prior panel sequence. It does not alter v8, lower a power floor, reuse OrbitTrace target information, or rotate within a previously failed survey after seeing its scientific outcome.

## Frozen method

Use the already-promoted v8 pooled-year-centroid label-free sparse-support multiplicity method exactly as frozen at commit `c9d6c44704013ba0c9430100e98a29a56b453304`.

No scientific constant, family rule, link radius, episode size, multiplicity definition, ranking rule, power floor, orbital corroboration criterion, or target boundary may be changed because of Obninsk.

## Candidate selected from metadata only

Authoritative public metadata source: NASA Planetary Data System data set `EAR-A-VARGBDET-5-METORB-V1.0` / PDS4 bundle `urn:nasa:pds:meteoroid.steel.orbits::1.0`.

Frozen candidate:

- survey: Obninsk radar survey;
- event file: `obninsk.tab`;
- observing years: 1967 and 1968 only;
- archive-reported total: 9,358 orbits;
- archive reports a common format containing orbit number, observation time, orbital elements, ecliptic longitude, radiant right ascension/declination, and derived velocity at infinity.

Selection rule fixed before event access: among newly identified surveys in this PDS archive that had no indexed prior OrbitTrace repository exposure, select the largest survey spanning at least two observing years. Harvard is excluded because the Harvard route was already part of the exhausted external sequence; Kharkov is single-year; Adelaide and Mogadisho are smaller. No event-level value from any candidate was inspected to make this choice.

## Stage 0 — repository freshness and archive-structure audit only

Before `obninsk.tab` may be opened:

1. prove no pre-existing repository branch, PR, or indexed source outside this pre-access branch contains `Obninsk` or `obninsk.tab`;
2. retrieve only the official PDS archive/container and documentation;
3. hash the downloaded archive bytes;
4. inspect only archive filenames, labels, format documentation, and schema definitions;
5. do not print, parse, sample, summarize, count by date, or otherwise inspect any `obninsk.tab` event row.

Stage 0 passes only if documentation establishes an exact deterministic path to all v8 geometry inputs without fitting to Obninsk values:

- event time or an explicitly documented solar-longitude field sufficient to derive solar longitude;
- geocentric radiant direction, either directly or by a deterministic documented coordinate conversion from the archived radiant fields;
- geocentric speed, either directly or by a physically exact documented conversion from the archived velocity field with all constants/conventions frozen before event access;
- stable event identity independent of scientific values.

If any mapping requires empirical calibration, data-dependent fitting, shower labels, target information, or an ambiguous convention that cannot be resolved from documentation alone, Obninsk fails pre-access compatibility and no event row may be opened.

## Stage 1 — coverage/power eligibility after a Stage-0 pass

Only after Stage 0 passes may an execution-only child access event rows. That child must use a frozen parser/transform created from documentation alone.

Before any known-shower or orbital-corrobation interpretation, require:

- exact years 1967 and 1968;
- existing v8 geometry-valid cuts only, translated mechanically to documented Obninsk fields;
- solar-longitude interval 20°–55° removed before any external scientific interpretation, matching prior external-validation blindness;
- no source/shower labels in proposal generation, family formation, pooling, scoring, or ranking;
- at least 24 scannable fixed 10° bins in each year;
- exact v6 connected-family semantics with v8 pooled same-year centroids;
- exact family-link radius 1.5;
- exact 128-event local episodes;
- exact multiplicity `M=(multi-anchor-v3-energy/Brown-peak)^2`;
- powered external universe requires `N >= 100` recurrent families and `Q >= 30` orbitally corroborated families;
- `D_SH < 0.05` may be interpreted only after the label-free family ranking is frozen.

A panel below either power floor is `INCONCLUSIVE`, not a failure and not a pass. The floors may not be lowered.

## Authorization consequence

Only a powered v8 external **pass** may satisfy the already-frozen prerequisite for the final target-containing GMN Stage A discovery scan.

An Obninsk incompatibility, underpowered result, or scientific failure does not authorize target reveal, does not authorize a successor unless the existing successor rule is independently satisfied, and does not permit retuning v8.

## Blinding

This branch must not access:

- OrbitTrace coordinates, identity, canonical members, target-region event values, or withheld reference;
- the final GMN Stage A/Stage B workflows;
- any old target rank as a tuning objective.

The only permitted current execution is Stage 0 archive/documentation/freshness auditing.