# Final #1263 AMOS evaluator hardening v3 — pre-data engineering freeze

## Classification

**ENGINEERING-ONLY PRE-DATA REPAIR. NO AMOS SCIENTIFIC DATA OR OUTCOME EXISTS.**

This freeze is written after the hardened-evaluator v2 activation produced only an engineering no-result and before any v3 evaluator/audit source is changed.

No provider request has been sent. No AMOS 2023/2024 event row, retained geometry row, shower association, OrbitTrace target information, protected-target geometry, SonotaCo, ASFN, EFN, MAARSY, or DMS scientific value has been accessed by this repair.

## Preserved v2 engineering no-result

Hardened pre-data audit v2:

- run `31865615689`;
- execution head `51984d61920c1d013608619fd5f8e862de79f842`;
- artifact `9241902930`;
- artifact digest `sha256:9941e55484a0c232fe48a77405c4b1096a4383bd858ddee97d2849c97c30cee5`.

The workflow verified all pinned source blobs and compiled the hardened evaluator successfully, then failed in the **static source audit before any synthetic pipeline or adversarial fixture executed** with:

`RuntimeError: evaluator contains forbidden scientific recomputation surface: recurrent_stability`

The failure was a false positive in the audit implementation. `audit_source_zero_data_v2.py` searched the evaluator's raw source text for the substring `recurrent_stability`. The hardened evaluator contains that token only as the pre-existing candidate score field name in the tuple:

`("ordinary_stability", "recurrent_stability", "synchronous_stability")`

It does not import or call the `recurrent_stability` scientific function. The v2 run therefore reached no scientific/synthetic endpoint beyond source inspection and is permanently classified as an **engineering no-result**. It is not rerun or relabeled.

## Additional pre-data correctness findings

Adversarial review also identified two fail-closed issues before any AMOS receipt.

### 1. Legitimate empty candidate catalogues must not become technical retries

The v2 validator required each method's candidate list to be nonempty. That is too strict. The frozen AMOS protocol does not classify a scientifically valid HDBSCAN extraction with zero selected candidates as a technical no-result.

If AMOS legitimately yields zero selected candidates for ordinary, recurrent, or density-synchronous extraction, that state must be preserved as a valid pretruth catalogue. The inherited metric/gate evaluation will then determine the binding scientific result. In particular, an empty final density-synchronous catalogue cannot satisfy the frozen strict-improvement/activity gate and therefore cannot be rescued by treating emptiness as a retryable transport/runtime failure.

### 2. Provider no-association sentinel must be exact

The inherited truth evaluator excludes only exact label `SPORADIC`. The frozen provider contract already requires explicit `SPORADIC` for retained events without an assigned shower.

Allowing ambiguous sentinel spellings such as `sporadic`, `NONE`, `NULL`, `N/A`, `UNKNOWN`, `UNASSIGNED`, `NO_SHOWER`, `0`, or `-` could cause a no-association token to be interpreted as a real known-shower label by the unchanged inherited evaluator.

The evaluator must therefore fail closed on known no-association aliases/case variants rather than normalize them or let them enter metrics. Exact `SPORADIC` remains the only accepted no-association value. This enforces the already-frozen contract and does not alter any true shower association.

## Sole authorized v3 engineering changes

Before the next zero-data activation, the evaluator/audits may change only as follows.

### A. Static source audit becomes AST-aware

Forbidden scientific recomputation must be detected from Python imports/call targets, not raw text substrings. Score-field strings such as `recurrent_stability` must not trigger a false failure.

The evaluator remains forbidden from importing/calling HDBSCAN fitting, GEO6 construction, ordinary stability recomputation, recurrent-EOM kernels, density-synchronous kernels, or candidate-generation functions.

### B. Empty flat catalogues are a valid pretruth state

For each of ordinary / recurrent / density-synchronous outputs:

- candidate payload must be a list but may be empty;
- selected-node list must be a list;
- candidate count and selected-node count must match exactly, including `0 == 0`;
- an empty list must hash deterministically as SHA-256 of empty bytes for both order and ordered-membership payloads under the frozen hash definitions;
- mechanism flags must still be recomputed exactly;
- no artificial candidate may be inserted to avoid an empty catalogue.

