# SonotaCo 2024 confirmation feasibility: parser-v1 result

Runner workflow `30876671903` completed the frozen data-only audit and preserved artifact `8879768860`, digest `sha256:95c172bb8b6ae2403e285955504f982882a85b5f83c23cd635e5fc841b301bf4`.

## Structural result

The official archive and intended annual member were successfully recovered:

- archive URL: `https://www.astro.sk/iaumdcDB/public/data/SNMv3/024a.zip`;
- archive SHA-256: `409bb958c6f114e542d818e7c4fcf7a58d89b2fb33090a442c8087bdcaa1540f`;
- selected member: `024a/_U2_20240101_S.csv`;
- member SHA-256: `0f25a0f9ea174c2b99915f48a61b35e35e3cde7f3117d82d4e05f8c4112acb00`;
- records: **38,793**;
- reported header fields: **46**;
- encoding / delimiter: `utf-8-sig` / comma;
- ZIP safety, CRC, source, member, row-count, encoding, delimiter, and uncertainty-header gates all passed.

## Frozen parser-v1 failures

Three gates failed:

- `header_at_least_40_unique_nonempty_fields`;
- `no_malformed_rows`;
- `required_geometry_and_label_headers`.

The aggregate structural evidence identifies two deterministic parser-interface mismatches:

1. the official header contains one final blank field, while all 38,793 data rows omit that trailing empty cell, causing the exact-width parser to mark every row malformed;
2. required fields are present with unit-bearing normalized names such as `soldeg`, `radeg`, `dedeg`, and `vgkms`, while parser v1 accepted only unit-free exact names.

No 2024 data-column value, shower-label token, label frequency, feature distribution, shower support, candidate score, comparator, or scientific endpoint was inspected.

Verdict: **`KILL_SONOTACO_2024_CONFIRMATION_PARSER_V1`**.

This run is not relabelled as a pass. It authorizes only a separately frozen parser-v2 feasibility test that changes exactly the two structural rules above while preserving the source URL, annual member name, row-count limits, encodings, delimiters, required scientific fields, no-value boundary, and all continuation restrictions. Keep this PR closed, draft, and unmerged.