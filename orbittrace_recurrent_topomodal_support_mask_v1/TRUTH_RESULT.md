# OrbitTrace recurrent-TopoModal support mask v1 — binding truth result

## 🔴 NEGATIVE — EXACT SUPPORT MASK CLOSED

Authoritative run: `32070872999`

Execution commit: `dcf7461fa1be73fba2e742c76a9d0d1a284a9bab`

Truth artifact: `9301740793`

Truth artifact digest: `sha256:e2c92111294257022884f09c94a72e8c053b3bb7f5489c13ddd8517bda694dbe`

Pretruth artifact: `9301658429`

Pretruth artifact digest: `sha256:53807a9e4014eb1006c20a734b16d8cee5a61a930faec4a0ec8fd067a37c4627`

Immutable support-mask prelabel SHA-256: `aba90f4f16b29b01d8087f351c771f34c91dc119bba59b0d332fcb8e299d9b0c`

Exact verdict:

`FAIL_RECURRENT_TOPOMODAL_SUPPORT_MASK_V1`

The two-stage workflow completed the frozen scientific contract successfully. The zero-label pretruth stage passed all structural gates and preserved the exact Recurrent-EOM rank order and candidate budget in all eight panels. Truth was opened only after that PASS. The truth evaluator scored only the sealed support-mask catalogue; no ranking, membership rule, threshold, budget, or gate was selected from the outcome.

## Fine sparse scale — denominator 1024

| aggregate | recurrent-EOM | support mask |
|---|---:|---:|
| qualified matches | 20 | **28** |
| recovered@25 total | 20 | **28** |
| recovered@50 total | 20 | **28** |
| recovered@100 total | 20 | **28** |
| recovered@500 total | 20 | **28** |
| mean top-100 dominant precision | 0.3530315709574533 | **0.5192476250601251** |
| mean MRR | **0.6959325396825397** | 0.5641617063492064 |
| mean median-fragmentation | 1.0 | 1.0 |

Panelwise qualified recovery: `8/8` nonlower, `5/8` strict wins, `0/8` losses.

## Coarse sparse scale — denominator 128

| aggregate | recurrent-EOM | support mask |
|---|---:|---:|
| qualified matches | 94 | **119** |
| recovered@25 total | 87 | **112** |
| recovered@50 total | 94 | **119** |
| recovered@100 total | 94 | **119** |
| recovered@500 total | 94 | **119** |
| mean top-100 dominant precision | 0.3396191653933494 | **0.43810183600572117** |
| mean MRR | **0.23584530975502274** | 0.2063089115865191 |
| mean median-fragmentation | 1.0 | 1.0 |

Panelwise qualified recovery: `8/8` nonlower, `8/8` strict wins, `0/8` losses.

## Frozen gates

Passed `8/10`. Failed only:

- fine mean MRR not lower;
- coarse mean MRR not lower.

Every recovery-total, panelwise recovery, precision, and fragmentation gate passed.

## Interpretation

The exact global support-mask architecture is permanently closed. Preserving Recurrent-EOM's candidate order while replacing each parent membership by the union of all TopoModal-supported events does not preserve enough early-rank shower representation to clear the MRR gate.

The result is informative relative to the already-closed recurrent-orphan completion catalogue. Support mask improves coarse qualified recovery (`119` vs `114`) but has lower MRR at both scales (`0.5642` vs `0.5707` fine; `0.2063` vs `0.2152` coarse). Therefore simply retaining more TopoModal-supported events inside the same parent is not the missing solution. The productive signal appears to involve which modal substructure represents a parent, not merely how much parent halo is removed.

Do not rescue this result by changing support 4, introducing overlap/Jaccard/containment thresholds, choosing a subset of support children, weighting children, blending parent and mask events, changing fallback behavior, reranking candidates, inserting support-only candidates, changing K, tuning per scale/bucket/year, or relaxing MRR/other gates.

Protected solar longitude `[20°,55°]` remained excluded. OrbitTrace target information/events, SonotaCo 2013/2014, ASFN/EFN event rows, AMOS, MAARSY, and DMS were not accessed.
