# EFN Stage-2 preaccess audit 1 — synthetic harness no-result

**Classification: engineering-only synthetic audit failure. No EFN geometry/event row or shower label accessed.**

Run `31841419744`, job `94898915132`, head `a7468c110eed1526f67585ac78e8c08a85b02979` passed all exact pre-geometry source pins and source-boundary checks, then failed only in the synthetic negative-case harness:

`Stage-2 negative case did not fail closed: extra-column`

Cause: the self-test monkeypatched `iter_returned_rows()` after the production CSV header/schema checker, so its injected `Shower` key never passed through the real `csv.DictReader` field-name assertion. This does not identify a production Stage-2 access defect; it identifies an insufficiently faithful test harness.

Authorized repair: change only the synthetic self-test injection point to mock `query_batch()` raw CSV responses so the production header, per-batch requested-ID, duplicate, and exact-set checks execute. Production `stage2_geometry.py`, retained-ID cohort, access fields, native mapping, recurrent-EOM method, and evaluator remain unchanged.

The provenance step also lacked `mkdir -p` after the self-test stopped before creating the output directory; that workflow-only artifact-plumbing issue may be repaired at the same time.

Firewall at failure:
- Stage-1 retained IDs frozen: true
- EFN geometry accessed: false
- EFN shower labels accessed: false
- target information accessed: false
- target-region physical values accessed: false
- MAARSY scientific access: false
- DMS scientific access: false
- OrbitTrace target access: false
