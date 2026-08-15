# #1263 density-synchronous recurrent-EOM — direct SonotaCo benchmark result

## 🟡 NEUTRAL — density-sync does not earn selection over recurrent-EOM

Binding workflow run: `31889652785`  
Execution head: `f0d721ddd7d3a3a304e4274218372195e25796c1`  
Artifact: `9248203777`  
Artifact digest: `sha256:a9e3b7895b43465181d94376b873c04ddc70d815d325930a0a49332a144a23d0`  
Frozen pretruth SHA-256: `051ea9a213c7a72b93875e8ddd6716aa884e802377c293b7b6cf4a6de5ca5609`  
Binding result SHA-256: `00b9defa3a07fc1396b8d9dcbc3bd62da44dc95e7245ad44d7bdedf375570f5c`

Exact verdict:

`NEUTRAL_DENSITY_SYNC_SONOTACO_DIRECT_BENCHMARK_V1`

SonotaCo 2013/2014 is **EXPOSED DEVELOPMENT / VALIDATION BENCHMARK ONLY**, not pristine external validation.

## Exact head-to-head

| Panel | Budget | recurrent-EOM macro-F1 / recovered | #1263 density-sync macro-F1 / recovered | Delta |
|---|---:|---:|---:|---:|
| Sugar 2013 | 34 | `0.3752906816276458 / 23` | `0.3752906816276458 / 23` | `0 / 0` |
| Sugar 2014 | 46 | `0.43773122295664196 / 24` | `0.43773122295664196 / 24` | `0 / 0` |
| HDBSCAN 2013 | 11 | `0.1914598192215768 / 11` | `0.1914598192215768 / 11` | `0 / 0` |
| HDBSCAN 2014 | 9 | `0.1685878550176112 / 9` | `0.1685878550176112 / 9` | `0 / 0` |

#1263 preserves the recurrent-EOM result exactly on all four panels.

It also preserves **4/4 v31 superiority** and **4/4 literature-comparator superiority** under the established matched budgets.

## Why the metrics tie despite an active density-sync mechanism

The complete candidate order changes on both routes, so the density-synchronous score is not mathematically inactive. However:

- Sugar route: recurrent-EOM and #1263 select the exact same 144 nodes; the first order difference is rank 42.
  - top 34 sequence is identical;
  - top 46 candidate **set** is identical (only order inside the set changes);
  - top 100 candidate set is identical.
- HDBSCAN route: recurrent-EOM and #1263 select the exact same 123 nodes; the first order difference is rank 42.
  - top 9 sequence is identical;
  - top 11 sequence is identical;
  - top 50 candidate set is identical.

The established Hungarian panel evaluator is set-based after truncation to the panel budget. Therefore the density-sync changes occur too far down the order, or only reorder candidates inside an unchanged budget set, to affect any of the four established validation panels.

## Method-selection decision

**Retain recurrent-EOM HDBSCAN v1 as the preferred OrbitTrace paper/development method.**

Reasoning:

1. recurrent-EOM already passed target-excluded GMN development;
2. recurrent-EOM beat v31 on all four SonotaCo panels and beat the matched literature comparators on all four panels;
3. #1263 produced a small full-GMN gain, but its strict @100 recovery superiority was not robust in the frozen 10-fold deletion diagnostic (`1761 -> 1761` aggregate);
4. the direct SonotaCo comparison shows zero performance gain over recurrent-EOM on all four validation panels;
5. recurrent-EOM is therefore the simpler method with the same demonstrated SonotaCo performance and a more defensible parsimony argument.

This does **not** make #1263 a scientific failure. It remains a valid density-level refinement with an active mechanism and a positive full-GMN development result. The conclusion is narrower: the available validation evidence does not justify choosing its added density-synchronous criterion over recurrent-EOM.

No new successor is authorized by this result. The next research work should use recurrent-EOM as the fixed method and focus on paper-quality characterization/comparison rather than another method-search loop.

## Firewall

- protected `[20°,55°]` remained excluded;
- `target_information_access=false`;
- `target_region_events_accessed=false`;
- `amos_access=false`;
- `maarsy_scientific_access=false`;
- `dms_scientific_access=false`;
- `post_result_parameter_search=false`.
