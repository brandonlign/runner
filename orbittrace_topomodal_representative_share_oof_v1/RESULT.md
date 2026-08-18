# OrbitTrace TopoModal representative-share OOF v1 — binding result

## 🔴 Binding verdict: FAIL exact architecture

The first execution attempt, run `32085559553`, is preserved as a technical no-result: all frozen input/provenance checks passed, but the additional zero-filled-MRR adapter attempted `int(None)` for unrecovered eligible showers before any result JSON or gate verdict existed.

The evaluator-only repair was frozen in `TECHNICAL_REPAIR_01.md` and implemented only as `technical_repair_01_wrapper.py`; the original scientific runner remained byte-identical.

The first technically valid binding endpoint is:

- run: `32086031907`
- execution head: `abbad4592e01f6666986c2b1703235fd115cae2e`
- artifact: `9306797122`
- artifact ZIP digest: `sha256:c277752e912b5c8f71e9376096235125c4b6dd666f184bfd0e200f0334463d40`
- result SHA-256: `dfa395e969a260ef82a25cd7296c841f525e8c090c9eea05b1b234b155bf6b6d`
- exact predecessor pretruth SHA-256: `22ee242d16e73c553d0e2041e55a8d938963c504a824797e92119d15b4bab7ba`

Exact verdict:

`FAIL_TOPOMODAL_REPRESENTATIVE_SHARE_OOF_V1`

The workflow completed the full frozen 12-gate contract and provenance upload successfully. Candidate capacity passed in all eight sparse panels. Protected `[20°,55°]`, OrbitTrace target information/events, SonotaCo, ASFN/EFN, AMOS, MAARSY, and DMS were not accessed by this experiment.

## Fine sparse scale — denominator 1024

| aggregate | Recurrent-EOM | representative-share TopoModal |
|---|---:|---:|
| qualified matches | 20 | **31** |
| recovered@25 | 20 | **31** |
| recovered@50 | 20 | **31** |
| recovered@100 | 20 | **31** |
| recovered@500 | 20 | **31** |
| mean top-100 dominant precision | 0.3530315709574533 | **0.5959589345839346** |
| historical conditional MRR | **0.6959325396825397** | 0.5399553571428571 |
| zero-filled eligible-query MRR | 0.3308496315192744 | **0.40583723072562355** |
| mean median fragmentation | 1.0 | 1.0 |

Qualified recovery is nonlower in 8/8 bucket-year panels and strictly higher in 6/8.

Fine gates: qualified-total PASS; panelwise PASS; zero-filled MRR PASS; precision PASS; fragmentation PASS; **historical conditional MRR FAIL**.

## Coarse sparse scale — denominator 128

| aggregate | Recurrent-EOM | representative-share TopoModal |
|---|---:|---:|
| qualified matches | 94 | **138** |
| recovered@25 | 87 | **125** |
| recovered@50 | 94 | **138** |
| recovered@100 | 94 | **138** |
| recovered@500 | 94 | **138** |
| mean top-100 dominant precision | 0.3396191653933494 | **0.5596573597516694** |
| historical conditional MRR | **0.23584530975502274** | 0.18492944432304148 |
| zero-filled eligible-query MRR | 0.06440922700317128 | **0.07557745653492765** |
| mean median fragmentation | 1.0 | 1.0 |

Qualified recovery is nonlower in 8/8 bucket-year panels and strictly higher in 8/8.

Coarse gates: qualified-total PASS; panelwise PASS; zero-filled MRR PASS; precision PASS; fragmentation PASS; **historical conditional MRR FAIL**.

## Mechanism interpretation

Representative-share supervision is active and materially improves the TopoModal OOF successor relative to Recurrent-EOM on the retrieval metric that assigns unrecovered eligible showers reciprocal rank zero. It also preserves the candidate generator's large recovery and purity gains with fragmentation 1.0.

However, it does not satisfy the project's historical conditional-MRR gates. Therefore the exact panelwise/yearwise F1-share target, same-fold ExtraTrees, same antichain, and same utility order are permanently closed as a promotion architecture. Do not tune share exponents, blend raw F1 and share targets, change folds/capacities, or alter the antichain/ranking as a rescue.

A separate sealed-result-only metric-geometry audit should determine whether the remaining conditional-MRR deficit reflects actual reorderable rank headroom or the mathematical behavior of conditioning the mean only on recovered showers. That audit cannot reopen this failed exact architecture.