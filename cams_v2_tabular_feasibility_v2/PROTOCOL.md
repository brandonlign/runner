# Historical CAMS Database 2.0 tabular structural feasibility v2

Status: separately frozen after parser v1 failed before resource download because it guessed `document.pdf`. PR #99 then identified the exact official target `formats.pdf` on both archive pages without following it.

Parser v2 changes only the documentation basename to `formats.pdf`. It follows exact hrefs on both official pages for `CAMS_California_v2.xlsx`, `CAMS_BeNeLux_v2.xlsx`, `CAMS_California_v2.1l`, `CAMS_BeNeLux_v2.1l`, `CAMS_by_date_v2.1l`, and `formats.pdf`.

Require HTTP success, hashes, byte identity across Version 2016/2020, valid XLSX ZIP CRC/safe paths/OOXML markers, nonempty `.1l` bytes, and PDF magic. Record only hashes, sizes, content types, and XLSX central-directory member names/sizes. Do not open XML members, cells, `.1l` text, PDF pages, `.d15` records, or any meteor/label value.

Every gate must pass. A pass authorizes only a separately frozen schema-only audit that stops before the first meteor row and predeclares an explicit native shower-label field. A failure kills this exact tabular route. Reserved later California records, all BeNeLux meteor values, SonotaCo 2024, and CAMSv3 2016 remain untouched.
