# EFN TAP_SCHEMA quoted-table discovery repair

**Classification: engineering-only metadata repair; no EFN event access.**

Repaired schema-audit run `31833452288` successfully reached VizieR's TAP service but returned zero rows for the metadata predicate:

`TAP_SCHEMA.tables.table_name = 'J/A+A/667/A157/catalog'`

This occurred before any event-table query. The official VizieR catalogue page independently identifies the table as `J/A+A/667/A157/catalog`; the remaining issue is how that non-standard identifier is represented inside `TAP_SCHEMA` (VizieR commonly preserves quoted/non-standard identifiers there).

Authorized metadata-only repair:

1. query only `TAP_SCHEMA.tables` using `table_name LIKE '%A157%'`;
2. select the unique returned metadata row whose table name, after stripping surrounding double quotes, equals `J/A+A/667/A157/catalog`;
3. use the exact raw `table_name` string returned by TAP_SCHEMA to query `TAP_SCHEMA.columns`;
4. normalize surrounding quotes only for comparison of required column identifiers.

No event table may be selected by the discovery audit. No Stage-1/2/3 query shape, scientific source, field mapping, panel, threshold, evaluator, or gate changes.
