# Execute repaired MAARSY 2016/2017 orbital validation

Execution-only trigger for the frozen post-ranking orbital stage.

Two technical failures have occurred without reaching any MAARSY orbit-value read: first a stale transport-container checksum, then a missing repository-module import path while loading the already-frozen evaluator. The workflow now uses the independently verified immutable geometry payload and the same module search path needed by the frozen evaluator (`orbittrace_multi_anchor_energy_v3:orbittrace_wavelet_catalogue_v3:.`).

The scientific runner, N=107 family/ranking universe, inner-file hashes, canonical ranking hash, D_SH rule, Q floor, evaluator blob, and all external-validation gates are unchanged.
