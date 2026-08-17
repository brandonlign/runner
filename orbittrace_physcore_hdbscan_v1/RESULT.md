# OrbitTrace PhysCore-HDBSCAN v1 — binding exposed-development result

## 🟢 POSITIVE

Binding workflow: `31988198562`

Pretruth artifact:
- ID: `9274430043`
- digest: `sha256:17ee20a454db09839470732a18a6d5951cfc90d4d697ed8d40f8ceae51f53d55`

Binding result artifact:
- ID: `9274439445`
- digest: `sha256:e836b6e0840d41c2d69f91d4e8e5f8de5629a910365746a8407eabf69be97364`
- `RESULT.json` SHA-256: `497888d38f8019750c5004d11ae2cda7fea0bdee3a8e6c357196af846c04b5ff`

Exact verdict:

`PASS_PHYSCORE_HDBSCAN_V1_DEVELOPMENT`

| Year | PhysCore macro-F1 | Published HDBSCAN macro-F1 | PhysCore recovered F1>0.5 | HDBSCAN recovered F1>0.5 | Panel |
|---|---:|---:|---:|---:|---|
| 2013 | **0.1756351130** | 0.1681717489 | **10** | **10** | **WIN** |
| 2014 | **0.1688317479** | 0.1568959558 | **9** | **9** | **WIN** |

Absolute macro-F1 gains are `+0.0074633641` in 2013 and `+0.0119357921` in 2014, corresponding to approximately `+4.44%` and `+7.61%` relative improvement over the exact published HDBSCAN scores. No recovered shower was lost.

## Scientific interpretation

The user-motivated pivot to build on the stronger published HDBSCAN parent succeeds on its first frozen test. PhysCore leaves the exact published HDBSCAN proposal catalogue, family count, and family order intact, then applies only a previously frozen meteor-physical coherence regularizer to family membership. This improves matched macro-F1 in both exposed SonotaCo years without reducing recovered-shower count.

The improvement therefore comes from membership regularization rather than changing HDBSCAN hyperparameters, selecting a different HDBSCAN hierarchy, adding candidate slots, or post-result threshold tuning.

This is the first OrbitTrace-owned successor in the current literature-facing sequence to satisfy the frozen direct superiority gate against the exact published 2025 catalogue-HDBSCAN implementation in both years.

## Claim boundary

Supported at this stage:

> On the exposed SonotaCo 2013/2014 development benchmark, a fixed meteor-physics membership regularizer applied to the exact published catalogue-HDBSCAN output improved matched macro-F1 in both years while preserving every recovered shower.

Not yet supported:
- universal superiority across all surveys;
- pristine external validation;
- superiority to every other literature comparator under a direct matched PhysCore benchmark;
- any result-informed change to the frozen PhysCore rule.

The exact v1 method is now frozen. Further work may only characterize or benchmark these exact frozen bytes; no radius, scale, support, peeling, fallback, HDBSCAN setting, family order, metric, truth mapping, or pass-gate modification is authorized from this result.

## Firewall

The run preserved:
- all candidate outputs and exact HDBSCAN parent outputs frozen before truth;
- protected solar longitude `[20°,55°]` excluded;
- `truth_access_before_pretruth=false`;
- `target_information_access=false`;
- `target_region_events_accessed=false`;
- `maarsy_scientific_access=false`;
- `dms_scientific_access=false`;
- `post_result_parameter_search=false`;
- SonotaCo 2013/2014 treated as `EXPOSED_DEVELOPMENT_ONLY`.
