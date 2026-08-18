# Cross-hierarchy refinement DAG v1 — Technical Repair 02

## Classification of Repair 01 run 32185199054

Run `32185199054` is a **technical no-result**. It produced no DAG stability result, no structural verdict, and no scientific prelabel/result artifact. The workflow contains no shower-truth stage.

Repair 01 successfully corrected the raw support-resolved TopoModal parent provenance:

- exact target-excluded GMN panel event count: PASS;
- exact panel event-universe SHA-256: PASS;
- exact raw support-resolved TopoModal memberships at d=128,b=0: PASS;
- exact recurrent-EOM memberships at d=128,b=0: FAIL.

The execution stopped before any cross-scale stability metric was computed:

`RuntimeError: sealed sparse membership rebind failed d=128 b=0: {'topomodal_memberships_exact': True, 'recurrent_memberships_exact': False, 'event_count_exact': True, 'event_universe_exact': True}`

The frozen scientific runner remains Git blob `4a45d8ab4b2237ddcbc4e1d0bf0f8a01dba15bf0`. The Repair 01 parent-prelabel adapter remains Git blob `16eaa8c45c5fe508e6e02e907bf402f1abf029bf` and is not modified by this repair.

## Concrete execution-environment discrepancy

The authoritative support-resolved-cut run that created immutable prelabel SHA-256 `4529eadd9ff93aae057f0a6fd5e0dd923f2300b7c6e01b74a0b7638e22da6de6` used this exact module-resolution order during parent reconstruction:

`PYTHONPATH=input/ranker:.:orbittrace_recurrent_eom_hdbscan_v1:input/v3:frozen-v8/orbittrace_wavelet_catalogue_v3:frozen-v8`

Repair 01 used:

`PYTHONPATH=input/ranker:.:orbittrace_recurrent_eom_hdbscan_v1:input/v3:frozen-v8:frozen-v8/orbittrace_wavelet_catalogue_v3`

The two final entries were reversed. Because the frozen runtime/source loader imports modules from these paths, restoring the authoritative order is a technical reproducibility correction required before concluding that the recurrent memberships themselves fail to reproduce.

## Frozen Repair 02 scope

Repair 02 may change **only** the execution environment's `PYTHONPATH` ordering for the actual structural runner to match the authoritative support-resolved-cut workflow byte-for-byte:

`input/ranker:.:orbittrace_recurrent_eom_hdbscan_v1:input/v3:frozen-v8/orbittrace_wavelet_catalogue_v3:frozen-v8`

Everything else remains inherited unchanged from Repair 01, including:

- frozen scientific runner blob `4a45d8ab4b2237ddcbc4e1d0bf0f8a01dba15bf0`;
- Repair 01 adapter blob `16eaa8c45c5fe508e6e02e907bf402f1abf029bf`;
- raw support-cut prelabel run `31961908008`, artifact `9267530845`, SHA-256 `4529eadd9ff93aae057f0a6fd5e0dd923f2300b7c6e01b74a0b7638e22da6de6`;
- target-excluded GMN 2022+2023 event universe;
- denominators 64/128/1024 and buckets 0..3;
- exact TopoModal hierarchy/cut;
- exact recurrent-EOM hierarchy/extraction;
- DAG edge rule (`nonempty exact event intersection`);
- common-refinement atom definition;
- projection and symmetric event-weighted mean-best-Jaccard metric;
- all nine frozen SUPPORT/REFUTES gates;
- all firewall and interpretation rules.

No source-code substitution, membership tolerance, alternate identity, fuzzy comparison, threshold, ranking, pruning, weighting, fallback, or gate relaxation is authorized.

If exact recurrent membership rebind still fails after this environment-parity repair, Repair 02 remains a technical no-result. The next action must diagnose the exact remaining source/runtime difference; it must not weaken the exact rebind prerequisite.

If Repair 02 reaches the frozen structural gates, that first technically valid zero-label result is binding.