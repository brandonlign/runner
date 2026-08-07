# UKMON 2020/2021 freshness audit ERE-only rerun

Execution-only child of the corrected frozen zero-data freshness audit parent.

The sole audit-logic change from the failed first attempt is the static POSIX ERE compatibility repair in `UKMON_MARKER`: `(?:Observation|Network)` -> `(Observation|Network)`. No search term, target year, exposure criterion, positive control, scientific rule, data source, or blindness boundary changed.

This run is repository-history-only. It must not contact UKMON, request meteor payloads, inspect scientific values or labels, or access OrbitTrace target information.
