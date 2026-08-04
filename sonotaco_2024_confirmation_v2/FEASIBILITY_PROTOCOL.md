# SonotaCo 2024 untouched-confirmation feasibility v2

Status: frozen before parser v2 reopens the pinned 2024 archive. No 2024 data-column value, shower-label token, feature distribution, score, comparator, or scientific endpoint may be inspected.

## Prior authoritative result

PR #62 parser v1 remains killed. It recovered the exact official archive and annual CSV but failed because the public schema has one trailing blank header field omitted by every data row, and because required scientific columns carry units in their names. That run is not relabelled.

## Sole parser-v2 corrections

Parser v2 may change exactly two structural rules:

1. **Trailing-empty reconciliation.** Drop exactly one final header field only when its normalized name is empty and every nonempty data row has exactly one fewer cell than the raw header. No other width repair, padding, truncation, or malformed-row tolerance is allowed.
2. **Exact unit-bearing names.** Require the exact normalized headers `soldeg`, `radeg`, `dedeg`, `vgkms`, and `shower`; require all three measurement-uncertainty headers `rasddeg`, `desddeg`, and `vgsdkms`; and require all three match diagnostics `dr`, `dv`, and `dd`.

No alias table, fuzzy matching, suffix stripping, token inspection, or data-value access is permitted.

## Pinned source

- URL: `https://www.astro.sk/iaumdcDB/public/data/SNMv3/024a.zip`;
- annual member basename: `_U2_20240101_S.csv`;
- archive SHA-256: `409bb958c6f114e542d818e7c4fcf7a58d89b2fb33090a442c8087bdcaa1540f`;
- member SHA-256: `0f25a0f9ea174c2b99915f48a61b35e35e3cde7f3117d82d4e05f8c4112acb00`;
- permitted record-count interval remains 30,000 through 50,000;
- encoding order and delimiters are unchanged from parser v1.

## Frozen gates

Every gate must pass:

1. exact pinned archive hash;
2. ZIP CRC and safe paths;
3. exactly one required annual member;
4. exact pinned member hash;
5. record count within 30,000–50,000;
6. frozen encoding and delimiter;
7. the documented trailing-empty condition holds exactly;
8. effective header has at least 40 unique nonempty normalized fields;
9. zero malformed rows after the sole documented reconciliation;
10. all exact geometry and label headers are present;
11. all exact measurement-uncertainty headers are present;
12. all exact match-diagnostic headers are present.

## Continuation boundary

A complete pass reserves SonotaCo 2024 as an untouched structural confirmation source. It authorizes only a separately frozen SonotaCo 2025 survey-native development study. Any later 2024 scientific application must use the exact method, label-prefix rule, thresholds, folds, and gates frozen after 2025 development and before any 2024 label or value is read.

A failure kills parser v2 and the planned 2024 confirmation source. No further parser change, alternate year, mirror, row-count relaxation, or header substitution is authorized.