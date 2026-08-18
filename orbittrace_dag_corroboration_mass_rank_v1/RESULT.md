# DAG corroboration-mass rank v1 — binding result

## Status

**FAIL_DAG_CORROBORATION_MASS_RANK_V1 — CLOSED**

The first technically valid truth execution completed successfully and is binding.

## Binding execution

- workflow run: `32186903201`
- science execution commit: `9d89f790576b6d884eff429098fb13a294fc6196`
- pretruth artifact: `9342776227` (`orbittrace-dag-corroboration-mass-rank-v1-pretruth`)
- pretruth artifact digest: `sha256:fb7eaa1079034cf5567305b782a4a7b3a0b3a30ace8dbebae22fdd60d34716af`
- truth artifact: `9342861268` (`orbittrace-dag-corroboration-mass-rank-v1-truth`)
- truth artifact digest: `sha256:200e08e8796636517a1ba7e851d8df43293b67267ced1fb40d0dd4814f58a046`
- prelabel SHA-256: `b4ac17e797074bb21e3ac734def1358953bc2544807e3a5801e0e2fcc8b9666c`
- pretruth SHA-256: `6c5188f85853f0867a3d7848bdf627de54149e3b50c2065094be8ff02aeb20be`
- truth/result SHA-256: `5ef04a01ba70dc7ba6b0931fa4f70ad3530d157d1da61f0da8fc0c36cb2d95fb`
- frozen protocol blob: `6d8e94b6d61f3301df01892f2796c94a0a70e5b7`

Pretruth verdict was `PASS_DAG_CORROBORATION_MASS_RANK_V1_PRETRUTH`; all 13 zero-label authorization gates passed before truth.

## Binding result

The successor preserved every raw support-resolved TopoModal membership exactly and changed only ranking using the frozen all-edge DAG corroboration-mass score.

### d=128

Native TopoModal:
- qualified total `142`;
- zero-filled MRR mean `0.0767498828458128`;
- precision mean `0.5648829520963607`;
- recovered@25 total `132`;
- fragmentation mean `1.0`.

DAG corroboration-mass rank:
- qualified total `118`;
- zero-filled MRR mean `0.06376559862638335`;
- precision mean `0.5280662516745174`;
- recovered@25 total `98`;
- fragmentation mean `1.0`;
- qualified nonlower vs native in `0/8` annual panels.

The ranking loses materially to the native TopoModal order across recovery, early recovery, MRR, and precision.

### d=1024

Native TopoModal:
- qualified total `31`;
- zero-filled MRR mean `0.4062624007936507`;
- precision mean `0.5971047679172679`;
- fragmentation mean `1.0`.

DAG corroboration-mass rank:
- qualified total `30`;
- zero-filled MRR mean `0.39716907596371875`;
- precision mean `0.5809589345839345`;
- fragmentation mean `1.0`;
- qualified nonlower vs native in `7/8` annual panels.

The effect is smaller at d=1024 but still regresses native TopoModal in qualified recovery, MRR, and precision.

## Gate outcome

Only two of the twelve truth gates passed:

- fine zero-filled MRR remained above recurrent-EOM;
- fine fragmentation did not worsen.

The remaining ten gates failed, including both strict native-MRR improvement gates and all coarse recovery/quality gates.

Exact verdict: `FAIL_DAG_CORROBORATION_MASS_RANK_V1`.

## Interpretation

The many-to-many DAG is structurally useful, but **linear event-mass expectation of recurrent-parent rank is not a useful standalone ordering statistic for full TopoModal candidates**. At d=128 it systematically promotes recurrently covered structure at the expense of the native modal ordering that carries stronger shower recovery and early-ranking information.

Together with the separately binding raw-atom result, the current evidence separates two failures:

- direct DAG atoms are too fine as reportable candidates;
- preserving full TopoModal candidates but replacing native order with global corroboration mass is too aggressive as a ranking rule.

This result does not weaken the binding zero-label DAG stability result or the fixed-scale TopoModal flagship evidence. It closes only this exact all-edge corroboration-mass ranking family.

## Closure

No rescue is authorized through score blends, alternative recurrent-priority transforms, max/min/product/geometric-mean aggregation, atom Jaccard/degree/entropy/persistence terms, thresholds, quotas, parent selection, candidate edits, K/gate changes, or learned reranking.

Any future method must be scientifically distinct and separately frozen before truth.

Protected `[20°,55°]`, OrbitTrace target information/events, SonotaCo, ASFN/EFN event rows, AMOS, MAARSY, and DMS remained inaccessible. No post-result parameter search was performed.
