# OrbitTrace topomodal canonical death-support v1 — binding result

## 🔴 NEGATIVE — EXACT ARCHITECTURE CLOSED

Authoritative run: `31961426802`

Artifact: `9267396363`

Artifact ZIP SHA-256: `c1636624d51df99280f454c5a06fb9e7454f13ed0f28d933568be3755063362b`

Immutable prelabel SHA-256: `6426110692f96c6b885042d9c95c8a9b24f4235ba58da1f5c7b730e4c30b537a`

Exact verdict:

`FAIL_TOPOMODAL_DEATH_SUPPORT_V1`

The workflow completed the frozen scientific contract successfully. Before shower truth opened, it reproduced the complete authoritative #1284 hierarchy, reconstructed GUDHI's finite persistence diagram from the frozen active-mode death lineage within the required `1e-12` tolerance, excluded infinite/root features exactly as preregistered, wrote the immutable prelabel, and verified its hash. The failure is therefore scientific candidate semantics rather than engineering.

## Candidate collapse under thinning

The canonical finite-feature rule removed almost all reportable candidates at the fine sparse scale:

| subset | death-support candidates | recurrent-EOM candidates | equal budget K |
|---|---:|---:|---:|
| d=128, b=0 | 7 | 29 | 7 |
| d=128, b=1 | 11 | 35 | 11 |
| d=128, b=2 | 11 | 38 | 11 |
| d=128, b=3 | 10 | 33 | 10 |
| d=1024, b=0 | 0 | 8 | 0 |
| d=1024, b=1 | 1 | 5 | 1 |
| d=1024, b=2 | 0 | 6 | 0 |
| d=1024, b=3 | 0 | 9 | 0 |

Thus `all_subsets_have_positive_equal_budget=false`. The fine-scale promotion gates are binding failures because three of four fine subsets have no successor candidate at all.

## Coarse equal-budget truth result

At the four ~5.8k-event subsets, both methods were truncated to the same `K=7–11` candidates per subset.

| aggregate | recurrent-EOM | canonical death-support |
|---|---:|---:|
| qualified matches | **51** | 13 |
| recovered@25 total | **51** | 13 |
| recovered@50 total | **51** | 13 |
| recovered@100 total | **51** | 13 |
| recovered@500 total | **51** | 13 |
| mean top-100 dominant precision | **0.55905085566** | 0.48203823895 |
| mean MRR | **0.38889721871** | 0.38043154762 |
| mean median-fragmentation | 1.0 | **0.875** |

Panelwise qualified-match comparison: `0/8` nonlower, `0/8` strict wins, `8/8` losses.

Only fragmentation improved; recovery, purity, and MRR all lost.

## Scientific interpretation

The earlier all-node #1284 successors established that the fixed-scale ToMATo hierarchy contains substantially more recoverable known streams than recurrent-EOM under thinning. This experiment shows that those useful stream-bearing objects are **not adequately represented by finite dying-mode supports alone**. In fine samples, most finite persistence features die while their pre-death support is below the already-frozen support-4 reporting floor, even though useful stream-scale merged ancestors remain present elsewhere in the hierarchy. At the coarser scale, retaining only finite death supports also discards too much stream coverage.

Therefore the exact architecture `fixed-scale ToMATo + one finite dying-child support per persistence feature + roots excluded + persistence ranking` is permanently closed.

Do **not** rescue it by adding roots, lowering support below 4, changing the active-mode survival rule, choosing an ancestor instead of the dying child, changing the persistence convention, adding a second score, altering equal-budget semantics, or relaxing gates after truth.

The broader fixed-scale #1284 hierarchy remains scientifically promising, but the next successor must solve **hierarchical selection** directly: retain reportable merged/surviving nodes when finer splits are not support-resolved, while avoiding the redundant all-node list that hurt early ranking.

Protected solar longitude `[20°,55°]` remained excluded. OrbitTrace target information/events, SonotaCo, ASFN/EFN event rows, AMOS, MAARSY, and DMS were not accessed.