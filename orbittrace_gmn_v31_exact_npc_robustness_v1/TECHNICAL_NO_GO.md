# OrbitTrace GMN v31 exact 1-NPC robustness v1 — technical no-go

Status: **TECHNICAL NO-GO BEFORE SCIENTIFIC SCORE**

This closure preserves the first binding execution of the already-frozen method and does not modify its scientific definition.

## Binding execution

- Frozen protocol commit: `dfa4be55a949df08afa90a4dda8a7edd449a4b1f`
- Frozen implementation commit: `d28912b57459393f9876d81a989142b94dfecf74`
- Workflow registration commit: `bb9492b584e07bd4421be2db50c06493f11eb98f`
- First scientific workflow run: `31665636305`
- Preserved artifact: `9167818443`
- Artifact digest: `sha256:016b3991d13d25ad359b1f9dcffcb6690fdd94377d932d50eb2ae916eac7d7df`

## What passed before science

The workflow passed all preregistered engineering and provenance gates before attempting the GMN successor calculation:

1. exact runtime/source compilation;
2. frozen diversity/evaluator source verification;
3. deterministic analytic exact-radius solver self-tests;
4. authoritative GMN v31 offline-package verification, including exact package hashes, shapes, firewall fields, parent hard-order control, and exact v31 fused control.

The solver self-tests returned `PASS_EXACT_NPC_ROBUSTNESS_ENGINEERING_SELF_TESTS`.

The offline package verification returned `PASS_AUTHORITATIVE_OFFLINE_PACKAGE_BEFORE_EXACT_NPC_ROBUSTNESS`.

## Binding failure

During the first GMN exact-radius calculation, a frozen fixed-opposite projection QP returned:

`SLSQP fixed-opposite projection failed: Positive directional derivative for linesearch`

The failure occurred inside `fixed_opposite_projection` before all 226 strict-OOF robustness scores were computed. Therefore no candidate ranking, no fused ranking, and no scientific successor metrics were produced.

## Why this is a technical no-go rather than an engineering repair

The frozen protocol explicitly requires, for every fixed-opposite QP:

- `method='SLSQP'`;
- fixed analytic gradients/Jacobians;
- `ftol=1e-12`;
- `maxiter=1000`;
- initial point equal to the query `z`;
- solver success plus fixed feasibility checks.

It also states that if any fixed-opposite QP fails these checks, **the entire method is technically invalid**, the QP is not skipped, and **no alternate optimizer or tolerance is tried after scientific execution**.

Because the first real GMN execution reached the frozen scientific QP and the frozen solver itself failed its mandatory success criterion, changing initialization, optimizer, tolerances, feasibility handling, active-set logic, projection backend, screening, or fallback behavior would change a preregistered execution rule after scientific data contact. That is not an authorized engineering repair.

## Scientific interpretation

This is **not** a negative GMN performance result. The method never produced a technically valid scientific outcome, so no comparison to v31 promotion metrics is permitted.

The lane is closed exactly as frozen. In particular, do not rescue it with:

- alternate optimizers or QP solvers;
- changed SLSQP settings or initialization;
- tolerance changes;
- candidate pruning or screening;
- approximate-radius fallbacks;
- lower-bound/exact-radius blends;
- signed/unsigned variants;
- prototype subsets;
- result-informed solver variants.

## Firewall

No SonotaCo 2013/2014 scientific outcome was accessed for this successor. Protected solar longitude 20°–55°, OrbitTrace target information/events, MAARSY, and DMS remained inaccessible. The authoritative offline package contained no raw GMN event rows, raw event IDs, or raw hidden-label event mapping.
