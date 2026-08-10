# OrbitTrace repository cleanup policy

This cleanup is organizational only. It must not rewrite scientific history, change a frozen result, or remove material needed to reproduce the discovery, paper, promoted methodology, or validation chain.

## Protected — do not delete or modify scientifically

1. Original GhostStream/OrbitTrace discovery lineage, including the HDBSCAN discovery/application code, frozen discovery outputs, target membership/provenance records, and any code/results cited or used in the paper.
2. Publication material and paper-supporting validation, including publication figures and the observational-validation lineage.
3. The surviving fixed-4° / Mondrian-clique sparse-stream detector lineage used as an independent recovery/benchmark.
4. Promoted/frozen methodology records and their source identities, especially v8 pooled-year-centroid label-free sparse-support multiplicity and the current v15 multiscale-consensus multiplicity deployment lineage.
5. Negative-result records needed to establish scientific provenance. A failed method may be removed from the active execution surface only if its result/protocol remains recoverable from Git history/PRs and its no-go status is indexed.
6. Frozen SonotaCo and MAARSY normalization/firewall contracts, final comparison/evaluator contracts, and any artifact hashes required by the current validation ladder.
7. Current canonical GMN/SonotaCo/MAARSY event adapters, survey-independent v15 application, exact-equivalence tests, label-free v8+v15 qualification, and the gated SonotaCo applicability path.

## Allowed cleanup

- Remove obsolete GitHub Actions workflows whose only purpose was retry/recovery/transport for a completed, failed, or superseded experiment.
- Remove duplicate launcher/retry workflow variants after preserving the associated PR/run/result provenance.
- Remove abandoned DMS execution scaffolding from the active branch. DMS is not part of the fixed validation ladder.
- Remove stale one-file execution markers after the associated run is immutable.
- Consolidate navigation/documentation so active methods and historical no-go experiments are clearly separated.

## Not allowed

- No force-push/history rewrite.
- No deletion of the original discovery method or paper-facing science.
- No deletion of a promoted method source, frozen protocol, result record, evaluator contract, or current validation adapter.
- No scientific parameter changes during cleanup.
- No new data access, target reveal, external evaluation, or method tuning as part of cleanup.

## Cleanup strategy

The active branch should contain a small, obvious execution surface. Historical failed experiments remain preserved in Git/PR history and are summarized in an archive index rather than left as runnable Actions workflows and open draft PRs. Cleanup changes are made on a dedicated branch and reviewed by diff before merge.
