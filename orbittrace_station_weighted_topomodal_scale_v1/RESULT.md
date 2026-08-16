# OrbitTrace station-support-weighted topomodal scale v1 — binding result

## 🟢 POSITIVE — STRUCTURAL PASS

Binding run: `31973153123`

Job: `95228601254`

Execution head: `b4654bedf63fae04f220735bfd321f14f7dafea9`

Artifact: `9270373477`

Artifact ZIP SHA-256: `799c0e4301e0adb74fb08b4848cf9d9bbf510995ca340a6889530e8ff35a9de9`

Result SHA-256: `a7cc8921a9431028f08c92479a001021160ee0e8cce6ed346a80d0d2510a8bb8`

Immutable `event_id -> Num(stat)` mapping SHA-256: `92f6ce1961b0e8642f6bdd1cc455b07785ed8224c8f8f3d467d69fac2b82921c`

Exact interpretation:

`SUPPORTS_STATION_WEIGHTED_TOPOMODAL_CROSS_SCALE_COHERENCE`

No shower truth was opened.

## Frozen method

The exact #1284 physical embedding, radius-1 graph, complete GUDHI ToMATo hierarchy, support floor 4, deterministic thinning panels, recurrent-EOM comparator, and cross-scale gates were unchanged.

The sole scientific substitution was the preregistered density field:

`rho_station(i) = sum_{j in N1(i)} Num(stat)_j / sum_{k in subset} Num(stat)_k`.

All `Num(stat)` values were the exact immutable integers from the binding availability artifact; no transform, cap, rank, threshold, imputation, blend, station identity, or station geography entered the method.

## Candidate counts

| subset | station-weighted ToMATo | recurrent-EOM |
|---|---:|---:|
| d=128 b=0 | 88 | 29 |
| d=128 b=1 | 95 | 35 |
| d=128 b=2 | 93 | 38 |
| d=128 b=3 | 82 | 33 |
| d=1024 b=0 | 9 | 8 |
| d=1024 b=1 | 5 | 5 |
| d=1024 b=2 | 6 | 6 |
| d=1024 b=3 | 9 | 9 |

Fine candidate noncollapse passed in all four buckets.

Mean `Num(stat)` per event was reporting-only and ranged from about 3.29 to 3.57 across the eight frozen panels. It did not select any method parameter.

## Cross-scale membership stability

Fine→coarse mean-best-Jaccard by bucket:

| bucket | station-weighted ToMATo | recurrent-EOM |
|---|---:|---:|
| 0 | **0.8112643577983317** | 0.5606150793650794 |
| 1 | **0.8822900136798906** | 0.7051527695218045 |
| 2 | **0.8534391534391536** | 0.5504804710843509 |
| 3 | **0.8350308641975308** | 0.6571853102095039 |

Aggregate:

- pooled station-weighted Jaccard: **`0.8396117926550738`**;
- pooled recurrent-EOM: `0.6152941107471891`;
- median station-weighted bucket score: **`0.8442350088183421`**;
- median recurrent-EOM: `0.6089001947872916`;
- strict bucket wins: **4/4**.

For context, original #1284 geometry-only ToMATo achieved pooled `0.8067062037`, median `0.8129624258`, and 4/4 wins. Thus station-support weighting improves the already-strong structural stability without changing the physical graph.

## Frozen gate outcome

All five preregistered gates passed:

1. nonempty in all eight subsets;
2. fine candidate noncollapse in all four;
3. pooled mean Jaccard strictly above recurrent-EOM;
4. median bucket Jaccard strictly above recurrent-EOM;
5. strict wins in at least 3/4 buckets — observed 4/4.

## Consequence

The separately preregistered `orbittrace_station_weighted_topomodal_recovery_v1` truth-bearing GMN test is **activated exactly as written**. Its ranking semantics and ten truth gates were frozen before the station-count availability and structural outcomes.

This is not yet evidence that station weighting improves known-shower recovery or MRR. It is also not yet evidence of cross-survey portability because equivalent `Num(stat)` metadata may not exist in other surveys.

Protected `[20.0,55.0]` remained excluded inclusively. OrbitTrace target information/events, shower truth, SonotaCo, ASFN/EFN event rows, AMOS, MAARSY, and DMS were not accessed.