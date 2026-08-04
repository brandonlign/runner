# Historical CAMS Database 2.0 tabular-interface structural feasibility

Status: frozen before downloading any tabular resource.

## Purpose

The native `.d15` development partition passed all parser and background gates but contained no `Sh` field in any of its first 40,744 records. The official IAU MDC archive separately publishes Excel and reduced single-line representations. This gate determines whether those separately published resources and their format documentation remain retrievable and structurally stable enough to justify a source-schema audit.

This is not a repair of the killed `.d15` label formulation. It does not compare values across formats, inspect any meteor row, infer labels, or consume the reserved later-California/BeNeLux confirmation reservoir.

## Frozen official pages and resources

Use only exact hrefs exposed by both official pages:

- `https://www.astro.sk/~ne/IAUMDC/PhV2016/video.html`
- `https://www.astro.sk/~ne/IAUMDC/PhVR2020/video.html`

Require exactly one href by URL basename for each:

- `CAMS_California_v2.xlsx`
- `CAMS_BeNeLux_v2.xlsx`
- `CAMS_California_v2.1l`
- `CAMS_BeNeLux_v2.1l`
- `CAMS_by_date_v2.1l`
- `document.pdf`

No guessed path, mirror, alternate filename, suffix, or search result may be substituted. Resolve links only with `urljoin` against the final official page URL.

## Frozen structural audit

For every resource from each page:

1. require HTTP success and record final URL, byte count, content type, and SHA-256;
2. require byte identity between the Version 2016 and Version 2020 links for the same basename;
3. for each `.xlsx`, require valid ZIP structure, no CRC failure, safe member paths, exact Office Open XML workbook markers `[Content_Types].xml`, `xl/workbook.xml`, and at least one `xl/worksheets/sheet*.xml`; record only ZIP member names and compressed/uncompressed sizes;
4. do not open or decode any XML member, shared string, worksheet, relationship, property, or cell;
5. for each `.1l`, require nonempty bytes and record only byte count and hash; do not decode text, count lines, inspect delimiters, or read records;
6. for `document.pdf`, require `%PDF-` magic, nonempty bytes, and record only byte count and hash; do not parse text, metadata, tables, or pages;
7. do not access either `.d15` archive, SonotaCo 2024, CAMSv3 2016, later California records, or BeNeLux meteor values.

## Frozen continuation gates

Every gate must pass:

- both official pages are retrievable;
- each page exposes exactly one href for all six basenames;
- corresponding resources are byte-identical across the Version 2016 and Version 2020 pages;
- both workbooks pass ZIP/OOXML structural gates;
- all three `.1l` resources are nonempty;
- `document.pdf` has valid PDF magic;
- no workbook member content, worksheet cell, single-line record, PDF page, or meteor value is opened or decoded;
- all reserved survey panels remain untouched.

A pass authorizes only a separately frozen **schema-only** audit. That audit may inspect workbook sheet names, the first nonempty header row, the first non-record format-description lines of `.1l`, and the documentation pages needed to identify field semantics. It must stop before the first meteor data row and must predeclare what constitutes an explicit native shower-label field before reading any row value.

A failure kills this exact tabular-interface route. No alternate mirror, resource name, or archive page may be introduced after execution.