### C. Exact pretruth schema and candidate-row schemas

The evaluator must reject any unexpected top-level pretruth field before label files are opened.

Exact candidate row schemas are:

- ordinary: `family_id,node_id,event_ids,member_count,ordinary_stability`;
- recurrent: `family_id,node_id,event_ids,member_count,ordinary_stability,recurrent_stability`;
- density-sync: `family_id,node_id,event_ids,member_count,ordinary_stability,synchronous_stability`.

No extra truth-bearing or unknown candidate field is allowed.

For every nonempty candidate:

- `member_count >= 10`;
- member IDs are sorted, unique, retained, and flat/nonoverlapping within the method;
- candidate node IDs are unique and exactly equal the selected-node universe;
- deterministic family ID is recomputed from exact members and the frozen namespace:
  - ordinary prefix `HDBEOM`;
  - recurrent prefix `REOM1`;
  - density-sync prefix `DSEOM1`;
- all required scores are finite;
- complete candidate order must already satisfy the frozen sort order:
  - ordinary: descending ordinary stability, descending member count, ascending family ID;
  - recurrent: descending recurrent stability, descending ordinary stability, descending member count, ascending family ID;
  - density-sync: descending synchronous stability, descending ordinary stability, descending member count, ascending family ID;
- stored order and membership SHA-256 values must equal recomputation from the supplied lists.

These checks validate a previously frozen catalogue. They do not recompute hierarchy, selection, or ranking from geometry.

### D. Exact label sentinel contract

Before inherited metrics are called:

- blank labels still fail;
- exact `SPORADIC` is accepted as the sole no-association token;
- case-insensitive `SPORADIC` variants other than exact uppercase fail;
- normalized aliases `NONE`, `NULL`, `NA`, `N/A`, `UNKNOWN`, `UNASSIGNED`, `NO_SHOWER`, `NO SHOWER`, `0`, and `-` fail closed;
- other nonblank association strings are preserved exactly; no relabeling/normalization is performed.

### E. Expanded synthetic/adversarial audit

The next zero-data audit must prove all prior valid synthetic behavior remains unchanged and add fixtures showing:

1. forged source pin rejected before labels;
2. forged HDBSCAN pin rejected before labels;
3. forged order hash rejected before labels;
4. non-retained candidate ID rejected before labels;
5. overlapping flat membership rejected before labels;
6. duplicate retained ID rejected before labels;
7. corrupted annual reconstruction rejected before labels;
8. falsified mechanism flag rejected before labels;
9. unexpected top-level pretruth field rejected before labels;
10. unexpected candidate-row field rejected before labels;
11. forged deterministic family ID rejected before labels;
12. score/order inconsistency rejected before labels;
13. empty candidate catalogues are accepted as structurally valid and yield a binding scientific FAIL token rather than technical error in a synthetic-only fixture;
14. ambiguous no-association label sentinel is rejected after valid pretruth validation and before scientific metrics;
15. exact `SPORADIC` remains accepted.

## Explicitly unchanged science

This repair may not change:

- final selected method #1263;
- ordinary HDBSCAN or recurrent-EOM comparator definitions;
- GEO6;
- HDBSCAN parameters;
- annual normalization;
- recurrent or density-synchronous formula;
- candidate generation, selection, ranking, or tie rules;
- protected `[20,55]` handling;
- exact AMOS years 2023/2024;
- eligible-shower threshold;
- overlap/precision qualification rule;
- @25/@50/@100/@500 budgets;
- top-100 precision, MRR, fragmentation semantics;
- inherited `metrics` implementation;
- inherited `annual_gate` implementation;
- primary AMOS PASS/FAIL gate;
- incremental density-synchrony gate;
- optional literature-comparator scientific contract;
- one-shot/no-rescue/no-method-switch governance.

## Required v3 result before future AMOS execution

The first technically valid v3 zero-data endpoint is binding for this engineering hardening. If it fails, no AMOS provider data may be opened under the hardened evaluator until a separately preserved, purely engineering pre-data repair is frozen and audited.

A v3 PASS is engineering evidence only. It does not count as AMOS external validation and does not authorize sending the provider request.