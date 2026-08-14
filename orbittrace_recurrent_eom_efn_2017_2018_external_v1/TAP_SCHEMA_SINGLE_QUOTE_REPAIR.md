# EFN TAP_SCHEMA literal-single-quote normalization repair

**Classification: engineering-only metadata repair; no EFN event access.**

Metadata-only run `31833628019` returned the VizieR `TAP_SCHEMA.tables` rows successfully and revealed the exact raw representation of the desired table name:

`'J/A+A/667/A157/catalog'`

The surrounding single quotes are literal characters in the returned `table_name` metadata value. The existing normalizer removed only surrounding double quotes, so it failed to recognize the otherwise correct table. The run stopped at metadata normalization and never queried the EFN event table.

Authorized repair:

- normalize one matching pair of surrounding single quotes **or** double quotes when comparing TAP metadata identifiers to the canonical catalogue/table name;
- preserve the exact raw metadata value separately for the subsequent `TAP_SCHEMA.columns` predicate;
- make no change to any event-table ADQL, Stage-1/2/3 selected columns, firewall, method, field mapping, evaluator, or gate.

At this repair point:

- `efn_event_rows_accessed=false`
- `efn_geometry_accessed=false`
- `efn_shower_labels_accessed=false`
- `target_region_physical_values_accessed=false`
