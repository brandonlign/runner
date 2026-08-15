# Final #1263 AMOS evaluator hardening v4 — exact Stage-3 label transport freeze

## Classification

**ENGINEERING-ONLY PRE-DATA HARDENING. NO AMOS SCIENTIFIC OUTCOME EXISTS.**

This record is frozen before the first technically valid zero-data endpoint using the label-whitespace hardening now present on the live branch.

No AMOS provider request has been sent. No AMOS 2023/2024 event-level scientific row, retained geometry, shower association, OrbitTrace target information, protected-target geometry, SonotaCo, ASFN, EFN, MAARSY, or DMS scientific value has been accessed.

## Preserved v3 binding PASS

The prior hardened evaluator v3 remains a valid historical zero-data PASS at exact execution head:

`36052457f36f250758f3391e2917e6e87d6c9b1a`

Binding v3 evidence:

- run `31865942127`;
- artifact `9242001104`;
- artifact digest `sha256:255234e57f3cd582cfe21e50394ba03df8d9ad7f92b7b8069a97180911708394`;
- evaluator Git blob `bb2a1ba553fb57e573e85df39ccad1b69fe3b541`;
- source audit result SHA-256 `5e164f9dae654f97714e65cf07fdfa2d51b9249a460eee48dd3e55306ae8fb22`;
- full synthetic pipeline result SHA-256 `d354d042a4dc057bae89aa46df2d684292fedb05badcdbcffe8e50bba7fe73c9`;
- adversarial hardening result SHA-256 `0de496d2f3b42111f39759c51c96063128b23eb063571174d96c42400d5bbe25`;
- all 12 forged pretruth attacks rejected before labels;
- all 15 frozen hardening assertions passed.

This evidence is not rewritten by v4.

## Post-v3 unvalidated engineering change

After the v3 PASS, parallel work committed exactly one evaluator behavior change in commit:

`726032e3f815d8be0c5510b6b9a823eab2fef525`

The change is limited to Stage-3 label transport. Instead of silently applying `.strip()` and accepting the stripped association string, the evaluator now:

1. stores the raw CSV association string;
2. computes its stripped form;
3. requires `raw_label == stripped_label`;
4. only then applies the already-frozen exact-SPORADIC / ambiguous-alias validation.

Current evaluator Git blob:

`c45e4739ea68639945b13de54f6e24dc9d870ba3`

No metric, gate, method, hierarchy, candidate, score, truth qualification threshold, budget, or survey role changed.

## Motivation

The provider contract specifies exact Stage-3 `shower_association` values and already requires exact `SPORADIC` for unassigned retained meteors. Silently trimming surrounding whitespace is a normalization step that can hide malformed transport.

Failing closed on leading/trailing whitespace makes the evaluator preserve the exact provider string boundary. It also protects arbitrary legitimate shower codes from hidden normalization: a valid mixed-case/nonbackground code must survive byte-for-byte after CSV parsing rather than being canonicalized.

## Dedicated zero-data audit source

Parallel work also added:

`orbittrace_final_density_sync_amos_2023_2024_external_v1/audit_label_transport_exactness_v3.py`

Git blob:

`b16778cd10cbbb7704a4ee007a14030b97e07500`

The audit is synthetic-only and is intended to prove:

- exact `SPORADIC` is accepted;
- a valid mixed-case shower code such as `MiXeD-Code_42` remains exactly the same label key in inherited metrics;
- known no-association aliases/case variants are rejected;
- surrounding whitespace is rejected rather than normalized;
- no scientific method or gate changes.

The previously existing v3 workflow was modified after its binding v3 execution to include this audit, but that modified workflow was **not** the workflow bytes used by run `31865942127`; therefore the label-transport hardening has no binding audit yet.

## Preserved hardened-freeze audit engineering no-result

A later independent hardened-freeze audit correctly detected that the live evaluator no longer matched the v3-audited evaluator pin.

- run `31866079514`;
- execution head `695f5a48fb9b67a548fdbf274414d396223ac533`;
- artifact `9242032936`;
- artifact digest `sha256:bc9c7e8c7f733b1c9d65d90a8ecd7da1e73b3a1af49d1cff3ccec72058bd1497`;
- failure step: `Verify current hardened source identities`;
- failure occurred before any binding audit artifact was downloaded or rehydrated.

This is permanently classified as an **engineering source-pin no-result**. It is not a failure of the v3 method/evaluator science and it is not permission to change any scientific byte.

## Sole authorized v4 work

The first v4 zero-data audit must execute the current evaluator blob `c45e4739...` and must include all prior v3 checks plus the dedicated label-transport exactness audit.

It must prove, on synthetic data only:

1. the AST/source firewall still passes;
2. the exact valid synthetic full pipeline still runs;
3. all v3 forged-pretruth attacks still reject before labels;
4. all v3 15 hardening assertions remain true;
5. exact `SPORADIC` is accepted;
6. every declared ambiguous no-association alias is rejected;
7. a legitimate mixed-case nonbackground shower code is preserved exactly through the inherited metrics output;
8. surrounding whitespace in `shower_association` is rejected, not silently normalized;
9. scientific method/gate change flag remains false.

## Explicitly unchanged science

V4 may not change:

- final method #1263;
- ordinary/recurrent comparator definitions;
- GEO6;
- HDBSCAN settings;
- recurrent/density-synchronous quality definitions;
- annual normalization;
- hierarchy construction;
- candidate selection or ranking;
- protected `[20,55]` handling;
- AMOS years 2023/2024;
- eligible-shower threshold;
- overlap/precision qualification rule;
- @25/@50/@100/@500 budgets;
- top-100 precision, MRR, fragmentation semantics;
- inherited `metrics`;
- inherited `annual_gate`;
- primary PASS/FAIL gate;
- incremental density-synchrony gate;
- provider fields;
- optional literature-comparator scientific contract;
- one-shot/no-rescue/no-method-switch governance.

A v4 PASS is engineering evidence only. It does not count as AMOS validation and does not authorize sending the provider request.