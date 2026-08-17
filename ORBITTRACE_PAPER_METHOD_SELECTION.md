# OrbitTrace paper-method selection

## Selected method

**Recurrent-EOM HDBSCAN v1** is the preferred OrbitTrace paper/development methodology.

Exact recurrent-EOM kernel Git blob:

`30ac3fa3bc47910370df528fcf3ae8ecb6277b47`

This selection is based on the combined target-excluded GMN development evidence, exposed SonotaCo 2013/2014 benchmark evidence, and the direct comparison against the later density-synchronous refinement (#1263).

## 🟢 Positive evidence for recurrent-EOM

Recurrent-EOM passed its frozen target-excluded GMN 2022+2023 development gate.

Its frozen exposed SonotaCo benchmark then beat exact v31 on all four established matched panels and also beat the corresponding frozen literature comparator on all four panels:

| Panel | recurrent-EOM macro-F1 / recovered | v31 macro-F1 / recovered |
|---|---:|---:|
| Sugar 2013 | `0.3752906816276458 / 23` | `0.2719801488280529 / 16` |
| Sugar 2014 | `0.43773122295664196 / 24` | `0.31529041952487225 / 17` |
| HDBSCAN 2013 | `0.1914598192215768 / 11` | `0.14888037368183737 / 9` |
| HDBSCAN 2014 | `0.1685878550176112 / 9` | `0.15198123772301594 / 9` |

Binding recurrent-EOM SonotaCo run: `31829200215`.

Artifact: `9230008341`.

Result SHA-256:

`c2395a86be5ba8a8b801210ac6e64b97c446e724991207aef85062ee00b89f12`

SonotaCo is **EXPOSED DEVELOPMENT / VALIDATION BENCHMARK**, not pristine external validation.

## 🟡 Direct comparison against #1263 density-synchronous recurrent-EOM

#1263 was a scientifically valid parameter-free refinement and passed its frozen full-GMN gate. Its strict recovered@100 gain, however, was not robust under the separately frozen 10-fold deletion diagnostic: aggregate recovered@100 was `1761 -> 1761`.

The direct owner-authorized SonotaCo benchmark in PR #1269 then compared exact recurrent-EOM and exact #1263 density-sync on the same label-free rows, same pooled hierarchy per route, same truth, same fixed candidate budgets, and same Hungarian evaluator.

Binding direct run: `31889652785`.

Artifact: `9248203777`.

Artifact digest:

`sha256:a9e3b7895b43465181d94376b873c04ddc70d815d325930a0a49332a144a23d0`

Pretruth SHA-256:

`051ea9a213c7a72b93875e8ddd6716aa884e802377c293b7b6cf4a6de5ca5609`

Result SHA-256:

`00b9defa3a07fc1396b8d9dcbc3bd62da44dc95e7245ad44d7bdedf375570f5c`

Exact verdict:

`NEUTRAL_DENSITY_SYNC_SONOTACO_DIRECT_BENCHMARK_V1`

The four direct results were exact ties:

| Panel | recurrent-EOM | #1263 density-sync | Delta |
|---|---:|---:|---:|
| Sugar 2013 | `0.3752906816276458 / 23` | `0.3752906816276458 / 23` | `0 / 0` |
| Sugar 2014 | `0.43773122295664196 / 24` | `0.43773122295664196 / 24` | `0 / 0` |
| HDBSCAN 2013 | `0.1914598192215768 / 11` | `0.1914598192215768 / 11` | `0 / 0` |
| HDBSCAN 2014 | `0.1685878550176112 / 9` | `0.1685878550176112 / 9` | `0 / 0` |

The density-synchronous mechanism was active, but both methods selected the exact same node sets on both SonotaCo routes. Their first complete-order difference occurred only at rank 42. Sugar top-34 was identical; Sugar top-46 contained the same candidate set; HDBSCAN top-9 and top-11 were identical. Therefore the established evaluation panels received no benefit from the added density-synchronous criterion.

## Final decision

Choose **recurrent-EOM HDBSCAN v1** over #1263 for the paper because:

1. it already has a positive frozen GMN development result;
2. it has 4/4 superiority versus v31 on the established SonotaCo benchmark;
3. it has 4/4 superiority versus the matched literature comparators;
4. #1263's extra full-GMN recovery gain is sample-sensitive under the frozen deletion diagnostic;
5. #1263 produces zero gain over recurrent-EOM on all four direct SonotaCo validation panels;
6. recurrent-EOM is the simpler method, so the evidence favors it by parsimony.

This conclusion does not erase #1263's positive full-GMN result. It says only that the added density-synchronous criterion is not justified as the preferred paper method by the combined evidence.

## Closed paths

Do not restart:

- the #1263 density-sync successor search;
- alternate density-sync weights/minima/alignment/smoothing/blends;
- AMOS outreach or AMOS data acquisition for this method-selection goal;
- external-dataset shopping;
- result-informed parameter or threshold rescue.

Further OrbitTrace work should treat recurrent-EOM as fixed and focus on characterization, comparison, figures, and manuscript claims rather than another methodology-search loop.

## Scientific firewall

Protected solar longitude `[20°,55°]` remains inaccessible. OrbitTrace target information/events, MAARSY and DMS remain scientifically inaccessible. The direct method-selection benchmark used only the already-exposed SonotaCo benchmark outside the protected interval.
