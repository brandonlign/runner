# Density-synchronous recurrent-EOM GMN train robustness CV v1 — binding result

## 🔴 NEGATIVE — recovery superiority is not robust under the frozen perturbation

Binding workflow run: `31859724335`.

Aggregate artifact: `9240223128`.

Artifact digest: `sha256:75b38fca14d7542f4efa5cb230fa9f2cbb08fead480a80159e8dca50d834e6de`.

Aggregate result SHA-256: `06b50ea9254b7ed81f02ee682d09f916fc6c0493568c2c8b6cfb2cc5f225f333`.

Execution head: `d00fd21d475154df438da8b6799e50a013cfa249`.

Exact verdict: `FAIL_DENSITY_SYNC_GMN_TRAIN_CV_V1`.

All 10 deterministic hash folds completed successfully. Every fold passed the exact-source, target-firewall, prelabel, provenance, and artifact checks. The density-synchronous mechanism was active in all 10 folds.

## Frozen aggregate comparison

Across 20 year-fold panels (10 leave-one-hash-bucket-out fits × GMN 2022/2023):

- total recovered@50: recurrent-EOM `910` → density-synchronous `910` — PASS no-regression;
- total recovered@100: recurrent-EOM `1761` → density-synchronous `1761` — **FAIL strict-improvement gate**;
- mean top-100 dominant precision: `0.7781536639305083` → `0.7786466016031524` (delta `+0.0004929376726440`) — PASS;
- mean MRR: `0.023045967245647316` → `0.023081599246733312` (delta `+0.0000356320010860`) — PASS;
- median top-500 fragmentation: `1.0` → `1.0` — PASS;
- mechanism-active folds: `10/10` — PASS.

Only one frozen gate fails, but the protocol required every gate. The binding robustness verdict is therefore negative.

## Why the @100 aggregate tied

The recovery effect is unstable across deterministic training perturbations rather than uniformly harmful:

- fold 0: density-synchronous recovered@100 improves by `+1` in 2022 and `+1` in 2023;
- fold 6: density-synchronous recovered@100 regresses by `-1` in 2022 and `-1` in 2023;
- the other eight folds: recovered@100 is tied in both years.

The `+2` and `-2` changes cancel exactly across all 20 year-fold panels.

The quality metrics are somewhat more stable: aggregate mean precision and aggregate mean MRR both improve, although individual tiny MRR/precision regressions occur in some folds. Thus density synchrony appears to be a weak ranking-quality improvement on average, but the original full-data strict fixed-budget recovery improvement is not robust to a deterministic ~10% change in the exposed GMN training sample.

## Scientific interpretation

This result does **not** invalidate or rewrite the binding full-data #1263 result `PASS_DENSITY_SYNCHRONOUS_RECURRENT_EOM_V1_GMN_DEVELOPMENT`. That experiment remains a valid preregistered comparison on the full permanent GMN development corpus.

It **does** materially reduce confidence that #1263 has a reproducible recovery advantage over recurrent-EOM v1. The strongest defensible statement is now:

> Density-synchronous recurrent-EOM is the current full-GMN development champion and improves average ranking quality under deterministic training perturbations, but its strict recovered@100 advantage is sample-sensitive and failed the preregistered robustness criterion.

This is TRAIN/DEVELOPMENT robustness evidence only. It is not validation or external generalization.

## Permanent closure / no rescue

No alternate fold count, hash function, random seed, holdout fraction, fold weighting, omitted fold, aggregate statistic, recovery budget, precision definition, MRR definition, or other post-result rescue is authorized for this robustness question.

SonotaCo 2013/2014 and AMOS 2023/2024 were not accessed. Protected `[20°,55°]`, OrbitTrace target information/events, ASFN, EFN, MAARSY, and DMS remained inaccessible to this experiment.
