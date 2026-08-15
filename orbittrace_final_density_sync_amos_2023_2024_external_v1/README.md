# OrbitTrace final density-synchronous AMOS 2023/2024 pre-data package

This directory contains the sealed **pre-data** package for the one-shot AMOS 2023/2024 external test of the final selected OrbitTrace method, exact PR #1263 density-synchronous recurrent-EOM HDBSCAN v1.

Method selection is already closed by PR #1267. This package is not a new method-development branch and must not be used to resume GMN search.

Authoritative files:

- `PROTOCOL.md` — final scientific protocol frozen before AMOS access.
- `EXECUTION_FREEZE.json` — immutable machine-readable method/source/audit freeze.
- `EXECUTION_FREEZE_SEAL.json` — independent audit seal for the immutable freeze.
- `generate_pretruth.py` — three-method, one-hierarchy geometry-only pretruth generator.
- `evaluate_labels.py` — postfreeze label-only evaluator.
- `DATA_REQUEST_READY_FINAL_NOT_SENT.md` — staged provider request, ready but **not sent**.
- `SCIENTIFIC_EXECUTION_RUNBOOK.md` — mechanical one-shot execution order if a compliant transfer is later obtained.
- `PREDATA_STATUS.md` — current status and exact binding audit evidence.

Current scientific state: **no AMOS scientific result exists.** No AMOS provider file, geometry row, or shower association has been received or accessed by this branch. Protected `[20°,55°]` remains excluded, OrbitTrace target information remains inaccessible, and MAARSY/DMS remain scientifically inaccessible.

Do not execute the old PR #1244 recurrent-EOM AMOS endpoint in parallel with this package. It is preserved only as historical/audited infrastructure provenance. This final-selected-method endpoint is the sole AMOS scientific chance under the method-selection closure.