# EFN Stage-1 VizieR returned-header repair

**Classification: engineering-only technical no-result; no geometry or shower-label access.**

The first authorized live Stage-1 run was `31834178184` at activation head `340cd142839b1b8927d0a05ce5392c365f4979a2`.

Preaccess authorization passed. The frozen ADQL query was accepted by VizieR and returned a CSV response, but the Stage-1 parser stopped before processing any row because VizieR sanitizes the quoted TAP column identifier `Obs.date` to the CSV header `Obs_date`.

Exact failure:

`Stage-1 returned wrong columns: ['Code', 'Obs_date', 'Lsun']`

Binding technical-failure provenance:

- run: `31834178184`
- technical artifact: `9231829658`
- artifact digest: `sha256:34a9f868f8baf15fd84af9640c7bd161a0d69a3c372271ae007877304faa46b6`
- frozen live workflow blob: `972834baf522f61abb4f3b0b12fd4c90aa8c61dc`
- pre-repair Stage-1 source blob: `61c6589ace0c5d36d83b7eb506c76200e0aa57ce`

No valid Stage-1 result was created; no retained-ID allowlist was created; the raw 824-row response was not persisted or uploaded. The artifact contains provenance-only files from the `always()` step.

Authorized repair before retry:

- keep the ADQL query **exactly unchanged**: `SELECT Code, "Obs.date", Lsun FROM "J/A+A/667/A157/catalog"`;
- recognize the VizieR CSV transport header exactly as `Code,Obs_date,Lsun`;
- map returned `Obs_date` back to the already-frozen semantic field `Obs.date` only for calendar-year parsing;
- keep `Code` and `Lsun` semantics unchanged;
- do not select or inspect any additional EFN column.

This is a transport-header alias repair only. It cannot alter the protected interval, 824-row cohort, years, method, native geometry mapping, evaluator, or gate.

Firewall at failure:

- `valid_stage1_endpoint=false`
- `retained_ids_frozen=false`
- `raw_stage1_response_persisted=false`
- `efn_geometry_accessed=false`
- `efn_shower_labels_accessed=false`
- `orbittrace_target_access=false`
