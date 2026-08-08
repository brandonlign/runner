# MAARSY 2016–2024 RCS release — pre-access continuation

Frozen after Stage-0D documentation-only run `31231978803` / artifact `9014112794` and before any file byte from the separate Zenodo RCS release is downloaded.

## Why this continuation is scientifically allowed

The first public MAARSY package (RADAR DOI `10.22000/yk29t2gu0h4jhkjg`) was inspected only through metadata, container headers, and its exact author README. No nested scientific data ZIP was opened or listed. The README establishes that that package's HDF5 exposes only:

- `t0` — Unix UTC time;
- `h0` — initial detection altitude;
- `vg` — geocentric speed.

It contains no documented radiant/trajectory direction, so it is interface-incompatible with frozen v8 before scientific-value access.

A separately published MAARSY dataset was then identified from public metadata/literature:

- Zenodo record: `15553437`;
- DOI: `10.5281/zenodo.15553437`;
- title: `MAARSY 2016-2024 Meteor Head Echo RCS Dataset`;
- creators: Juha Vierinen and Håkon Silseth;
- declared file: `silseth_thesis_data.tar.gz`;
- public record size: approximately 21.5 GB;
- associated MAARSY literature states that the instrument/reduction yields 3-D meteor trajectories/vector velocities.

Repository freshness searches performed before this freeze found no prior indexed source hit, branch, or PR for `15553437`, `silseth_thesis_data`, or `Silseth` in OrbitTrace work.

This is an interface continuation within the newly selected MAARSY external opportunity, not a post-result rotation after v8 science: no MAARSY event value or v8 score has yet been seen.

## Stage 0E — Zenodo metadata only

Before any Zenodo file byte may be downloaded, Stage 0E may retrieve only public record metadata from the Zenodo record/API.

It may record:

- exact record/DOI/title/creators/license/description;
- exact filename, byte size, checksum, file identifier, and download/content URL as returned by Zenodo metadata;
- related identifiers and publication dates;
- metadata-declared formats/types.

It must not request the file content URL, preview scientific content, or use any event-level value.

## Stage 0F — structural probe only, only if separately frozen

If Stage 0E passes and metadata contains no internal file/schema inventory, a later separately frozen step may request only a bounded initial byte range from the exact hash/checksum-pinned `silseth_thesis_data.tar.gz`. That step may decompress only enough of the gzip stream to identify tar headers at the start of the archive. It may not interpret member payloads or continue through a scientific-data member merely to reach later headers.

Any documentation/source-code member payload access requires another freeze after its exact member name and size have been identified structurally.

## Frozen scientific requirements remain unchanged

No MAARSY release may alter v8. A usable release must provide, through documentation frozen before event access:

- timestamp sufficient for solar longitude;
- geocentric radiant direction or a documented 3-D geocentric velocity/trajectory vector with exact frame/sign conventions;
- geocentric speed;
- stable event identity;
- at least two usable years.

If eventually opened scientifically, the external evaluation retains the existing 20°–55° exclusion, >=24 scannable bins per year, exact fixed4/v6/v8 construction, 128-event episodes, `M=(v3/Brown)^2`, and powered floors `N>=100` and `Q>=30`. Orbital corroboration remains post-ranking only.

No OrbitTrace target information, final GMN Stage A/Stage B request, or target-containing GMN data may be accessed during this route.