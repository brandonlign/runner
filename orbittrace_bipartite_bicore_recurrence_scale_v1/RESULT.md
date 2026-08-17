# Bipartite bicore recurrence scale v1 — binding Stage-1 result

## Verdict

🔴 **`FAIL_BIPARTITE_BICORE_RECURRENCE_SCALE_V1_PRETRUTH` — CLOSED BEFORE TRUTH.**

The first technically valid zero-label Stage-1 execution failed the frozen capacity authorization gate. No GMN shower truth was opened, and no Stage-2 ranking/evaluation is authorized. Per the frozen protocol, this exact radius-1 symmetric `(4,4)` raw-event bicore architecture is permanently closed; no alternate core order, radius, asymmetric core, soft degree, edge weighting, butterfly/bitruss threshold, same-year edge, halo, component split, or capacity rescue is authorized from this result.

## Binding provenance

- current full-GMN development parent: density-synchronous recurrent-EOM HDBSCAN v1, PR #1263;
- parent execution head: `182f07ade6bb5d4be2c80b88df9216bb2d6eee2d`;
- frozen protocol commit: `e63622924ee24934ecad867b2c1f2105fb15293e`;
- frozen protocol blob: `8d0040e66bc0c640a9427c7b36824e05acb8e3ef`;
- frozen implementation commit: `384ab1726bcb34c5ca9facac310176e36d2a8ea3`;
- frozen implementation blob: `2ee3c3c9e592f84d15f910ce2ae35c2a5a79f977`;
- scientific execution head: `92eebb51d1e42a0876ed0dba26ed06c7c0243b16`;
- binding workflow run: `32081492913`;
- binding job: `95545222575`;
- binding artifact: `9305317452`;
- artifact digest: `sha256:ec1a60b6292b530ad70b0b6dc25b72aac263b6087ce0aee2ef0106fad7920438`;
- binding pretruth JSON SHA-256: `848782549d2bfd94a0e085aefb0862ecf92bf9c3bb1467a95adb7c7633aff555`;
- immutable zero-label endpoint source JSON SHA-256: `95f8a57718a30b2c7e85016d505276d72cccb9e4ac1d6eb29f13067efc73dd0c`.

The scientific workflow completed successfully end to end. All protocol/source hashes and the protected-data firewall passed before graph construction. The hidden GMN shower-label mapping was explicitly destroyed before any bicore graph, peeling, component, or cross-scale computation.

## Frozen mechanism

For each target-excluded sparse GMN 2022/2023 panel:

1. use exact inherited GEO6 physical geometry;
2. construct only cross-year edges at fixed Euclidean radius `1.0`;
3. discard all self and same-year edges;
4. iteratively peel every event with fewer than four active opposite-year neighbors;
5. emit connected components of the surviving strictly bipartite `(4,4)` core.

The value `4` was inherited prospectively from the long-frozen minimum stream-support constant. No alternate radius/core order was evaluated.

## Candidate-capacity result

The bicore collapsed to exactly **one connected component in every one of the eight sparse panels**:

| scale | bucket | frozen reference K | bicore families |
|---|---:|---:|---:|
| d=128 | 0 | 29 | **1** |
| d=128 | 1 | 35 | **1** |
| d=128 | 2 | 38 | **1** |
| d=128 | 3 | 33 | **1** |
| d=1024 | 0 | 8 | **1** |
| d=1024 | 1 | 5 | **1** |
| d=1024 | 2 | 6 | **1** |
| d=1024 | 3 | 9 | **1** |

Therefore `capacity_at_least_reference_k_all_8` fails decisively in all eight panels.

## Cross-scale structure

Despite the capacity collapse, the single surviving bicore component is extremely stable under the established nested ~8x thinning comparison:

| bucket | bicore mean-best Jaccard | recurrent reference |
|---|---:|---:|
| 0 | **0.9778434269** | 0.5606150794 |
| 1 | **0.9851150203** | 0.7051527695 |
| 2 | **0.9836289222** | 0.5504804711 |
| 3 | **0.9778067885** | 0.6571853102 |

Aggregate cross-scale mean:

- bicore: **0.9810985395**;
- recurrent reference: `0.6183584075`;
- bucket wins/ties: **4/4**.

Thus the failure is not instability. It is severe under-segmentation/percolation.

## Frozen gates

PASS — **11/12**:

- `immutable_endpoint_source`;
- `strict_bipartite_graph_all`;
- `bicore_degree_floor_all`;
- `annual_support_floor_all`;
- `pairwise_disjoint_all`;
- `crossyear_connected_all`;
- `peeling_order_invariance_all`;
- `year_swap_invariance_all`;
- `cross_scale_nonlower_4_of_4`;
- `cross_scale_mean_not_lower`;
- `firewall`.

FAIL:

- **`capacity_at_least_reference_k_all_8`**.

All twelve gates were mandatory.

## Scientific interpretation

This zero-label result independently reproduces, with a different topology, the broad-background collapse seen in annual sync-density persistence flattening.

The raw cross-year GEO6 recurrence graph contains an exceptionally stable many-to-many recurrent structure, but a hard symmetric local recurrence condition does **not** separate it into a catalogue-sized collection of streams. Instead, the `(4,4)` core percolates into one giant recurrent component in every panel. The almost-perfect fine→coarse Jaccard values show that this giant structure is not a sampling accident: it is a persistent background-scale object under severe thinning.

Therefore the remaining problem is more specific than "rank the candidates better" or "replace one-to-one matching with many-to-many recurrence." A useful successor must provide a principled **partition/decomposition inside a giant recurrent bipartite background** while preserving recurrence, rather than defining families as connected components after one hard adjacency/core criterion.

That conclusion does **not** authorize tuning this bicore. The frozen v1 closure forbids changing `(4,4)`, radius `1.0`, asymmetric core orders, butterfly/bitruss thresholds, same-year edges, component splitting, or other result-informed rescues.

## Firewall

Throughout the binding run:

- `shower_truth_used = false`;
- protected inclusive solar longitude `[20.0,55.0]` remained excluded;
- `target_information_access = false`;
- `target_region_events_accessed = false`;
- SonotaCo 2013/2014 was not accessed;
- ASFN/EFN event-level data was not accessed;
- AMOS, MAARSY, and DMS scientific data were not accessed;
- orbital information was not accessed;
- station metadata was not accessed;
- uncertainty metadata was not accessed;
- `post_result_parameter_search = false`.
