# Historical CAMS Database 2.0 reader-specification audit

Status: separately frozen after PR #93 passed the structural archive gate and before any meteor data member is opened.

## Purpose

Extract the exact record specification, field order, and any native shower-tag representation from the official `reading.f` source accompanying CAMS Database 2.0. This gate reads source code only. It does not download or open either meteor-data ZIP.

## Frozen source

- URL: `https://www.astro.sk/~ne/IAUMDC/PhV2016/reading.f`
- bytes: `9905`
- SHA-256: `437d9d8f7d68b824751954b51e2caaec69e379912bce3b924acf2292e89acb1c`

The same bytes were independently exposed by the IAU MDC Version 2020 page in PR #93.

## Frozen extraction

After exact byte/hash verification, preserve the unmodified reader source in the artifact and extract only source-code structure:

- physical line count and Fortran comment/noncomment counts;
- every `OPEN`, `READ`, `WRITE`, and `FORMAT` source statement, including fixed-form continuation lines;
- declaration statements and variable names;
- comment lines containing any of `shower`, `stream`, `IAU`, `Working List`, `tag`, or `classification`;
- literal file/member names and record-count constants;
- whether the source contains a native shower/stream variable and whether that variable participates in the data-record `READ` statement.

Do not execute the Fortran source. Do not fetch either data archive. Do not inspect or emit any meteor record, label value, geometry value, date, solar longitude, identifier, or detector score.

## Frozen continuation gates

Every gate must pass:

1. exact source byte count and SHA-256;
2. source is valid nonempty fixed/free-form Fortran text with at least one `READ` and one `FORMAT` statement;
3. a complete data-record `READ`/`FORMAT` interface can be identified from the source;
4. the source identifies at least the fields required for PR #38 transfer: date or solar longitude, radiant longitude/right ascension, radiant latitude/declination, and geocentric speed;
5. the source identifies a native shower/stream tag or number that is read from the data record;
6. neither CAMS data archive is requested;
7. SonotaCo 2024 and CAMSv3 2016 values remain unread.

A pass authorizes only a separately frozen aggregate-only parser/label-support audit. That later audit must pin both archive hashes and member names, implement the exact reader format, reserve a confirmation partition before opening records, remove solar longitude 20°–55° inclusive before label parsing or support counts, and emit no shower identities.

A failure kills the historical CAMS Database 2.0 native-label route. No alternative field interpretation or inferred geometry-based labels may be introduced after execution.
