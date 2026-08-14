# Activate EFN Stage-2 retained native geometry access

Stage 1 is binding and frozen in `STAGE1_BINDING_FREEZE.json`. Stage-2 retained-ID-only access is authorized by `STAGE2_PREACCESS_FREEZE.json` after the successful zero-data audit.

The only scientific values authorized are the six native fields for the exact frozen 782 retained IDs:

`Code, Obs.date, Lsun, Lgeo-Lsun, Bgeo, Vgeo`

Each server query is restricted by `Code IN (<subset of frozen retained IDs>)`. No raw-longitude server filter is used. `Lsun` is canonicalized with the already-promoted `% 360.0` rule and the protected `[20,55]` interval is asserted again locally.

No `Shower`, `Object`, orbit, brightness, uncertainty, target information, MAARSY, or DMS access is authorized.
