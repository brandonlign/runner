## Purpose

Pre-data engineering package for the **single one-shot AMOS 2023/2024 final external test** authorized by method-selection closure #1267.

The selected final method is exact PR #1263 density-synchronous recurrent-EOM HDBSCAN v1, binding head `182f07ade6bb5d4be2c80b88df9216bb2d6eee2d`. This PR does **not** reopen methodology search, access AMOS scientific data, or send the provider request.

## Scientific contract

The final AMOS protocol was frozen before implementation/data access. It fits exactly one pooled HDBSCAN hierarchy to retained AMOS 2023+2024 GEO6 geometry and freezes three complete candidate outputs before truth:

1. ordinary HDBSCAN EOM — primary external baseline;
2. exact recurrent-EOM — locked predecessor comparator;
3. exact #1263 density-synchronous recurrent-EOM — sole final method.

The primary final method must satisfy the frozen no-regression/strict-improvement gate versus ordinary HDBSCAN and no-regression gate versus recurrent-EOM. Strict incremental @100 improvement over recurrent-EOM is reported separately because #1265 showed the GMN +1 recovery gain was perturbation-sensitive.

If the final method fails AMOS, external generalization is not established. No method switch, AMOS rerun, threshold/gate rescue, or replacement external survey is authorized.

## Protected-data design

Provider transfer is frozen into three stages:

- Stage 1: `event_id,utc_time,solar_longitude_deg` only;
- inclusive removal of `[20.0,55.0]` before any geometry/truth;
- Stage 2 retained geometry only: `event_id,ra_j2000_deg,dec_j2000_deg,vg_km_s`;
- Stage 3 retained `event_id,shower_association` only after all three candidate orders are frozen and hash-bound.

Optional Stage 2B uncertainty/convergence/q/e fields are isolated to the previously frozen literature comparator supplement and cannot enter the primary final-method generator.

## 🟢 Positive engineering — complete zero-data audit chain

### Three-method source + full synthetic pipeline

- run `31864904536`
- artifact `9241708894`
- digest `sha256:6e4e970c7d11c1f3fe2ef14891a8684f1022a222f38ac7e584d967751922750b`
- source result SHA `88ffcbcf23addbe7e91d0ade4ae502eca4c221a535fc430b7dc972f263a20b9a`
- pipeline result SHA `4824a43b9dfeeef8cace5bdc72484cd33b9b332b06784a263bcc861dfe398833`
- verdicts:
  - `PASS_FINAL_DENSITY_SYNC_AMOS_PREDATA_SOURCE_AUDIT_V1`
  - `PASS_FINAL_DENSITY_SYNC_AMOS_FULL_PIPELINE_SYNTHETIC_AUDIT_V1`

Proved one pooled fit, ordinary-partition identity, shared hierarchy, recurrent/density-sync annual reconstruction, deterministic pretruth, truth isolation, exact pretruth-hash binding, fail-closed incomplete labels, and no method switching. The synthetic fixture produced a valid FAIL scientific token, proving PASS is not hard-coded.

### Optional comparator isolation

- run `31865012724`
- artifact `9241733611`
- digest `sha256:db48f22626bcde80c798c7333fc318421b4d0245ea2bae5539f311aed4163249`
- result SHA `5a8e9e978f1e51454b465b13a98bd6b09d97655480763ae4d85970da0889e567`
- verdict `PASS_FINAL_DENSITY_SYNC_AMOS_COMPARATOR_ISOLATION_AUDIT_V1`

Proved optional uncertainty/convergence/q/e fields cannot enter the primary #1263 generator and cannot change the primary sample.

### Blind receipt + canonical transport reuse

- run `31865140271`
- artifact `9241774418`
- digest `sha256:eb1b9471fd74e7ea28525ad7deba026b87940d540ba7ebd027636b4eb83baf52`
- result SHA `01871ec6ae5975d7adec17aaef17a0d3cb42a2fbbb3cdcf6c6c75c0461a9e0c9`
- verdict `PASS_FINAL_DENSITY_SYNC_AMOS_TRANSPORT_REUSE_AUDIT_V1`

Re-proved exact 20.0°/55.0° inclusive exclusion, fail-closed blind-index errors, exact J2000→GEO6 mapping, and protected/non-retained geometry rejection on the historical audited transport bytes.

### Independent execution-freeze rehydration

Immutable freeze:
- blob `84e85d69b2fcbf1dcdeeeaf0568c026c50548bd7`
- SHA-256 `9af0d330bc20c0a2cff367532d069a9b9630fab025e7c980900c5a0a7d9065d5`

Audit:
- run `31865241958`
- artifact `9241800054`
- digest `sha256:ffcdf114ac9ac25bf5e2b60458ffe002f205beb69b92a41620d8d3f95a81ee3a`
- result SHA `795a7557fd721242ed5c7acac6e894d0c62a657e6f525f3975509c36ad529949`
- verdict `PASS_FINAL_DENSITY_SYNC_AMOS_EXECUTION_FREEZE_AUDIT_V1`

This audit independently re-downloaded the three previous artifacts by exact run ID and recomputed all binding result hashes recorded in the freeze.

## 🟡 Scientific status — no AMOS result

At this PR state:

- provider request: `READY_NOT_SENT`;
- provider request sent: false;
- AMOS data received: false;
- AMOS event rows opened: false;
- AMOS geometry opened: false;
- AMOS labels opened: false;
- AMOS scientific execution started: false;
- SonotaCo/ASFN/EFN accessed by this pipeline: false;
- protected target data / OrbitTrace target info / MAARSY / DMS accessed: false.

The exact staged request is ready in `DATA_REQUEST_READY_FINAL_NOT_SENT.md`, but sending remains a separate owner-authorized action.

## Relationship to old AMOS work

PR #1244 remains preserved as the old unexecuted recurrent-EOM AMOS protocol and audited transport provenance. Its scientific endpoint must not be run in addition to this one. Exact method-agnostic receipt/adapter sources were reused only by immutable source pins and rerun synthetic audits.

PR #1248's literature supplement remains optional and isolated. Missing optional fields never alter the primary final test.

## Branch-diff hygiene

This branch starts exactly from #1267 head `d46864d375ece59bc3d3862e2c25f17b9ea91388`. It modifies no historical method/result source. All changes are confined to the new final-AMOS pre-data package and its zero-data audit workflows.
