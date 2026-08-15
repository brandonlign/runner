# Final #1263 AMOS — execution runtime requirement

## Status

**Pre-data engineering/reproducibility requirement. No scientific data are accessed by this file.**

This requirement applies to the sole authoritative future-execution freeze:

- `EXECUTION_FREEZE_V3_EXACT_LABEL.json`
- Git blob `beed71cac547973b198b6ed16e319ebe42051583`
- SHA-256 `cfa94e7bfad096693f1370142a7f28a65a0ee5e311806a3f634203a45ae111d3`

It does not modify the frozen method, data roles, gates, or one-shot governance. It makes explicit the runtime already encoded by the binding audited workflow so a future scientific execution cannot silently drift to a different HDBSCAN/scikit-learn numerical implementation.

## Exact audited runtime

The binding current-evaluator zero-data audit run `31866127514` / artifact `9242054017` recorded:

- Python `3.11.15`;
- NumPy `2.1.3`;
- SciPy `1.14.1`;
- scikit-learn `1.7.1`;
- HDBSCAN `0.8.43`;
- joblib `1.5.3`;
- threadpoolctl `3.6.0`.

The redundant current-evaluator V4 audit run `31866241969` used the same stack and reproduced the same current-evaluator source/full-pipeline/adversarial/exact-label result SHA-256 values.

## Future scientific execution rule

Use the exact audited stack above for the AMOS endpoint.

Do **not** silently upgrade or substitute HDBSCAN, scikit-learn, NumPy, SciPy, or the Python runtime before the one-shot scientific endpoint. HDBSCAN hierarchy construction and numerical tie behavior are implementation-sensitive enough that a package-version change would weaken exact reproducibility of the frozen method.

If an exact runtime component is unavailable, stop **before opening any AMOS scientific file**. A replacement environment is allowed only after a separately frozen, zero-scientific-data equivalence audit proves the replacement reproduces the frozen synthetic pipeline, including at minimum:

- identical protected-region transport behavior;
- identical canonical GEO6 arrays;
- identical condensed-tree identity on the frozen synthetic fixtures;
- identical ordinary/recurrent/density-synchronous selected-node sets;
- identical candidate memberships and complete orders;
- identical pretruth hashes where deterministic environment metadata is not part of the payload;
- identical inherited evaluator outputs and PASS/FAIL tokens;
- unchanged source blobs, method definitions, parameters, data roles, metrics, gates, and provider contract.

Such an environment audit is engineering-only and cannot inspect AMOS, GMN, SonotaCo, ASFN, EFN, OrbitTrace target information/events, MAARSY, or DMS scientific values.

## Current state

- provider request: `READY_NOT_SENT`;
- AMOS provider data received: false;
- AMOS scientific data accessed: false;
- scientific execution started: false;
- target information/access: false;
- MAARSY/DMS scientific access: false.
