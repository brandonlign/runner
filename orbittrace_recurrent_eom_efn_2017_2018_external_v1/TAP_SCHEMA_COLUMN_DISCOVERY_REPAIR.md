# EFN TAP_SCHEMA column-table discovery repair

**Classification: engineering-only metadata repair; no EFN event access.**

Metadata-only run `31833839945` successfully discovered the canonical EFN table in `TAP_SCHEMA.tables` after literal-quote normalization. It then returned zero rows when `TAP_SCHEMA.columns` was constrained by the exact raw `table_name` string copied from `TAP_SCHEMA.tables`.

This shows that VizieR does not expose the table identifier with identical literal encoding in the two TAP_SCHEMA views. The run stopped there. No selection from the EFN event table occurred.

Authorized repair:

1. query only `TAP_SCHEMA.columns` using `table_name LIKE '%667/A157%'`;
2. include `table_name` in the returned metadata columns;
3. normalize a single surrounding quote pair (`'...'` or `"..."`) independently for each returned table identifier;
4. retain only metadata rows whose normalized table name is exactly `J/A+A/667/A157/catalog`;
5. verify the required field set from those metadata rows.

This is discovery of metadata identifier encoding only. It does not change the event-table identifier, Stage-1/2/3 query shapes, native scientific field mapping, method, firewall, evaluator, or gate.

At repair time:

- `efn_event_rows_accessed=false`
- `efn_geometry_accessed=false`
- `efn_shower_labels_accessed=false`
