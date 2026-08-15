## Purpose

Pre-data engineering package for the **single one-shot AMOS 2023/2024 final external test** authorized by method-selection closure #1267.

The selected final method is exact PR #1263 density-synchronous recurrent-EOM HDBSCAN v1, binding head `182f07ade6bb5d4be2c80b88df9216bb2d6eee2d`. This PR does **not** reopen methodology search, access AMOS scientific data, or send the provider request.

## Current execution authority

Future AMOS execution is governed only by:

- `EXECUTION_FREEZE_V3_EXACT_LABEL.json`
- Git blob `beed71cac547973b198b6ed16e319ebe42051583`
- SHA-256 `cfa94e7bfad096693f1370142a7f28a65a0ee5e311806a3f634203a45ae111d3`
- exact postfreeze evaluator blob `c45e4739ea68639945b13de54f6e24dc9d870ba3`.

Independent seal:

- `EXECUTION_FREEZE_V3_EXACT_LABEL_SEAL.json`
- Git blob `9b8a2763974c4bcaf7afc8dc1072febc65e5c83a`
- audit run `31866299250`
- artifact `9242102571`
- digest `sha256:a55baf7b5fe703cb8dc0cf4dc02cd77cbcaf7d1745487b9647cb2fcdab440844`
- result SHA-256 `f0905dc03f1a36463e5047e3c5168268ae054efa06ad62cacc1d90240a6ea892`
- verdict `PASS_FINAL_DENSITY_SYNC_AMOS_EXECUTION_FREEZE_V3_EXACT_LABEL_AUDIT`.

Older execution-freeze files remain preserved historical engineering provenance only and must not be used for future AMOS execution.

## Scientific contract

The final AMOS protocol fits exactly one pooled HDBSCAN hierarchy to retained AMOS 2023+2024 GEO6 geometry and freezes three complete candidate outputs before truth:

1. ordinary HDBSCAN EOM — primary external baseline;
2. exact recurrent-EOM — locked predecessor comparator;
3. exact #1263 density-synchronous recurrent-EOM — sole final method.

The primary final method must satisfy the frozen no-regression/strict-improvement gate versus ordinary HDBSCAN and no-regression gate versus recurrent-EOM. Strict incremental @100 improvement over recurrent-EOM is reported separately.

If the final method fails AMOS, external generalization is not established. No method switch, AMOS rerun, threshold/gate rescue, or replacement external survey is authorized.

## Protected-data design

- Stage 1 exact blind index: `event_id,utc_time,solar_longitude_deg`.
- Remove `[20.0,55.0]` **inclusively** before any retained geometry/truth may be opened.
- Stage 2 retained geometry only: `event_id,ra_j2000_deg,dec_j2000_deg,vg_km_s`.
- Stage 3 retained `event_id,shower_association` only after all three candidate orders are persisted and hash-frozen.
- Exact uppercase `SPORADIC` is the sole no-association sentinel.
- Surrounding association-label whitespace and ambiguous no-association aliases fail closed rather than being normalized.
- Optional Stage 2B uncertainty/convergence/q/e fields remain isolated to the already-frozen literature-comparator supplement and cannot enter the primary final method.

## 🟢 Binding current-evaluator zero-data evidence

### Exact source/full-pipeline/adversarial/label transport

Run `31866127514`, head `98ac9b430e511f2b05951470984bc485ee2cfb04`, artifact `9242054017`, digest `sha256:e05d8948f1aada319ce251dc649fad9aca7e13df1c6ef084df12fda898e6b742`.

Result SHA-256 values:

- source/firewall `63d53aff1a056e6be67347f6adc3ba453c9851833b3ebc2a56ec380318a2e439`;
- full pipeline `d354d042a4dc057bae89aa46df2d684292fedb05badcdbcffe8e50bba7fe73c9`;
- adversarial hardening `0de496d2f3b42111f39759c51c96063128b23eb063571174d96c42400d5bbe25`;
- exact label transport `fff8d9777e83acbf1940a94429bee6ee2809721c5e946a3c3cfa2207ad060427`.

The current evaluator rejects 12 forged pretruth payloads before label opening, passes all 15 hardening assertions, preserves valid mixed-case shower codes exactly, rejects ambiguous no-association aliases/whitespace, and treats a legitimate empty candidate catalogue as a scientific FAIL state rather than a retryable technical error.

### Comparator isolation

Run `31865012724`, artifact `9241733611`, PASS. Optional uncertainty/convergence/q/e fields cannot enter the primary final-method generator or alter its primary sample.

### Transport reuse

Run `31865140271`, artifact `9241774418`, PASS. Re-proved exact inclusive 20.0°/55.0° exclusion, fail-closed blind-index errors, exact J2000→GEO6 mapping, and protected/non-retained geometry rejection.

### Freeze integrity

Run `31866299250` independently re-downloaded the current-evaluator, comparator, and transport artifacts and recomputed every binding result hash in the authoritative freeze. PASS.

A redundant zero-data run `31866241969` / artifact `9242093082` independently reproduced the same four current-evaluator result SHA-256 values. It is confirmation only, not another scientific chance.

## Preserved engineering no-results

- `31865615689` — static source-audit false positive before synthetic pipeline execution.
- `31866079514` — stale source-pin failure after exact-label hardening, before evidence rehydration.

Neither is an AMOS scientific outcome.

## 🟡 Scientific status — NO AMOS RESULT

- provider request: `READY_NOT_SENT`;
- provider request sent: false;
- AMOS provider transfer received: false;
- AMOS event rows / geometry / shower associations accessed: false;
- AMOS scientific execution started: false;
- protected target data / OrbitTrace target info / MAARSY / DMS accessed: false.

The exact staged request is ready in `DATA_REQUEST_READY_FINAL_NOT_SENT.md`, but sending remains a separate owner-authorized action. `SCIENTIFIC_EXECUTION_RUNBOOK.md` defines the mechanical one-shot execution if a compliant transfer is later obtained.

## Relationship to old AMOS work

PR #1244 remains historical/audited infrastructure provenance only. Its scientific recurrent-EOM endpoint must **not** be executed as a second chance. PR #1248's literature supplement remains optional and isolated; missing optional fields never alter the primary final test.
