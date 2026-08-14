# EFN Stage-2 returned-header repair — frozen after technical no-result

**Classification: engineering-only transport repair. No scientific method, row eligibility, geometry mapping, or evaluator change.**

The first authorized Stage-2 live run reached the retained-ID-only VizieR geometry query:

- run: `31841676793`
- job: `94899693445`
- head: `3604da5481fb891f1b4e669558a29f229600ac79`
- technical artifact: `9234462006`
- technical artifact digest: `sha256:daeb79826f184fc186fc52f85aeb0e81fe884b21d9c0eceeb197e3e1f1e424f6`

All source pins and the binding Stage-1 retained set passed first. The server query was restricted to a subset of the already-frozen retained-ID allowlist and selected only:

`Code, Obs.date, Lsun, Lgeo-Lsun, Bgeo, Vgeo`

The first response header was:

`Code, Obs_date, Lsun, Lgeo-Lsun, Bgeo, Vgeo`

The loader had conservatively expected VizieR to sanitize `Lgeo-Lsun` to `Lgeo_Lsun`, so it stopped immediately with:

`Stage-2 returned wrong columns: ['Code', 'Obs_date', 'Lsun', 'Lgeo-Lsun', 'Bgeo', 'Vgeo']`

The header assertion occurs before iteration over response rows, so no returned geometry row was parsed into the scientific representation and no valid Stage-2 endpoint was produced. The server response was not persisted. The query contained only Stage-1 retained IDs, therefore no protected-row geometry was requested or returned.

## Sole authorized repair

Change only the expected VizieR returned-header mapping for the native longitude field:

- semantic field remains `Lgeo-Lsun`;
- returned CSV header is `Lgeo-Lsun` (literal hyphen), not `Lgeo_Lsun`;
- row lookup changes correspondingly from `row['Lgeo_Lsun']` to `row['Lgeo-Lsun']`.

Unchanged:

- Stage-1 retained IDs/hashes;
- six selected Stage-2 fields;
- retained-ID-only `Code IN (...)` server restriction;
- generic `% 360.0` solar-longitude normalization;
- inclusive protected interval `[20,55]` after canonicalization;
- native `Lgeo-Lsun`, `Bgeo`, `Vgeo` values (no conversion/calibration);
- HDBSCAN/recurrent-EOM method;
- candidate generation/ranking;
- labels remain inaccessible;
- evaluator and validation gate.

Before a live retry, the repaired source must pass a zero-EFN-data synthetic audit exercising the literal-hyphen returned CSV header and fail-closed extra-column/ID/geometry cases.

Firewall at repair freeze:
- Stage-1 retained IDs frozen: true
- protected-region physical values requested/returned: false
- valid Stage-2 endpoint: false
- Stage-2 canonical geometry artifact: false
- EFN shower labels accessed: false
- target information accessed: false
- MAARSY scientific access: false
- DMS scientific access: false
- OrbitTrace target access: false
