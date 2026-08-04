# SonotaCo cross-predictive radiant-drift source audit

Status: frozen before any new meteor archive access or detector score.

PR #118 showed that fitting and validating a phase slope on the same quartet disproportionately compresses background quartets and reduces all-four-member recovery. Its preserved next hypothesis is cross-prediction: fit on three events and require prediction of the held-out fourth.

This source-only audit decodes the exact PR #118 implementation to preserve its phase ordering, coordinate handling, quartet search, controls, and event interfaces before defining the cross-predictive revision.

The workflow must concatenate exactly eight source parts from `sonotaco_radiant_drift_development/source_parts`, require decoded SHA-256 `f72f7bd9478414c32edffc68209e8e8dd4de8b36bfef884be17c93cbe5b3b0af`, compile and AST-parse the source, and upload the exact decoded file and definition inventory.

No archive, mapping audit, meteor row, label, score, p-value, fold, or endpoint may be opened or computed. SonotaCo 2024 and GhostStream remain untouched.

A pass authorizes only a separately frozen cross-predictive SonotaCo 2025 development experiment.
