# Historical CAMS Database 2.0 single-line schema audit parser v2

Status: separately frozen after parser v1 selected the table-of-contents occurrence of the reduced-format heading. Parser v1 read no data resource and produced no authoritative schema result.

## Sole parser correction

Use the exact official `formats.pdf` source:

- URL: `https://www.astro.sk/~ne/IAUMDC/PhV2016/formats.pdf`
- bytes: `62530`
- SHA-256: `2cb0f754a81fe62c41f2b106c1e82750a38f38725a459591111d084f210e1924`

Extract all PDF text, select the **last** occurrence of `Reduced data: meteor in a single line`, and take the section from that heading through the next `Old IAU MDC format` heading. Require both boundaries and require the section to contain at least 100 characters. This is the only change from parser v1.

## Unchanged scientific gate

Record only parameter codes explicitly present in that actual reduced-format section. The interface passes only if all five required fields are explicit:

- `LS` or unambiguous solar-longitude wording;
- `RA` or unambiguous right-ascension wording;
- `DEC` or unambiguous declination wording;
- `Vg` or unambiguous geocentric-velocity wording;
- `Sh` or unambiguous shower-number wording.

No solar-longitude derivation from calendar date, no shower assignment from geometry or orbit, and no use of columns outside the reduced-format section are allowed.

Do not request any `.1l`, `.xlsx`, or `.d15` data resource. Do not read any meteor record, label value, later California row, BeNeLux value, SonotaCo 2024 value, or CAMSv3 2016 value.

A failure kills this exact `.1l` route. A pass would authorize only a separately frozen aggregate-only development audit. All reserved panels remain untouched.
