# SonotaCo fixed-4° final development source audit

Status: frozen before any final-candidate score or endpoint is computed.

## Final-model decision

The SonotaCo 2025 development program is complete. The original 2° formulation failed k=4 recall. The bounded-neighbor, phase3, soft-phase, conformal-fusion, free-drift, heliocentric-drift, cross-predictive, and phase-span selector revisions did not pass their frozen complete standards. The only evaluated formulation that passed the original two-threshold scientific standard is the fixed 4° relative-solar-longitude scale from PR #113:

- k=4 recall 0.154412 / 0.058824 at alpha 0.05 / 0.01;
- weak AUROC 0.813250;
- pooled FPR 0.047852 / 0.006836;
- worst-sector FPR 0.065104;
- k=6 recall 0.522059 / 0.183824;
- k=8 recall 0.691176 / 0.294118.

PR #128 froze that final-model decision without opening SonotaCo 2024. Before any confirmation can be designed, the fixed model must pass one standalone complete SonotaCo 2025 development benchmark with no scale family or selection logic.

## Exact standalone source

The final source evaluates exactly two views:

- 2° per unit: exact original PR #38/PR #69 control;
- 4° per unit: frozen final candidate.

It preserves the exact PR #113 parser adapter, source hashes, event filtering, blind exclusion, window construction, seeds, anchored nearest-three complete-link quartet search, calibration bins, calibration and negative counts, folds, positive replicates, p-values, and metric definitions. It removes the 6° and 8° diagnostic views and all fold-wise or consensus scale-selection code.

Frozen standalone source SHA-256: `747b2b1471f3ba193d68a39dd82ad3ac8506be63b651d45f84ffabb8d1acd301`.

Exact inherited PR #113 source SHA-256: `e5cdb6eb8d07fdbcc5c29a4d02139fff86386e8aebde83717fdc7485acda265d`.

## Source-only audit gates

The audit must prove, without opening any meteor archive or computing any score:

1. both exact source hashes;
2. both sources compile and AST-parse;
3. the final source evaluates exactly scales (2°,4°), with candidate fixed at 4°;
4. every pre-main scoring/helper function is AST-identical to PR #113;
5. the complete `main` data construction and scoring prefix is byte-identical to PR #113 through construction of `by_scale`;
6. every `mondrian-*` seed literal and all inherited source hashes are unchanged;
7. no scale selection, consensus, held-out scale choice, 6° view, or 8° view remains;
8. the full final-development gates are present;
9. SonotaCo 2024 and GhostStream values are absent.

A pass authorizes only a separately frozen standalone SonotaCo 2025 final-development run. SonotaCo 2024 remains untouched.
