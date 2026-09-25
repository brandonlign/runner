# OrbitTrace topomodal support-resolved cut v1 — binding result

## 🔴 NEGATIVE — EXACT ARCHITECTURE CLOSED

**Record correction only. No method, gate, candidate, ranking, or scientific outcome is changed by this commit.** The earlier RESULT.md captured interim numbers instead of the completed authoritative workflow aggregates. The values below are the binding run output.

Authoritative run: `31961908008`

Artifact: `9267530845`

Artifact ZIP SHA-256: `92fc029751562bbff844fd5ef866448a5bf1972ce035e5f74851861a4948c9c8`

Immutable prelabel SHA-256: `4529eadd9ff93aae057f0a6fd5e0dd923f2300b7c6e01b74a0b7638e22da6de6`

Exact verdict: `FAIL_TOPOMODAL_SUPPORT_RESOLVED_CUT_V1`

The workflow completed the frozen contract. The complete #1284 hierarchy and recurrent-EOM comparator memberships were reproduced before truth, the selected cut was pairwise disjoint and partitioned reportable roots, the active-mode persistence reconstruction passed, and the immutable prelabel was sealed before shower truth opened. This is a scientific failure, not an engineering no-result.

## Candidate counts before truth

| subset | support-resolved cut | recurrent-EOM | equal budget K |
|---|---:|---:|---:|
| d=128, b=0 | 69 | 29 | 29 |
| d=128, b=1 | 80 | 35 | 35 |
| d=128, b=2 | 79 | 38 | 38 |
| d=128, b=3 | 70 | 33 | 33 |
| d=1024, b=0 | 9 | 8 | 8 |
| d=1024, b=1 | 6 | 5 | 5 |
| d=1024, b=2 | 6 | 6 | 6 |
| d=1024, b=3 | 9 | 9 | 9 |

Candidate existence did not collapse under thinning. At every panel the successor had enough candidates for the exact recurrent-EOM budget.

## Fine sparse scale (`d=1024`, ~700 events)

| aggregate | recurrent-EOM | support-resolved cut |
|---|---:|---:|
| qualified matches | 20 | **31** |
| recovered@25/@50/@100/@500 total | 20 | **31** |
| mean top-100 dominant precision | 0.3530315709574533 | **0.5971047679172679** |
| mean MRR | **0.6959325396825397** | 0.5404513888888889 |
| mean median-fragmentation | 1.0 | 1.0 |

Panelwise qualified nonloss: **8/8**; strict wins: **6/8**.

## Coarse sparse scale (`d=128`, ~5.8k events)

| aggregate | recurrent-EOM | support-resolved cut |
|---|---:|---:|
| qualified matches | 94 | **142** |
| recovered@25 total | 87 | **132** |
| recovered@50/@100/@500 total | 94 | **142** |
| mean top-100 dominant precision | 0.3396191653933494 | **0.5648829520963607** |
| mean MRR | **0.23584530975502274** | 0.18405119390717406 |
| mean median-fragmentation | 1.0 | 1.0 |

Panelwise qualified nonloss: **8/8**; strict wins: **8/8**.

## Frozen gates

Every recovery, panelwise nonloss, precision, and fragmentation gate passed at both scales. The **only failed gates were fine MRR and coarse MRR**.

## Scientific interpretation

The support-resolved disjoint cut does **not** sacrifice the strong sparse recovery discovered in the #1284 topomodal hierarchy. It materially beats recurrent-EOM on qualified recovery and purity at both ~700-event and ~5.8k-event scales while keeping median fragmentation at 1.0.

Its failure is narrower and more informative: the native modal-contrast order places the recovered streams too late. Therefore the remaining obstacle is **candidate prioritization**, not candidate existence, purity, fragmentation, or sample-size recovery. The exact cut/ranking architecture remains closed because the preregistered MRR gates failed; the result does not authorize retuning the ranking score.

Do not alter support 4, change the cut recursion, add lookahead, change root handling, tune modal contrast, add a result-informed score blend, change equal-budget semantics, or relax gates after truth.

Protected solar longitude `[20°,55°]` remained excluded. OrbitTrace target information/events, SonotaCo, ASFN/EFN event rows, AMOS, MAARSY, and DMS were not accessed.