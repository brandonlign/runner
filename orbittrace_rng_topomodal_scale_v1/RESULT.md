# OrbitTrace RNG-pruned topomodal scale v1 — binding result

## 🔴 NEGATIVE — EXACT ARCHITECTURE CLOSED BEFORE SHOWER TRUTH

Binding run: `31971594585`

Job: `95224786807`

Execution head: `3040f2536cfae3180f52147224437459f849c77e`

Artifact: `9269975285`

Artifact ZIP SHA-256: `e60fcbe140e01baae301f7b4582e21cb729cf16581a9203a0d571ba6fe28f44a`

Exact interpretation from the successfully completed zero-label scientific step:

`REFUTES_RNG_TOPOMODAL_CROSS_SCALE_COHERENCE`

The subsequent workflow contract step failed only while formatting a reporting-only summary because it referenced `f['n']` instead of the existing `f['events_total']`. The scientific diagnostic JSON had already been written successfully and is authoritative. No rerun is scientifically necessary or authorized from this bookkeeping error.

## Mechanism activity

The exact relative-neighborhood rule was highly active. Original #1284 radius-1 edges were pruned to:

| subset | original radius edges | RNG edges | retained |
|---|---:|---:|---:|
| d=128 b=0 | 64,247 | 2,385 | 0.0371 |
| d=128 b=1 | 77,863 | 2,523 | 0.0324 |
| d=128 b=2 | 74,985 | 2,506 | 0.0334 |
| d=128 b=3 | 68,335 | 2,419 | 0.0354 |
| d=1024 b=0 | 777 | 150 | 0.1931 |
| d=1024 b=1 | 1,102 | 154 | 0.1397 |
| d=1024 b=2 | 1,415 | 166 | 0.1173 |
| d=1024 b=3 | 1,164 | 170 | 0.1460 |

Thus this is not a null/ineffective graph transformation.

## Candidate counts

| subset | RNG-ToMATo | recurrent-EOM |
|---|---:|---:|
| d=128 b=0 | 311 | 29 |
| d=128 b=1 | 333 | 35 |
| d=128 b=2 | 326 | 38 |
| d=128 b=3 | 323 | 33 |
| d=1024 b=0 | 26 | 8 |
| d=1024 b=1 | 32 | 5 |
| d=1024 b=2 | 26 | 6 |
| d=1024 b=3 | 37 | 9 |

The method was nonempty in all eight subsets and passed the frozen fine-candidate noncollapse gate in all four buckets.

## Cross-scale membership stability

Fine→coarse mean-best-Jaccard by bucket:

| bucket | RNG-ToMATo | recurrent-EOM | strict winner |
|---|---:|---:|---|
| 0 | **0.7101397018563639** | 0.5606150793650794 | RNG-ToMATo |
| 1 | 0.5769419142028621 | **0.7051527695218045** | recurrent-EOM |
| 2 | **0.6102693193504618** | 0.5504804710843509 | RNG-ToMATo |
| 3 | 0.6020648616521104 | **0.6571853102095039** | recurrent-EOM |

Aggregate:

- pooled RNG-ToMATo fine→coarse mean best Jaccard: **`0.62040641063634`**;
- pooled recurrent-EOM: `0.6152941107471891`;
- median RNG-ToMATo bucket score: `0.6061670905012861`;
- median recurrent-EOM: **`0.6089001947872916`**;
- strict RNG-ToMATo bucket wins: **`2/4`**.

## Frozen gates

PASS:

- RNG-ToMATo nonempty in all eight subsets;
- fine candidate noncollapse in all four buckets;
- pooled fine→coarse mean Jaccard strictly greater than recurrent-EOM.

FAIL:

- median bucket fine→coarse mean Jaccard strictly greater than recurrent-EOM;
- strict bucket-level wins at least `3/4` — observed only `2/4`.

Every gate was mandatory. Therefore the exact architecture is negative and closed.

## Scientific interpretation

Removing locally redundant radius edges changes #1284's modal topology drastically but does **not** improve sample-size generalization consistently. The gain is bucket-dependent: two deterministic thinning views improve and two regress, and the median bucket is slightly worse than recurrent-EOM.

The strong original #1284 result (`0.8067062037` pooled, `0.8129624258` median, 4/4 wins) therefore does not appear to be limited by redundant short-range graph bridges in a way that relative-neighborhood pruning fixes. The exact RNG-pruned connectivity lane is closed.

The preregistered conditional truth protocol in `orbittrace_rng_topomodal_recovery_v1/PROTOCOL.md` is **blocked** because the zero-label structural prerequisite failed. No known-shower truth is opened for this architecture and SonotaCo is not activated.

No rescue via Gabriel/Delaunay/kNN variants, RNG inequality changes, graph radius/physical-scale changes, density changes, support changes, persistence cuts, subset/salt changes, or gate relaxation is authorized from this outcome.

Protected solar longitude `[20.0,55.0]` remained excluded inclusively. OrbitTrace target information/events, shower truth, SonotaCo 2013/2014, ASFN/EFN event rows, AMOS, MAARSY, and DMS were not accessed.