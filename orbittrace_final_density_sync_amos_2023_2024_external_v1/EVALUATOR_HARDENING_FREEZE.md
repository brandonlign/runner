# Final #1263 AMOS evaluator hardening — pre-data engineering repair freeze

## Classification

**ENGINEERING-ONLY PRE-DATA HARDENING. NO SCIENTIFIC OUTCOME EXISTS.**

The first final-AM0S pre-data package and its execution freeze passed all synthetic/source audits, and no AMOS provider request or scientific data access occurred. During adversarial review of PR #1268 before any provider transfer, a fail-closed weakness was identified in `evaluate_labels.py`.

The evaluator correctly required the caller-provided SHA-256 to match the supplied pretruth file, but it did not independently verify all internal pretruth invariants. Therefore an accidentally modified or externally constructed pretruth file could be paired with its newly recomputed SHA and reach label evaluation even if its candidate lists, order hashes, membership hashes, mechanism flags, source pins, or HDBSCAN declaration no longer matched the frozen generator contract.

This is a trust-boundary weakness, not an observed scientific result and not a reason to alter any method or metric.

## Preserved v1 pre-data provenance

The original immutable execution freeze remains preserved unchanged:

- freeze Git blob `84e85d69b2fcbf1dcdeeeaf0568c026c50548bd7`;
- freeze SHA-256 `9af0d330bc20c0a2cff367532d069a9b9630fab025e7c980900c5a0a7d9065d5`;
- freeze audit run `31865241958`;
- freeze audit artifact `9241800054`;
- freeze audit verdict `PASS_FINAL_DENSITY_SYNC_AMOS_EXECUTION_FREEZE_AUDIT_V1`.

Those records remain valid evidence that v1 was internally consistent at the time it was sealed. They are now **superseded for future AMOS execution** by the engineering hardening defined here. They must not be deleted or rewritten.

## Sole authorized repair

Before any AMOS data receipt, harden only the postfreeze evaluator's validation of the already-frozen pretruth payload.

The repaired evaluator must, before opening/using label content beyond file parsing:

1. enforce the exact frozen HDBSCAN declaration;
2. enforce all exact upstream scientific source pins carried by pretruth;
3. enforce exact years, protected interval, final-method identity, phase and firewall flags;
4. require yearly retained-ID lists to be nonempty, individually unique, mutually disjoint, and exactly match `events_by_year` / `events_total`;
5. require every candidate event ID in ordinary, recurrent and density-synchronous lists to belong to the pooled retained-ID universe;
6. reject duplicate event IDs within a candidate;
7. reject duplicate candidate family IDs within each method order;
8. recompute and verify each method's complete order SHA from the frozen candidate list;
9. recompute and verify each method's ordered-membership SHA from the frozen candidate list;
10. recompute mechanism activity from selected-node tuples and complete-order hashes and require identity with the stored mechanism flags;
11. require candidate counts to agree with any persisted count metadata if present;
12. retain exact inherited `metrics` and `annual_gate` scientific evaluation without any threshold, metric, budget, truth rule, feature, method, or gate change.

The evaluator remains forbidden from importing HDBSCAN, geometry construction, recurrent/density-synchronous kernels, or recomputing hierarchy/candidates after labels.

## Explicitly forbidden changes

This repair may not alter:

- final method #1263;
- ordinary/recurrent comparator definitions;
- GEO6;
- HDBSCAN settings;
- density-synchronous or recurrent formula;
- annual normalization;
- candidate generation/ranking;
- protected `[20,55]` handling;
- label semantics;
- eligible shower threshold;
- overlap/precision threshold;
- @25/@50/@100/@500 budgets;
- top-100 precision, MRR or fragmentation definitions;
- primary or incremental PASS gates;
- years;
- provider data contract;
- optional literature comparator contract;
- one-shot/no-rescue governance.

## Required re-audit before any scientific execution

After the evaluator source is hardened, the following must all be rerun on zero/synthetic data and frozen again:

- source/firewall audit;
- full synthetic pipeline audit, including deliberate tampered-pretruth rejection fixtures;
- comparator-isolation audit where relevant;
- transport-source reuse audit may be reused only if its exact sources remain unchanged, but the new execution freeze must cite the unchanged binding transport evidence;
- new execution freeze and independent freeze-integrity audit.

No AMOS provider request is sent and no AMOS scientific value may be opened during this repair.