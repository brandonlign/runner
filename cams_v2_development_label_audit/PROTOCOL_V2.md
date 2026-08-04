# Historical CAMS Database 2.0 development-label audit parser v2

Status: separately frozen after parser v1 stopped on record 1 before any label aggregate was formed.

## Sole correction

The official `reading.f` initializes `SHN(J)` to two spaces before parsing each catalogue and overwrites it only when a `Sh :` field is present. Therefore the native record format permits the entire `Sh :` field to be omitted when the shower assignment is absent.

Parser v2 changes only the `Sh` cardinality rule:

- zero `Sh :` field headers in a record means absent/background;
- one `Sh :` field header follows the already frozen presence flag and opaque two-byte token rule;
- more than one `Sh :` field header remains fatal.

`Yr :` and `LS :` remain required exactly once. No other source hash, archive/member, 40,744-record development boundary, year gate, blind interval, token syntax, support definition, continuation gate, reserved-data boundary, or output rule changes from `PROTOCOL.md`.

Parser v1 and its artifact remain a preserved no-go. Parser v2 must emit the count of records with an omitted `Sh` field, without emitting any record or token identity.
