# CAMSv3 independent-survey structural feasibility v2

Status: frozen before parser v2 downloads any archive. No data-column value, shower-label token, detector score, calibration window, scientific endpoint, SonotaCo 2024 value, or GhostStream value may be read.

## Prior authoritative result

PR #85 parser v1 remains killed. It verified all six official 2011–2016 archive hashes, ZIP integrity, row counts, delimiters, required geometry fields, zero malformed rows, and one identical 63-field header. Its sole failure was requiring the complete ZIP member path to equal the pinned CSV basename, while each archive stores that basename beneath a directory prefix.

## Sole parser-v2 correction

For each archive:

1. enumerate CSV members;
2. compare `PurePosixPath(member).name` to the exact pinned basename;
3. require exactly one matching member;
4. read that exact member.

No fuzzy matching, suffix matching, alternate archive, alternate year, manual attachment, path normalization beyond `PurePosixPath.name`, or scientific-value access is permitted.

## Frozen sources and gates

The exact 2011–2016 archive URLs, SHA-256 hashes, expected CSV basenames, row counts, UTF-8-SIG encoding, semicolon delimiter, required fields (`Yr`, `Mn`, `Dayy`, `LS`, `RA`, `DECL`, `Vg`), safe-path rule, CRC check, unique/nonempty-header rule, zero-malformed-row rule, and cross-year identical-header rule are unchanged from parser v1.

Exact parser-v2 source SHA-256: `86abef5e3d70972f47e90f78516b303e64c448cb553cf37919db7a0abc5f74b7`.

Every gate must pass. A complete pass establishes only that CAMSv3 is structurally usable for a separately frozen aggregate-only label/uncertainty audit. It does not authorize reading scientific values, building a detector benchmark, accessing confirmation data, or applying anything to GhostStream.

Any failed gate kills parser v2 and the CAMSv3 route without another parser revision.