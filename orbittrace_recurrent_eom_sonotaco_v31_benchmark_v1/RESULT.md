# Recurrent-EOM HDBSCAN v1 — binding SonotaCo/v31 benchmark result

**Scientific classification: POSITIVE.**

Binding run: `31829200215`  
Artifact: `9230008341`  
Artifact digest: `sha256:a0eb8aafc88f3e963a3e788294f1a82bcc6612c26b587f5e12861a579486d110`  
Execution commit: `7e788a57be45e5393374caff8280abc377b2b0b4`  
Frozen pretruth SHA-256: `c6afbc0c3443b6c34e3f90b0f63453a0a35bfae3f3c84ffe8a479f8f50cffeef`  
Binding result SHA-256: `c2395a86be5ba8a8b801210ac6e64b97c446e724991207aef85062ee00b89f12`

The first workflow attempt `31829046495` failed before HDBSCAN fitting and before any pretruth payload existed because repository root was absent from Python module search path. Truth and v31 were not downloaded. Commit `7e788a57be45e5393374caff8280abc377b2b0b4` changed only workflow `PYTHONPATH`; the frozen recurrent-EOM implementation, benchmark protocol, benchmark source, row bytes, comparator budgets, and gates were unchanged.

## Pretruth freeze

The repaired run completed all candidate generation before downloading exposed shower truth or the v31 result.

### Sugar-matched route

- pooled accessible events: 34,038
  - 2013: 18,638
  - 2014: 15,400
- vanilla-HDBSCAN selected nodes: 150
- recurrent-EOM selected nodes / candidates: 144
- mechanism active: yes
- frozen candidate-order SHA-256: `38e2f952b91d5f72ef1d7275d1e586d378d5f4d4dff0f3499af8dfde480faf00`

### HDBSCAN-matched route

- pooled accessible events: 29,311
  - 2013: 16,028
  - 2014: 13,283
- vanilla-HDBSCAN selected nodes: 132
- recurrent-EOM selected nodes / candidates: 123
- mechanism active: yes
- frozen candidate-order SHA-256: `1fcea76bd19ffc24b08fb93525bd3802a2a3ef0013f61cd1d96f26f97a69d678`

No truth, v31 score, comparator result, or shower label entered memberships or rank order.

## Exact matched comparison

The primary preregistered gate required recurrent-EOM to have **strictly greater macro-F1 and at least equal recovered F1>0.5 count relative to exact v31 on all four panels**.

| Panel | Budget | v31 macro-F1 | Recurrent-EOM macro-F1 | Delta | v31 recovered | Recurrent-EOM recovered | Result |
|---|---:|---:|---:|---:|---:|---:|---|
| Sugar 2013 | 34 | 0.2719801488 | **0.3752906816** | **+0.1033105328** | 16 | **23** | **WIN** |
| Sugar 2014 | 46 | 0.3152904195 | **0.4377312230** | **+0.1224408034** | 17 | **24** | **WIN** |
| HDBSCAN 2013 | 11 | 0.1488803737 | **0.1914598192** | **+0.0425794455** | 9 | **11** | **WIN** |
| HDBSCAN 2014 | 9 | 0.1519812377 | **0.1685878550** | **+0.0166066173** | 9 | 9 | **WIN** |

Primary verdict:

`PASS_RECURRENT_EOM_SONOTACO_V31_SUPERIORITY_V1`

**4/4 v31 panels passed.**

## Literature comparator reporting

The same frozen recurrent-EOM outputs also passed the existing literature pair gate on **all four panels**:

- Sugar 2013 literature: 0.2037265747 / 13; recurrent-EOM: **0.3752906816 / 23**.
- Sugar 2014 literature: 0.2590152773 / 15; recurrent-EOM: **0.4377312230 / 24**.
- HDBSCAN 2013 literature: 0.1681302505 / 10; recurrent-EOM: **0.1914598192 / 11**.
- HDBSCAN 2014 literature: 0.1568959558 / 9; recurrent-EOM: **0.1685878550 / 9**.

Thus recurrent-EOM achieved **4/4 literature panel wins** under the established matched budgets/evaluator.

## Interpretation

This result is a strong exposed-development portability success. Combined with the earlier target-excluded GMN 2022+2023 PASS, recurrent-EOM HDBSCAN v1 is now the methodology parent for subsequent untouched validation work.

SonotaCo 2013/2014 remains **EXPOSED DEVELOPMENT ONLY**. This result is not described as pristine external validation.

No SonotaCo-informed parameter change, rank rescue, threshold change, membership edit, or second search is authorized for recurrent-EOM v1.

## Firewall

- protected solar longitude `[20°,55°]` remained removed;
- `target_information_access=false`;
- `target_region_events_accessed=false`;
- `maarsy_scientific_access=false`;
- `dms_scientific_access=false`;
- `post_result_parameter_search=false`.
