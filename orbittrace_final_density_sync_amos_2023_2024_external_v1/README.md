# OrbitTrace final density-synchronous AMOS 2023/2024 pre-data package

This directory is the sealed **pre-data** package for the one-shot AMOS 2023/2024 external test of the final selected OrbitTrace method, exact PR #1263 density-synchronous recurrent-EOM HDBSCAN v1.

Method selection is closed by PR #1267. This package is **not** a method-development branch and must not be used to resume GMN search.

## Current authority

For any future AMOS execution, the sole authoritative machine-readable contract is:

- `EXECUTION_FREEZE_V3_EXACT_LABEL.json`
- Git blob `beed71cac547973b198b6ed16e319ebe42051583`
- SHA-256 `cfa94e7bfad096693f1370142a7f28a65a0ee5e311806a3f634203a45ae111d3`

Its independent integrity seal is:

- `EXECUTION_FREEZE_V3_EXACT_LABEL_SEAL.json`
- Git blob `9b8a2763974c4bcaf7afc8dc1072febc65e5c83a`
- audit run `31866299250`
- artifact `9242102571`
- verdict `PASS_FINAL_DENSITY_SYNC_AMOS_EXECUTION_FREEZE_V3_EXACT_LABEL_AUDIT`

The older `EXECUTION_FREEZE.json`, `EXECUTION_FREEZE_SEAL.json`, and `EXECUTION_FREEZE_HARDENED.json` are retained only as historical engineering provenance and are **not** valid future-execution authorities.

## Authoritative package files

- `PROTOCOL.md` — final scientific protocol frozen before AMOS access.
- `EXECUTION_FREEZE_V3_EXACT_LABEL.json` — exact method/source/audit/provider-state freeze for future execution.
- `EXECUTION_FREEZE_V3_EXACT_LABEL_SEAL.json` — independent integrity seal for that freeze.
- `generate_pretruth.py` — geometry-only, one-hierarchy, three-method pretruth generator.
- `evaluate_labels.py` — hardened postfreeze label-only evaluator; exact evaluator blob `c45e4739ea68639945b13de54f6e24dc9d870ba3`.
- `DATA_REQUEST_READY_FINAL_NOT_SENT.md` — staged provider request, ready but **not sent**.
- `SCIENTIFIC_EXECUTION_RUNBOOK.md` — mechanical one-shot execution sequence if a compliant staged transfer is later obtained.
- `PREDATA_STATUS.md` — human-readable current status and binding audit evidence.
- `FROZEN_ENDPOINT_SUMMARY.json` — compact machine-readable current state.
- `PACKAGE_MANIFEST.json` — current package/navigation manifest.

## Current engineering evidence

The exact current evaluator/package passed a clean zero-data source/full-pipeline/adversarial/exact-label audit in run `31866127514`, plus independent comparator isolation and transport-reuse audits. The execution freeze was independently rehydrated and verified in run `31866299250`.

A separate redundant V4 zero-data run `31866241969` reproduced the same four current-evaluator result SHA-256 values; it is confirmation only, not another scientific chance.

## Current scientific state

**No AMOS scientific result exists.**

- provider request sent: false;
- AMOS provider transfer received: false;
- AMOS event rows accessed: false;
- AMOS geometry accessed: false;
- AMOS shower associations accessed: false;
- scientific execution started: false;
- protected `[20°,55°]` target-region geometry accessed: false;
- OrbitTrace target information accessed: false;
- MAARSY/DMS scientifically accessed: false.

Do not execute the old PR #1244 recurrent-EOM AMOS endpoint in parallel with this package. It is historical/audited infrastructure provenance only. This final-selected-method endpoint is the sole AMOS scientific chance under the method-selection closure.
