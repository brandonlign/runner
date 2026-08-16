# Density-sync FLASC refinement v1 — technical repair 02

Repair run `31922286016` is also a **technical no-result**. It failed at Python import startup before catalogue parsing, parent reconstruction, FLASC support generation, prelabel freeze, or any known-shower evaluation.

Cause: the repair wrapper was executed by filesystem path. Python therefore placed `orbittrace_density_sync_flasc_refine_v1/` first on `sys.path`, so the frozen runner's intentionally bare `import run_development as parent_runner` resolved back to the FLASC runner itself instead of the pinned `orbittrace_recurrent_eom_hdbscan_v1/run_development.py` supplied first in `PYTHONPATH`, producing a circular import.

The only authorized repair is to launch the exact same pinned wrapper as a module:

`python -m orbittrace_density_sync_flasc_refine_v1.technical_repair_01_wrapper ...`

This restores the module-resolution mode already used by the original FLASC workflow and other successful OrbitTrace endpoints. No Python source, scientific method, FLASC setting, candidate rule, evaluator, firewall, or gate changes.