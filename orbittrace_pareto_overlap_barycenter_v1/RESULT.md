# OrbitTrace overlap-barycenter Pareto v1 — binding result

## Verdict

**FAIL_PARETO_OVERLAP_BARYCENTER_V1 — CLOSED (4/5 truth gates).**

Binding run: `32104258164`

Pretruth artifact: `9312658564`, digest `sha256:3be325d33501278c69245a21c6d10932db661b60d129c331472dcea7587c0b96`

Truth artifact: `9312714112`, digest `sha256:5790c3abd223be22c137a112709e5d76d46f6409eec3b60b090e93e702108a19`

Immutable prelabel SHA-256: `af97b5b12e54db12c226c84fb0f1391b9895abcf94c524adfc8ffa1813ce79c0`

Truth result SHA-256: `12ccb3edfa82212d0714476d818ee4478b9f7d1a8e359c81c0488f966864956a`

Frozen protocol commit: `e763792b08c89991ec39838b8385d92797962a90`
Protocol blob: `5369b1816bf7d71597050634b25627a934f68ea7`
Builder blob: `ff6c984b79db363efa756351087ad0f088b8c5e7`
Truth evaluator blob: `52a67feb1f0effc76d99bfcf30e9364a47a48a37`
Activation commit: `6dcaa450bad6003c111a31c4111183e59c84a785`

## Pretruth structural result

**PASS 12/12.**

The mechanism reproduced the positive d=128/d=1024 Pareto-prominence ordering exactly on all eight frozen sparse panels. At d=64 it handled 8 genuine multi-parent TopoModal candidates without modifying membership:

- bucket 0: n=11,375, K=61, retained=128, multi-parent=2
- bucket 1: n=11,645, K=59, retained=141, multi-parent=3
- bucket 2: n=11,493, K=59, retained=134, multi-parent=1
- bucket 3: n=11,549, K=58, retained=127, multi-parent=2

All four panels retained capacity >= K. The protected `[20°,55°]` solar-longitude interval remained excluded and no truth entered candidate construction or ranking.

## Binding d=64 truth result

| Metric | Recurrent-EOM | overlap-barycenter Pareto |
|---|---:|---:|
| qualified total | 155 | **196** |
| recovered@25 total | **116** | 103 |
| recovered@50 total | 149 | **176** |
| recovered@100 total | 155 | **196** |
| recovered@500 total | 155 | **196** |
| top-100 dominant precision mean | 0.3259689855 | **0.4532371739** |
| zero-filled MRR mean | **0.04071839151** | 0.03984252084 |
| historical conditional MRR mean | **0.1593318520** | 0.1246029248 |
| reciprocal-rank mass | **24.49569816** | 23.99270468 |
| fragmentation mean | 1.0 | 1.0 |

Qualified recovery was nonlower in 7/8 annual panels.

Passed gates:
- qualified total not lower;
- qualified recovery nonlower in >=6/8 panels;
- top-100 precision not lower;
- fragmentation not higher.

Failed gate:
- **mean zero-filled eligible-query MRR not lower**.

## Scientific interpretation

The dense-scale failure of unique-parent Pareto was genuinely fixable at the correspondence level: overlap-weighted parent-rank barycenters preserve the successful sparse method exactly and remove the d=64 structural abort while strongly improving total recovery and precision.

However, collapsing a many-parent correspondence to one overlap-weighted scalar rank still perturbs early Pareto layers enough to lose reciprocal-rank mass. The loss is small in zero-filled MRR (~2.15%) but binding. Recovery at rank 25 also drops even though recovery at 50/100/500 improves strongly, locating the remaining problem specifically in earliest-slot ordering rather than candidate quality/capacity.

This exact barycenter rule is closed. Do not rescue it with best-parent selection, overlap powers, Jaccard weights, unmatched-event penalties, harmonic/geometric means, thresholds, or result-informed transforms.

A legitimate successor must represent multi-parent correspondence without forcing it into a single scalar that can globally cascade Pareto layers, while reducing exactly to the original successful unique-parent Pareto relation in the sparse regime.