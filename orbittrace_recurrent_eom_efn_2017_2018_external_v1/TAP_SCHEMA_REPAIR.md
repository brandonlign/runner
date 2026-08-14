# EFN TAP_SCHEMA audit repair — metadata ordering only

**Classification: engineering-only no-result. No EFN event table was queried.**

First schema-audit run `31833219047` passed all frozen source pins and successfully executed the `TAP_SCHEMA.tables` metadata query. The second metadata request returned HTTP 400 before producing a column result because the audit used:

`ORDER BY column_index`

against `TAP_SCHEMA.columns`. VizieR's TAP metadata interface does not accept that ordering field in this query.

No query selected from `"J/A+A/667/A157/catalog"`; no EFN event, solar longitude, geometry, velocity, shower label, or orbit value was accessed. The failed run therefore has no scientific endpoint and no Stage-1 access.

Authorized repair: change only the metadata query ordering from `ORDER BY column_index` to `ORDER BY column_name`. Column ordering has no scientific role; the audit subsequently verifies the required column set by exact names.

No table identifier, required field, Stage-1/2/3 query shape, scientific method, panel, threshold, firewall, evaluator, or gate changes.
