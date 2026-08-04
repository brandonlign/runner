# CAMSv3 independent-survey structural feasibility parser v2

Status: separately frozen after parser-v1 failed only exact full ZIP-member path equality. No data-column or label value was inspected in parser v1.

## Sole parser correction

For each pinned 2011–2016 CAMSv3 archive, require exactly one safe CSV member whose `PurePosixPath(member).name` equals the already pinned basename `iaumdcCAMSv3_<year>.csv`. Record the actual full path. No other source, hash, year, row count, delimiter, header, field, or gate changes.

## Preserved frozen gates

- exact six archive URLs and SHA-256 hashes from parser v1;
- ZIP CRC and safe paths;
- exactly one basename-matching CSV member;
- UTF-8-SIG and semicolon parsing;
- pinned row count for every year and zero malformed rows;
- unique nonempty header containing exact fields `Yr`, `Mn`, `Dayy`, `LS`, `RA`, `DECL`, `Vg`;
- identical full header across all six years;
- no data-column value, shower-label token, detector score, calibration window, SonotaCo 2024 value, or GhostStream value read.

Every gate must pass. A pass authorizes only a separately frozen aggregate-only native-label audit using candidate fields predeclared from the structural header. A failure kills CAMSv3 as the next external-validation route under parser v2.
