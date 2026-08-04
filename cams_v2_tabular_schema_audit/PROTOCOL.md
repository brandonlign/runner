# Historical CAMS Database 2.0 XLSX schema-only audit

Status: frozen after PR #100 passed tabular structural feasibility and before any meteor row or label value is read.

## Sources

- California workbook URL `https://www.astro.sk/~ne/IAUMDC/PhV2016/CAMS_California_v2.xlsx`, 29,150,990 bytes, SHA-256 `3b4daf3dd5d20f99d250c872490393e020cd29dd5a17741c5c88b1678ca83ba4`.
- BeNeLux workbook URL `https://www.astro.sk/~ne/IAUMDC/PhV2016/CAMS_BeNeLux_v2.xlsx`, 287,061 bytes, SHA-256 `e35725616b966ba7956d6e60b22a8e3648db6d2e5eb7ea1865396a3da495c1a9`.

## Frozen schema boundary

For each exact workbook:

1. verify hash, ZIP CRC, and exact single worksheet member `xl/worksheets/sheet1.xml`;
2. stream `sheet1.xml` only until the closing tag of worksheet row 1, then stop without requesting row 2;
3. require row 1 to contain only textual header cells, with no formula and no numeric/date value;
4. if row-1 cells reference `xl/sharedStrings.xml`, require referenced indices to be exactly contiguous from 0 through the maximum referenced index; stream shared strings only through that maximum index and stop immediately;
5. emit the resolved row-1 header strings and normalized forms, sheet name, cell references, and source hashes only;
6. do not inspect workbook properties, later worksheet rows, unreferenced shared strings, styles, `.1l` files, `formats.pdf`, `.d15` data, or any meteor/label value.

Header normalization is Unicode NFKC, trim, lowercase, and removal of non-alphanumeric characters.

## Frozen field semantics

The schema passes only if both workbooks have identical normalized headers and expose exactly one match in each required family:

- solar phase: `ls` or `solarlongitude`;
- radiant longitude/right ascension: `ra`, `rightascension`, or `radiant right ascension` after normalization;
- radiant latitude/declination: `dec`, `declination`, or `radiant declination` after normalization;
- geocentric speed: `vg`, `geocentricspeed`, or `geocentricvelocity`;
- native shower label: exact normalized `sh` or `showernumber`.

The native-label field must be explicitly present in the header. No adjacent column, inferred field, position-based alias, token inspection, or geometry-derived classification is allowed.

## Frozen continuation gates

Every gate must pass: exact hashes; row 1 only; no row 2 request; contiguous header shared strings only; identical schemas; unique required geometry fields; unique explicit native shower-label field; and all reserved panels untouched.

A pass authorizes only a separately frozen aggregate-only audit of the first 40,744 California worksheet data rows. Before that audit, the exact row/column parser, year and phase columns, blind exclusion, label syntax, record boundary, support gates, and reserved later-row/BeNeLux boundary must be frozen. A failure kills this exact XLSX route.
