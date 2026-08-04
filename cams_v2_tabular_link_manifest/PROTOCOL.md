# CAMS Database 2.0 tabular page-link manifest

Status: frozen after tabular parser v1 failed only because the documentation href was not named `document.pdf`, and before any tabular resource is downloaded.

Fetch only the official Version 2016 and Version 2020 `video.html` pages. Parse HTML anchors without following them. Require exactly one href by basename for each of the five fixed tabular resources: `CAMS_California_v2.xlsx`, `CAMS_BeNeLux_v2.xlsx`, `CAMS_California_v2.1l`, `CAMS_BeNeLux_v2.1l`, and `CAMS_by_date_v2.1l`.

Also require exactly one anchor on each page whose normalized visible text is `here`; record its href, resolved URL, and basename. Require the two pages to resolve that anchor to the same basename. This identifies the documentation target actually published after the sentence describing file formats without guessing a filename.

Do not request or follow any discovered resource URL. Do not open any workbook, single-line file, documentation file, `.d15` archive, meteor record, label, geometry, or reserved survey panel.

A pass authorizes a separately frozen tabular structural parser v2 using the exact manifested documentation basename. A failure kills this page-link discovery route.
