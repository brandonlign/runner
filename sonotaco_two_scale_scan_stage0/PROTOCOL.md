# SonotaCo fixed two-scale scan source audit

Status: frozen before any new score, p-value, or endpoint is computed.

## Motivation

PR #113 showed that the exact 2° and 4° activity-phase scales recover complementary positive windows. A fixed 4° score passed the original k=4 recall gates, but complex-held-out selection of one global scale was unstable. The only authorized next candidate is therefore a fixed scan over exactly {2°, 4°} with one empirical conformal correction for the scale search.

Before defining that correction, this source-only audit preserves the exact PR #113 implementation so the new method inherits verified episode generation, seeds, score conventions, calibration bins, folds, and reporting interfaces.

## Frozen audit

The workflow shall decode only `sonotaco_k4_phase_scale_diagnostic/source_parts/part00.b64`, require SHA-256 `e5cdb6eb8d07fdbcc5c29a4d02139fff86386e8aebde83717fdc7485acda265d`, compile and AST-parse it, and upload the exact decoded source plus its top-level interface inventory.

No meteor archive, mapping audit, event row, label, score, fold result, or endpoint may be opened or computed. SonotaCo 2024 and GhostStream remain untouched.

A pass authorizes only a separately frozen SonotaCo 2025 two-scale joint-conformal development experiment.
