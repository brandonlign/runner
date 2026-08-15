# Density-synchronous recurrent-EOM v1 — import-only execution repair freeze

## Status

**ENGINEERING-ONLY REPAIR FREEZE AFTER A TECHNICAL NO-RESULT.**

The first GMN activation workflow run `31852571788` is preserved permanently as a technical no-result, not a scientific PASS/FAIL.

- execution head: `e4bba8dbe17af2cf530ded0c2ee1322525e87fcd`;
- artifact: `9237971344`;
- artifact digest: `sha256:30ad75c1fde8e7345532557d53ca338035a2ef7948c002d5330dadd620121198`.

The failure occurred at Python module import, before the successor runner entered `main()`:

`AttributeError: partially initialized module 'run_development' has no attribute 'YEARS' (most likely due to a circular import)`.

The frozen successor runner is itself named `run_development.py` and contains the intended import `import run_development as parent_runner`. When executed directly by file path, Python places the successor's directory first on `sys.path`, so this import resolved back to the partially initialized successor file instead of the exact promoted-parent runner.

This is a module-resolution collision only. It occurred before catalogue parsing, HDBSCAN fitting, prelabel freezing, hidden-truth use, metric calculation, or any scientific result.

The preserved run artifact contains exactly four provenance/environment files:

- `binding_provenance_sha256.txt`;
- `environment.txt`;
- `execution_commit.txt`;
- `python_version.txt`.

It contains **no** `DENSITY_SYNCHRONOUS_RECURRENT_EOM_V1_PRELABEL.json` and **no** `DENSITY_SYNCHRONOUS_RECURRENT_EOM_V1_GMN_DEVELOPMENT.json`.

## Frozen repair

The scientific bytes remain immutable:

- protocol blob `1187cbba37372c834bdbbf7eb05b1f7c31f8dcf9`;
- density-synchronous kernel blob `587a304f451e41b9503272f1783a6c6ebb295000`;
- successor scientific runner blob `157813ca331165180a6d20aa71bfc78d5984396f`;
- promoted recurrent-EOM kernel blob `30ac3fa3bc47910370df528fcf3ae8ecb6277b47`;
- promoted-parent runner blob `fdc4f3f6e037014aadfcc3ce41b7344aa0a80b2c`;
- execution-freeze blob `620fa5185ff331e8d3befd4395370df5e35fec83`.

The sole permitted repair is a thin execution wrapper that, before executing the unchanged successor runner:

1. verifies the exact promoted-parent and successor runner Git blob identities above;
2. explicitly loads the promoted-parent `orbittrace_recurrent_eom_hdbscan_v1/run_development.py` under the module name `run_development`;
3. verifies that `sys.modules['run_development']` points to that exact promoted-parent source;
4. executes the unchanged successor runner as `__main__`, preserving its original command-line arguments.

No scientific constant, objective, hierarchy rule, membership rule, ranking, metric, gate, data source, truth-access order, or firewall field may change.

## Required zero-data audit before retry

A retry is unauthorized until a zero-data import audit proves:

- the wrapper verifies every frozen source blob;
- the module named `run_development` resolves to the promoted-parent file, never the successor file;
- importing the unchanged successor runner through the repaired module environment binds `parent_runner` to that exact promoted-parent module;
- inherited constants (`YEARS`, `BLIND`, `MIN_CLUSTER_SIZE`, `MIN_SAMPLES`) exactly equal the promoted parent;
- the successor scientific runner and density-synchronous kernel remain byte-identical to the pre-outcome freeze;
- no catalogue parser, network client, HDBSCAN fit, hidden truth, GMN row, SonotaCo, EFN, ASFN, AMOS, MAARSY, DMS, target information, or protected-region event is accessed by the audit.

Only after that audit passes may one clean retry execute the exact frozen scientific method. The first technically valid endpoint remains binding. This repair does not authorize any scientific variant or second method search.
