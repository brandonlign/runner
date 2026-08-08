# OrbitTrace v8 — MAARSY 2016–2023 external pre-access protocol

## Status

Frozen after the terminal v8 external-validation synthesis returned `INCONCLUSIVE_V8_EXTERNAL_VALIDATION_NO_POWERED_PRISTINE_PANEL`, and before downloading or opening any MAARSY event-level data.

This is a genuinely new independent-dataset opportunity discovered from public publication/repository metadata after the exhausted prior panel sequence. Repository searches performed before this branch found no `MAARSY` branch, pull request, or indexed source hit in `brandonlign/runner`.

The Obninsk historical survey was investigated only through archive metadata/XML and **no `obninsk.tab` event row was ever opened**. Its metadata exposed an apparent-radiant / `Vinf` interface that would require survey-specific geocentric correction. MAARSY is selected instead at the pre-scientific stage because the public 2026 paper reports a much larger multi-year event universe and directly processed three-dimensional meteor trajectories plus geocentric velocity. No Obninsk scientific outcome was observed or used.

## Immutable promoted method

Use the already-promoted v8 pooled-year-centroid label-free sparse-support multiplicity method exactly as frozen at commit `c9d6c44704013ba0c9430100e98a29a56b453304`.

No density threshold, fixed4 proposal rule, component rule, family rule, family-link radius, centroid repair, episode size, multiplicity definition, ranking rule, orbital criterion, external power floor, or pass/fail rule may change because of MAARSY.

## Candidate fixed from public metadata only

Dataset/publication identifiers fixed before event access:

- survey/instrument: Middle Atmosphere Alomar Radar System (MAARSY), Andøya, Norway;
- public analysis period: 2016–2023;
- reported good-quality meteor-head-echo population: over 1.4 million events;
- publication: Huyghebaert et al., *Atmospheric Measurement Techniques* 19, 4277–4292 (2026), DOI `10.5194/amt-19-4277-2026`;
- cited data record: Huyghebaert and Vierinen (2026), DOI `10.22000/yk29t2gu0h4jhkjg`;
- publication-level interface statement: the analysis uses the three-dimensional trajectory and geocentric velocity of each meteor.

The public paper is used only for dataset size, years, instrument identity, and interface feasibility. No event-level MAARSY value has been inspected for this protocol.

## Stage 0A — DOI / repository metadata transport audit only

Before any dataset file may be downloaded:

1. resolve DOI `10.22000/yk29t2gu0h4jhkjg`;
2. retrieve only repository landing-page metadata and/or DataCite DOI metadata;
3. record resolved repository URL, title, creators, publication year, rights/license, file/resource names if exposed by metadata, declared sizes/checksums if exposed, and metadata/API URLs;
4. do not follow any event-data download URL;
5. do not inspect a preview containing event rows;
6. do not retrieve a file whose role cannot be established as metadata/documentation before download.

Stage 0A is transport/metadata only and cannot produce a scientific v8 result.

## Stage 0B — schema/documentation audit only

Only after Stage 0A identifies a documentation/schema resource may that resource be opened. Event-level files remain unopened.

Stage 0B passes only if documentation establishes an exact deterministic mapping, without fitting to MAARSY values, to all v8 geometry inputs:

- event timestamp sufficient to calculate solar longitude with a single pre-frozen astronomical transform;
- geocentric radiant direction, either directly as geocentric RA/Dec/ecliptic coordinates or as a three-dimensional geocentric trajectory/velocity vector with documented frame and sign convention;
- geocentric speed `Vg` directly, or the norm of the same documented geocentric velocity vector;
- stable event identity independent of scientific values;
- enough temporal metadata to partition events by calendar year.

If the public release contains geocentric speed but not enough trajectory/radiant information to derive a geocentric radiant without empirical fitting, the panel is interface-incompatible and no event file may be opened.

No orbital elements may be used to reconstruct detector-input radiants or speeds. Orbit information is reserved for the already-frozen post-ranking corroboration stage only.

## Stage 1 — row-level coverage/power eligibility

Only after a passed, source-hashed Stage-0B parser/transform freeze may an execution-only child open event rows.

Before any known-shower or orbit interpretation, require unchanged external-v8 gates:

- use only years/files explicitly frozen after documentation-only availability assessment, with at least two independent calendar years;
- remove solar longitude `20°–55°` before external scientific interpretation, matching prior external-validation blindness;
- use no source/shower labels in proposal generation, component construction, family formation, pooling, scoring, or ranking;
- at least 24 scannable fixed 10° solar-longitude bins in every selected year;
- exact fixed4 label-free proposal construction inherited by v8;
- exact v6 within-year components and cross-year connected-family semantics;
- family-link radius exactly `1.5`;
- exact v8 pooled same-year centroids;
- exact 128-event local episodes;
- multiplicity exactly `M=(multi-anchor-v3-energy/Brown-peak)^2`;
- powered external universe requires `N >= 100` recurrent families and `Q >= 30` orbitally corroborated families;
- orbital corroboration uses the already-frozen `D_SH < 0.05` rule only after the label-free family ranking is immutable.

A panel below either frozen power floor is `INCONCLUSIVE`, not a v8 failure and not a v8 pass. The floors may not be lowered.

## External pass consequence

Only a powered v8 external pass may satisfy the existing prerequisite for the separately frozen target-containing GMN Stage A discovery scan.

A MAARSY interface failure, underpowered result, or powered scientific failure does not authorize target reveal and does not permit retuning v8.

## Blinding / firewall

This route must not access:

- OrbitTrace coordinates, identity, canonical members, target-region event values, or withheld reference;
- the final GMN Stage A or Stage B execution requests;
- old target rank/member/coordinate artifacts as a design input.

At the time of this freeze, **only Stage 0A metadata transport is authorized**.