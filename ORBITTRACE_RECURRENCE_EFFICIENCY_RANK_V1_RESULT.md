# Recurrent-EOM recurrence-efficiency rank v1 — binding result

## 🔴 NEGATIVE — frozen ranking successor fails no-regression gate

Binding GitHub Actions run: `31994594592`.

Execution head: `bb435f6c0e9f70f21ad6c200d243cd16d5eb3618`.

Artifact: `9276413494`.

Artifact digest: `sha256:c977913d26dcaf53c8b55dae42e975490fb8501afc71e4a329a9294b8125b08f`.

Frozen successor pretruth SHA-256: `a75471ec88d7a1939eec2853170944cf7034ea58d239dc603d8e0e3d95cb919b`.

Binding result JSON SHA-256: `8621b3d3af3765f11e8b0694e0cad734ca910faa5fd10698140495565a5ce122`.

Exact verdict:

`FAIL_RECURRENT_EOM_RECURRENCE_EFFICIENCY_RANK_V1`

The candidate family universe and event memberships remained exactly identical to recurrent-EOM. The recurrence-efficiency order was active and changed ranking only.

### Matched exposed SonotaCo results

| Panel | recurrent-EOM | recurrence-efficiency | recovered parent → successor | Outcome |
|---|---:|---:|---:|---|
| Sugar 2013 | `0.3752906816` | `0.3752906816` | `23 → 23` | tie |
| Sugar 2014 | `0.4377312230` | `0.4427542223` | `24 → 25` | improvement |
| HDBSCAN 2013 | `0.1914598192` | `0.1721919965` | `11 → 10` | regression |
| HDBSCAN 2014 | `0.1685878550` | `0.1672338387` | `9 → 9` | macro-F1 regression |

The frozen promotion gate required macro-F1 and recovered-count non-regression on all four panels plus at least one strict improvement. Although Sugar 2014 improved by `+0.0050229993` macro-F1 and `+1` recovered shower, both HDBSCAN-panel macro-F1 values regressed and HDBSCAN 2013 lost one recovered shower.

## Interpretation and closure

The result confirms that recurrent-EOM's ranking contains improvable structure—the same parameter-free reranker promoted an additional recoverable Sugar-2014 shower—but a global penalty based on recurrent-to-pooled stability efficiency is not robust across the matched row universes.

This exact score family is closed. No alternate power, denominator transform, raw-score blend, rank fusion, threshold, route-specific exception, budget-specific exception, or result-informed second attempt is authorized from this outcome.

Recurrent-EOM HDBSCAN v1 remains the preferred catalogue-scale method.

SonotaCo 2013/2014 was exposed development only. Protected `[20°,55°]`, OrbitTrace target information/events, AMOS, MAARSY, DMS, and pristine external endpoints were not accessed. No post-result parameter search was performed.
