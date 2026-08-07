# Post-archive-access integrity repair — parser invocation order

## Status

This repair is frozen **after raw SonotaCo 2015/2017 archive bytes were downloaded by retry4 but before those archives were successfully parsed or scientifically ranked**.

Retry4 is preserved as `FAIL_MULTIPLICITY_SONOTACO_EXTERNAL_INTEGRITY` at stage `parser_transport`. It downloaded the two official SNMv3 ZIP archives, then failed before parser output because the frozen external runner invoked each transported parser with arguments in the wrong order.

Source-only Actions audit run `31201845405`, artifact `9003119605`, verdict `PASS_POSTACCESS_INVOCATION_BUG_SOURCE_AUDIT`, established without catalogue/archive-content access that:

- both immutable transported parsers require `(archive, audit_path, base)`;
- the frozen runner contains exactly one call `parsed = function(archive_path, base, mapping_audit)`;
- the mechanical correction is exactly `parsed = function(archive_path, mapping_audit, base)`;
- this is a one-line invocation repair and not a scientific-method change.

The evaluation protocol, fixed4 proposal scanner, multi-anchor multiplicity ranking, Brown comparator, fixed4 comparator, scaled-K endpoint, power requirements, pass gates, family linker, parser semantics, mapping, quality cuts, label handling, 20°–55° exclusion, and OrbitTrace target blindness are unchanged.

Because raw holdout archive bytes have already been transported, any repaired result must be described as a **fixed-protocol external evaluation completed after raw-archive transport exposure**, not as a pristine first-pass prospective validation. No result from retry4 was available to tune the method or gates.
