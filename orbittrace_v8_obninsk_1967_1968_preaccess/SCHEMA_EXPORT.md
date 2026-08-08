# Obninsk metadata-only schema export

Frozen after successful Stage-0 run `31231190121` / artifact `9013852268` and before any `.tab` event access.

The first audit proved the official PDS archive can be retrieved and that `obninsk.tab` exists while opening no `.tab` member. This follow-up is restricted to the already-public PDS4 label `data/obninsk.xml`.

It may export only structural field metadata: field number, name, data type, byte location/length, unit, format, missing/special constants, and textual description. It may not open, sample, count, parse, hash separately, or otherwise read `obninsk.tab` contents.

Purpose: decide whether the archived fields provide an exact deterministic mapping to the already-frozen v8 external geometry inputs (solar longitude, geocentric radiant, geocentric speed, stable identity) without empirical fitting or data-dependent calibration.

No scientific v8 evaluation, power calculation, target access, or GMN Stage A/Stage B execution is authorized.