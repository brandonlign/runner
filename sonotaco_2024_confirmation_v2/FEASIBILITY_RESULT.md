# SonotaCo 2024 untouched-confirmation feasibility v2: authoritative pass

Runner workflow `30876923507` completed the separately frozen parser-v2 data-only gate. Artifact `8879852261` was preserved with digest `sha256:07c5d288f25b1a28ede2efcad48b71a0e5a91bc88071c6ec68edfb5db35eb840`.

All twelve frozen gates passed:

- exact pinned archive and annual-member hashes;
- ZIP CRC and safe paths;
- exactly one required annual member;
- 38,793 records within the predeclared range;
- frozen `utf-8-sig` and comma parsing;
- exact documented trailing-empty reconciliation: raw header 46 fields, every row 45 fields, effective header 45 fields;
- zero malformed rows after that sole reconciliation;
- at least 40 unique nonempty effective fields;
- exact unit-bearing geometry headers `soldeg`, `radeg`, `dedeg`, and `vgkms` plus `shower`;
- all three measurement-uncertainty headers;
- all three `dr/dv/dd` diagnostics.

Pinned evidence:

- archive SHA-256: `409bb958c6f114e542d818e7c4fcf7a58d89b2fb33090a442c8087bdcaa1540f`;
- annual member: `024a/_U2_20240101_S.csv`;
- member SHA-256: `0f25a0f9ea174c2b99915f48a61b35e35e3cde7f3117d82d4e05f8c4112acb00`;
- parser source SHA-256: `d3f9c99bb64b6458a8637bc308bc84ba9d00d83258fa1383a1d73a0865dd072b`.

Verdict: **`PASS_SONOTACO_2024_CONFIRMATION_FEASIBILITY_V2`**.

No 2024 data-column value, shower-label token or frequency, feature distribution, support count, detector score, comparator, or scientific endpoint was inspected. SonotaCo 2024 is now reserved as an untouched external-survey confirmation panel.

This pass authorizes only a separately frozen SonotaCo 2025 survey-native development study. A 2024 scientific run is permitted only if that study passes, and only with the exact method, label-prefix rule, thresholds, folds, and gates frozen before any 2024 value or label is read. Keep this PR closed, draft, and unmerged as the feasibility record.