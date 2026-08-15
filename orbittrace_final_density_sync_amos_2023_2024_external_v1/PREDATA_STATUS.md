# Final #1263 AMOS 2023/2024 — pre-data status

## 🟢 Engineering status: READY AND SEALED

The final selected-method AMOS pipeline is fully implemented and independently zero-data audited before any AMOS 2023/2024 event-level scientific access.

Selected method: exact density-synchronous recurrent-EOM HDBSCAN v1 from PR #1263, binding head `182f07ade6bb5d4be2c80b88df9216bb2d6eee2d`.

Method selection is closed by PR #1267. No further GMN methodology search is authorized.

## Binding zero-data evidence

### 1. Three-method source + full synthetic pipeline audit — PASS

- run `31864904536`
- execution head `66e291f0c83f39834dc59159b579fb9d728327ee`
- artifact `9241708894`
- digest `sha256:6e4e970c7d11c1f3fe2ef14891a8684f1022a222f38ac7e584d967751922750b`
- source audit result SHA-256 `88ffcbcf23addbe7e91d0ade4ae502eca4c221a535fc430b7dc972f263a20b9a`
- synthetic full-pipeline result SHA-256 `4824a43b9dfeeef8cace5bdc72484cd33b9b332b06784a263bcc861dfe398833`
- verdicts:
  - `PASS_FINAL_DENSITY_SYNC_AMOS_PREDATA_SOURCE_AUDIT_V1`
  - `PASS_FINAL_DENSITY_SYNC_AMOS_FULL_PIPELINE_SYNTHETIC_AUDIT_V1`

Proved, on synthetic-only rows:
- generator has no truth input surface;
- exactly one pooled HDBSCAN fit;
- ordinary / recurrent / density-synchronous outputs share one hierarchy;
- byte-deterministic pretruth rerun;
- annual reconstruction within frozen tolerance;
- labels open only after pretruth hash freeze;
- evaluator cannot recompute hierarchy/candidates;
- incomplete label maps fail closed;
- PASS is not hard-coded (the synthetic fixture produced a valid scientific FAIL token because strict @100 improvement was absent).

### 2. Optional literature-comparator isolation audit — PASS

- run `31865012724`
- execution head `eaa4f4ebb62b3bf65b6c6539813ab8e9b6ba13f7`
- artifact `9241733611`
- digest `sha256:db48f22626bcde80c798c7333fc318421b4d0245ea2bae5539f311aed4163249`
- result SHA-256 `5a8e9e978f1e51454b465b13a98bd6b09d97655480763ae4d85970da0889e567`
- verdict `PASS_FINAL_DENSITY_SYNC_AMOS_COMPARATOR_ISOLATION_AUDIT_V1`

Proved optional uncertainty/convergence/q/e fields cannot enter the primary #1263 generator and missing optional fields do not alter the primary final-test sample.

### 3. Historical transport-source reuse audit — PASS

- run `31865140271`
- execution head `38895440667ff8eceda7caf83cecf7ae02a8b4bc`
- artifact `9241774418`
- digest `sha256:eb1b9471fd74e7ea28525ad7deba026b87940d540ba7ebd027636b4eb83baf52`
- result SHA-256 `01871ec6ae5975d7adec17aaef17a0d3cb42a2fbbb3cdcf6c6c75c0461a9e0c9`
- verdict `PASS_FINAL_DENSITY_SYNC_AMOS_TRANSPORT_REUSE_AUDIT_V1`

Re-proved on exact historical transport bytes:
- 20.0° excluded;
- 55.0° excluded;
- wrong year / duplicate ID / extra blind-index column fail closed;
- canonical J2000 radiant + Vg mapping to GEO6 is exact;
- protected/non-retained geometry fails closed.

### 4. Execution-freeze integrity audit — PASS

Sealed execution freeze:
- Git blob `84e85d69b2fcbf1dcdeeeaf0568c026c50548bd7`
- SHA-256 `9af0d330bc20c0a2cff367532d069a9b9630fab025e7c980900c5a0a7d9065d5`

Independent audit:
- run `31865241958`
- execution head `8d89de94c991858865880556d8d97cc9d94ee7e3`
- artifact `9241800054`
- digest `sha256:ffcdf114ac9ac25bf5e2b60458ffe002f205beb69b92a41620d8d3f95a81ee3a`
- result SHA-256 `795a7557fd721242ed5c7acac6e894d0c62a657e6f525f3975509c36ad529949`
- verdict `PASS_FINAL_DENSITY_SYNC_AMOS_EXECUTION_FREEZE_AUDIT_V1`

The integrity audit re-downloaded all three prior artifacts by exact run ID and recomputed every result hash recorded in the freeze.

## 🟡 Scientific status: NO AMOS RESULT YET

- provider request: **READY_NOT_SENT**;
- AMOS 2023/2024 provider data received: false;
- AMOS event rows accessed: false;
- AMOS geometry accessed: false;
- AMOS shower associations accessed: false;
- scientific execution started: false;
- protected `[20°,55°]` target-region geometry accessed: false;
- OrbitTrace target information accessed: false;
- SonotaCo / ASFN / EFN accessed by this final pipeline: false;
- MAARSY / DMS accessed scientifically: false.

Therefore there is no positive or negative AMOS scientific result to report yet.

## Remaining external dependency

A compliant staged AMOS 2023/2024 transfer is required. The exact request is frozen in `DATA_REQUEST_READY_FINAL_NOT_SENT.md`, but sending it remains a separate owner-authorized action.

Until that external dependency is resolved, do not:
- run more GMN successors;
- retroactively validate #1263 on SonotaCo;
- access AMOS through an alternate noncompliant sample;
- change the final method/gate;
- search for a replacement external survey.

Once a compliant transfer exists, execute only the mechanical sequence in `SCIENTIFIC_EXECUTION_RUNBOOK.md`. The first technically valid AMOS endpoint is binding.