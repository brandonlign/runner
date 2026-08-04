# Historical CAMS Database 2.0 single-line schema audit

Status: frozen before opening any `.1l` resource.

## Purpose

Determine from the exact official format specification whether the reduced one-line CAMS representation is technically capable of supporting the unchanged PR #38 detector, which requires solar longitude, geocentric radiant RA/DEC, geocentric speed, and a native established-shower label.

## Frozen source

- URL: `https://www.astro.sk/~ne/IAUMDC/PhV2016/formats.pdf`
- bytes: `62530`
- SHA-256: `2cb0f754a81fe62c41f2b106c1e82750a38f38725a459591111d084f210e1924`

Download only this document. Do not request any `.1l`, `.xlsx`, `.d15`, later California, BeNeLux, SonotaCo 2024, or CAMSv3 2016 data resource.

## Frozen extraction and gates

Extract text from the PDF and isolate the section headed `Reduced data: meteor in a single line` through the next section heading. Record only the parameter codes explicitly listed for the reduced format.

The interface passes only if the section explicitly includes all five required fields: `LS`, `RA`, `DEC`, `Vg`, and `Sh` (or unambiguous shower-number wording). No derivation of LS from date, inference of shower labels from geometry/orbits, or use of columns outside the reduced-format section is allowed.

A failure kills this exact `.1l` route without opening a meteor record. A pass would authorize only a separately frozen first-40,744-row aggregate label audit. All reserved panels remain untouched.
