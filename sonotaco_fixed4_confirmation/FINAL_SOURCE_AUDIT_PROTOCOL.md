# Fixed-4° SonotaCo confirmation source audit

Status: frozen before any SonotaCo 2024 data value, label token, support count, score, p-value, fold result, or endpoint is read.

## Final model decision

SonotaCo 2025 is the development survey. The final candidate is the exact **4° relative-solar-longitude scale** evaluated in runner PR #113, with all other PR #38 geometry, quartet search, windowing, calibration, p-value, and quality rules unchanged.

This is a new final-model freeze, not a relabelling of PR #113's failed cross-fitted scale-selection protocol. The model is selected after the complete 2025 development record because:

- fixed 4° passed every original pooled scientific gate on 2025;
- weak AUROC was 0.813250;
- pooled FPR was 0.047852 / 0.006836;
- k=4 recall was 0.154412 / 0.058824;
- k=6 recall was 0.522059 / 0.183824;
- k=8 recall was 0.691176 / 0.294118;
- all five fixed-4° fold AUROCs exceeded 0.75;
- four of five development folds selected 4° over the other preregistered scales.

All negative and near-miss development results remain part of the record. No further SonotaCo 2025 optimization is authorized after this freeze.

## Exact frozen sources

- PR #113 phase-scale source SHA-256: `e5cdb6eb8d07fdbcc5c29a4d02139fff86386e8aebde83717fdc7485acda265d`;
- SonotaCo 2024 structural parser-v2 source SHA-256: `d3f9c99bb64b6458a8637bc308bc84ba9d00d83258fa1383a1d73a0865dd072b` from commit `60bbe701981256b89aaa1c9361efef2bbb2dd57e`;
- SonotaCo 2024 archive SHA-256: `409bb958c6f114e542d818e7c4fcf7a58d89b2fb33090a442c8087bdcaa1540f`;
- annual member SHA-256: `0f25a0f9ea174c2b99915f48a61b35e35e3cde7f3117d82d4e05f8c4112acb00`.

## Audit boundary

This audit may only:

1. decode, hash-verify, compile, and AST-inspect the exact PR #113 source;
2. fetch, hash-verify, compile, and AST-inspect the exact parser-v2 source from the pinned commit;
3. preserve both decoded sources and their interface summaries.

It may not download `024a.zip`, inspect a 2024 CSV row or label, execute a detector, or compute any scientific endpoint.

A pass authorizes only a separately frozen one-shot SonotaCo 2024 confirmation protocol and implementation. The complete confirmation implementation, label rule, calibration design, seeds, comparators, and gates must be committed before the archive is opened.
