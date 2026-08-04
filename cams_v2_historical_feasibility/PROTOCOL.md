# Historical CAMS Database 2.0 structural feasibility

Status: frozen before downloading either full CAMS data archive.

## Scientific purpose

The current IAU MDC CAMSv3 annual export is structurally valid but its `sh` column is empty for every 2011–2015 development row after the blinded interval is removed, so that exact native-label route is killed.

This separate gate tests the official historical **CAMS Database 2.0** archive described by the CAMS 2016 papers and the IAU MDC Version 2016/2020 archive pages. The papers state that extracted stream members were identified by IAU Working List stream number in Database 2.0. This gate asks only whether the advertised full archives and their reader specification remain retrievable and structurally stable.

It is not a detector test and reads no meteor-record value or shower-label value.

## Frozen official entry pages

- `https://www.astro.sk/~ne/IAUMDC/PhV2016/video.html`
- `https://www.astro.sk/~ne/IAUMDC/PhVR2020/video.html`

From each page, extract exact relative/absolute links by HTML `href` basename for:

- `CAMS_California_v2.zip`
- `CAMS_BeNeLux_v2.zip`
- `reading.f`

No guessed archive path is allowed. Each page must contain exactly one link for each basename. Resolve links only with RFC-compatible `urljoin` against the page URL.

## Frozen structural audit

For each resolved resource:

1. require HTTP success and record final URL, byte count, and SHA-256;
2. require the Version 2016 and Version 2020 links for the same basename to yield byte-identical resources;
3. for each ZIP, require valid ZIP structure, no CRC failure, safe member paths, at least one non-directory member, and record only member names and byte sizes;
4. for `reading.f`, require nonempty plain text containing case-insensitive tokens `CAMS`, `READ`, and at least one of `SHOWER` or `STREAM`; record only source hash, byte count, line count, and matched required-token booleans;
5. do not open or decode any meteor data member inside either ZIP beyond ZIP integrity verification;
6. do not read or emit any individual meteor value, shower label, geometry, score, solar longitude, or event identifier.

## Frozen continuation gates

Every gate must pass:

- both official pages are retrievable;
- each page exposes exactly one href for all three pinned basenames;
- corresponding 2016/2020 resources are byte-identical;
- both archives pass ZIP CRC and safe-path checks and contain nonempty data members;
- the reader source passes its required-token gate;
- no meteor data member is opened for content inspection;
- no SonotaCo 2024 or CAMSv3 2016 value is read.

A pass authorizes only a separately frozen parser/specification audit. That next audit may inspect `reading.f`, archive member formats, headers/tags, and aggregate label syntax, but must freeze its parser and remove solar longitude 20°–55° before any label support count. It may not use GhostStream values or infer labels from event geometry.

A failure kills this exact historical-source route. No alternate mirror, guessed path, filename, or page may be substituted after execution.
