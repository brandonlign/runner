# MAARSY Stage 0B — metadata-description schema audit

Frozen after Stage-0A run `31231509041` / artifact `9013960107` and before any MAARSY dataset-content download.

The DOI landing response exposed one scientific dataset item (`application/x-tar`) and three machine-readable description resources. This stage may fetch only the following `rel=describedby` resources:

1. `https://www.radar-service.eu/radar/en/export/yk29t2gu0h4jhkjg/exportradarmetadata`
2. `https://www.radar-service.eu/radar/en/export/yk29t2gu0h4jhkjg/exportrocrate`
3. `https://www.radar-service.eu/radar/en/export/yk29t2gu0h4jhkjg/exportJsonld`

It may not request the `rel=item` archive URL or any URL learned from these descriptions unless a later protocol is frozen first.

Purpose: determine from repository metadata alone whether the public release exposes a file inventory, file roles, formats, variable names, schema/documentation resources, checksums, or other structural information sufficient to design an exact v8 input mapping before scientific-value access.

Allowed output is metadata structure and textual descriptions only. If any description embeds scientific event rows or arrays unexpectedly, the workflow must stop without parsing/summarizing those values and record an integrity stop.

No v8 scientific evaluation, event-data download, meteor-row access, power calculation, OrbitTrace target access, or GMN Stage A/Stage B execution is authorized.