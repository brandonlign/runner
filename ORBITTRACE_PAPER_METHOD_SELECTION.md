# OrbitTrace paper-method selection

## Selected method

**Recurrent-EOM HDBSCAN v1** is the preferred OrbitTrace paper/development methodology.

Exact recurrent-EOM kernel Git blob:

`30ac3fa3bc47910370df528fcf3ae8ecb6277b47`

This selection is based on the combined target-excluded GMN development evidence, exposed SonotaCo 2013/2014 benchmark evidence, the direct comparison against the later density-synchronous refinement (#1263), and the subsequent independently frozen cross-hierarchy DAG exploration summarized below.

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

## 🟢 structural / 🔴 detector — cross-hierarchy refinement DAG exploration

A later, separately frozen zero-label experiment asked whether the many-to-many correspondence between support-resolved TopoModal candidates and recurrent-EOM candidates could be represented more faithfully by their exact nonempty intersections rather than by forced unique parent ownership.

Binding structural run `32185851992` passed all nine preregistered gates. Across eight nested thinning transitions, common-refinement atoms had pooled mean symmetric stability `0.8066370721`, versus `0.7917895143` for TopoModal and `0.6917863083` for recurrent-EOM, and strictly beat both parents on `7/8` transitions. This remains valid positive structural evidence.

Per the frozen protocol, that structural PASS authorized exactly one truth-scored detector-extraction follow-up. The follow-up used every exact nonempty DAG atom as a candidate and reused the already-successful two-objective Pareto-prominence ordering without atom-size filters, merge rules, overlap thresholds, learned reranking, or result-informed parameter choices.

The first technically valid complete truth execution was binding run `32189372993`, artifact `9343696639`, result SHA-256 `d4e11a82ca54bb754b229f085744133859f7174d15a609d39036fd1af4300064`, with exact verdict:

`FAIL_DAG_ATOM_PARETO_PROMINENCE_V1`

The historical sparse Pareto comparator reproduced exactly before interpretation. The firewall remained intact and no post-result parameter search occurred.

At d=64, raw atomization increased pooled qualified recoveries from `153` to `185` and mean top-100 dominant precision from `0.3254283129943979` to `0.4624144734944088`, but mean zero-filled MRR fell from `0.04064735821202093` to `0.03851358495146374`, violating the frozen dense no-regression contract. At d=128 the atom successor produced `125` qualified recoveries versus `127` for the already-successful sparse Pareto comparator and slightly lower zero-filled MRR (`0.06670142141174568` versus `0.06716051462349848`). At d=1024 it produced `28` versus `30` qualified recoveries, with slightly lower zero-filled MRR and precision. The strict sparse-added-value gate also failed.

Interpretation: the common-refinement representation is genuinely more thinning-stable, but **using every refinement atom directly as a reportable detector cluster is too fine-grained under the frozen ranking/evaluation contract**. Structural stability therefore does not imply optimal detector granularity. The exact DAG-atom detector is permanently closed and must not be rescued with atom-size cutoffs, component unions, rank weights, quotas, learned reranking, or other result-informed variants.

This negative detector result does not weaken the already-binding recurrent-EOM evidence and does not justify replacing the selected paper method.

## Final decision

Choose **recurrent-EOM HDBSCAN v1** as the paper method because:

1. it already has a positive frozen GMN development result;
2. it has 4/4 superiority versus v31 on the established SonotaCo benchmark;
3. it has 4/4 superiority versus the matched literature comparators;
4. #1263's extra full-GMN recovery gain is sample-sensitive under the frozen deletion diagnostic;
5. #1263 produces zero gain over recurrent-EOM on all four direct SonotaCo validation panels;
6. the independently motivated cross-hierarchy DAG is structurally useful, but its one authorized raw-atom detector extraction fails the binding truth promotion contract;
7. recurrent-EOM remains the simplest method with the strongest combined truth-scored evidence, so the evidence favors it by parsimony.

This conclusion does not erase #1263's positive full-GMN result or the cross-hierarchy DAG's positive zero-label stability result. It says that neither later mechanism has earned replacement of recurrent-EOM as the preferred truth-scored paper methodology.

## Closed paths

Do not restart:

- the #1263 density-sync successor search;
- alternate density-sync weights/minima/alignment/smoothing/blends;
- the exact DAG-atom + Pareto-prominence detector;
- atom-size thresholds, including `>=4` filtering, as a rescue of the failed DAG detector;
- result-informed component unions/contractions or parent restoration for the failed DAG detector;
- overlap/Jaccard thresholds, degree penalties, per-parent quotas, or rank-fusion variants for the failed DAG detector;
- learned reranking of the failed DAG detector;
- AMOS outreach or AMOS data acquisition for this method-selection goal;
- external-dataset shopping;
- result-informed parameter or threshold rescue.

Further OrbitTrace paper work should treat recurrent-EOM as fixed and focus on characterization, comparison, figures, and manuscript claims rather than another methodology-search loop unless a genuinely distinct hypothesis is independently justified and separately authorized before truth.

## Scientific firewall

Protected solar longitude `[20°,55°]` remains inaccessible. OrbitTrace target information/events, MAARSY and DMS remain scientifically inaccessible. The direct method-selection benchmark used only the already-exposed SonotaCo benchmark outside the protected interval. The cross-hierarchy DAG structural and detector experiments used only authorized target-excluded GMN development data and did not open protected target information or external scientific data.