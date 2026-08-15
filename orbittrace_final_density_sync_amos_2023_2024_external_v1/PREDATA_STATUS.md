# Final #1263 AMOS 2023/2024 — authoritative pre-data status

## 🟢 Engineering status: READY AND SEALED

The final selected-method AMOS pipeline is implemented and independently audited **before any AMOS 2023/2024 event-level scientific access**.

Selected method: exact density-synchronous recurrent-EOM HDBSCAN v1 from PR #1263, binding head `182f07ade6bb5d4be2c80b88df9216bb2d6eee2d`.

Method selection is closed by PR #1267. No further GMN methodology search is authorized.

The sole authoritative future-execution freeze is now:

- `EXECUTION_FREEZE_V3_EXACT_LABEL.json`
- Git blob `beed71cac547973b198b6ed16e319ebe42051583`
- SHA-256 `cfa94e7bfad096693f1370142a7f28a65a0ee5e311806a3f634203a45ae111d3`

The older `EXECUTION_FREEZE.json` and `EXECUTION_FREEZE_HARDENED.json` remain preserved as historical engineering provenance but are superseded for future AMOS execution.

## Binding zero-data evidence

### 1. Corrected v3 source / full-pipeline / adversarial / exact-label audit — PASS

- run `31866127514`
- execution head `98ac9b430e511f2b05951470984bc485ee2cfb04`
- artifact `9242054017`
- digest `sha256:e05d8948f1aada319ce251dc649fad9aca7e13df1c6ef084df12fda898e6b742`

Exact result SHA-256 values:

- AST-aware source audit: `63d53aff1a056e6be67347f6adc3ba453c9851833b3ebc2a56ec380318a2e439`
- full synthetic pipeline: `d354d042a4dc057bae89aa46df2d684292fedb05badcdbcffe8e50bba7fe73c9`
- adversarial evaluator hardening: `0de496d2f3b42111f39759c51c96063128b23eb063571174d96c42400d5bbe25`
- exact label-transport audit: `fff8d9777e83acbf1940a94429bee6ee2809721c5e946a3c3cfa2207ad060427`

Binding engineering verdicts:

- `PASS_FINAL_DENSITY_SYNC_AMOS_PREDATA_SOURCE_AUDIT_V3`
- `PASS_FINAL_DENSITY_SYNC_AMOS_FULL_PIPELINE_SYNTHETIC_AUDIT_V1`
- `PASS_FINAL_DENSITY_SYNC_AMOS_EVALUATOR_HARDENING_AUDIT_V3`
- `PASS_FINAL_DENSITY_SYNC_AMOS_LABEL_TRANSPORT_EXACTNESS_AUDIT_V3`

This clean audit proves, using synthetic-only rows:

- generator has no truth input surface;
- exactly one pooled HDBSCAN hierarchy supplies ordinary EOM, recurrent-EOM, and final density-synchronous outputs;
- pretruth is byte-deterministic;
- evaluator performs structural/source/order/membership integrity checks before opening either label file;
- evaluator has no HDBSCAN/GEO6/recurrent/density-sync recomputation call surface;
- all 12 forged-pretruth attacks are rejected before labels;
- all 15 frozen adversarial hardening assertions pass;
- an empty selected catalogue is a valid endpoint and yields the binding scientific FAIL token rather than a technical retry opportunity;
- exact uppercase `SPORADIC` is accepted;
- ambiguous no-association aliases fail closed;
- surrounding whitespace fails closed instead of being silently normalized;
- a valid mixed-case synthetic shower code `MiXeD-Code_42` survives unchanged through the inherited metric label keys;
- the synthetic fixture still produces a valid reporting-only scientific FAIL, proving PASS is not hard-coded.

### 2. Optional literature-comparator isolation audit — PASS

- run `31865012724`
- artifact `9241733611`
- digest `sha256:db48f22626bcde80c798c7333fc318421b4d0245ea2bae5539f311aed4163249`
- result SHA-256 `5a8e9e978f1e51454b465b13a98bd6b09d97655480763ae4d85970da0889e567`
- verdict `PASS_FINAL_DENSITY_SYNC_AMOS_COMPARATOR_ISOLATION_AUDIT_V1`

Optional uncertainty/convergence/`q`/`e` fields cannot enter the primary #1263 generator, and missing optional fields do not alter the primary final-test sample.

### 3. Historical transport-source reuse audit — PASS

- run `31865140271`
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

### 4. Authoritative exact-label execution-freeze integrity audit — PASS

Independent audit:

- run `31866299250`
- execution head `a7f0fbb40c7c3e95ff839802d9a5c2875c648a80`
- artifact `9242102571`
- digest `sha256:a55baf7b5fe703cb8dc0cf4dc02cd77cbcaf7d1745487b9647cb2fcdab440844`
- result SHA-256 `f0905dc03f1a36463e5047e3c5168268ae054efa06ad62cacc1d90240a6ea892`
- verdict `PASS_FINAL_DENSITY_SYNC_AMOS_EXECUTION_FREEZE_V3_EXACT_LABEL_AUDIT`

This audit independently re-downloaded the corrected v3 artifact, comparator-isolation artifact, and transport-reuse artifact by exact run ID; recomputed all binding result hashes; verified the exact evaluator/generator/method/transport pins; verified exact label transport; and proved the stale hardened freeze is superseded.

Integrity seal:

- `EXECUTION_FREEZE_V3_EXACT_LABEL_SEAL.json`
- Git blob `9b8a2763974c4bcaf7afc8dc1072febc65e5c83a`

## Preserved engineering no-results / superseded evidence

These remain in history and must not be erased:

- hardened v2 audit run `31865615689`: technical no-result because a naive static source-string check falsely treated metadata text `recurrent_stability` as a recomputation surface; no synthetic pipeline/AMOS science executed in that attempt.
- earlier v3 run `31865942127`: passed the checks it executed, but used the pre-exact-label evaluator and did not test an already-frozen requirement that valid association strings remain exact. Its subsequently written `EXECUTION_FREEZE_HARDENED.json` is therefore non-authoritative for future AMOS execution.

These are engineering provenance, not scientific outcomes.

## 🟡 Scientific status: NO AMOS RESULT YET

- provider request: **READY_NOT_SENT**;
- provider request sent: false;
- AMOS 2023/2024 provider data received: false;
- AMOS event rows accessed: false;
- AMOS geometry accessed: false;
- AMOS shower associations accessed: false;
- scientific execution started: false;
- protected `[20°,55°]` target-region geometry accessed: false;
- OrbitTrace target information accessed: false;
- SonotaCo / ASFN / EFN accessed by this final pipeline: false;
- MAARSY / DMS accessed scientifically: false.

Therefore there is **no positive or negative AMOS scientific result** to report.

## Remaining external dependency

A compliant staged AMOS 2023/2024 transfer is required. The exact request is frozen in `DATA_REQUEST_READY_FINAL_NOT_SENT.md`, but sending it remains a separate owner-authorized action.

Until that dependency is resolved, do not:

- run more GMN successors;
- retroactively validate #1263 on SonotaCo;
- access AMOS through an alternate noncompliant sample;
- change the final method/gate;
- search for a replacement external survey.

Once a compliant transfer exists, execute only the mechanical sequence in `SCIENTIFIC_EXECUTION_RUNBOOK.md`. The first technically valid AMOS endpoint is binding.
