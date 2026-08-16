# OrbitTrace window-owned persistence ranking v1 — evaluator-repair result

## 🔴 NEGATIVE — CLOSED

Authoritative evaluator-only repair run: `31959226439`

Result artifact: `9266812693`

Source immutable prelabel run/artifact: `31956064964` / `9266239856`

Immutable prelabel SHA-256: `beae39cc987100373d236a19e656415dd63f183cfbbb4202345e0cde7e3b6f11`

Frozen successor candidates: `1028` total, `1014` present in both years.

Exact binding verdict:

`FAIL_WINDOW_OWNED_PERSISTENCE_RANKING_V1_GMN_DEVELOPMENT`

The repaired evaluator ran under NumPy `2.1.3` with Persistable absent, consumed the immutable candidate list in stored rank order, did not regenerate candidates, and used the immutable historical recurrent-EOM parent controls. The workflow and all scientific-contract checks completed successfully.

### 2022

| metric | recurrent-EOM parent | window-owned persistence |
|---|---:|---:|
| recovered@25 | 22 | 0 |
| recovered@50 | 45 | 1 |
| recovered@100 | 89 | 3 |
| recovered@500 | 193 | 50 |
| top-100 dominant precision | 0.7856486013 | 0.15274507536764081 |
| MRR | 0.0224982696 | 0.00313146630098278 |
| qualified matches | 236 | 102 |
| fragmentation median top500 | 1.0 | 2.0 |

### 2023

| metric | recurrent-EOM parent | window-owned persistence |
|---|---:|---:|
| recovered@25 | 23 | 1 |
| recovered@50 | 46 | 2 |
| recovered@100 | 89 | 4 |
| recovered@500 | 192 | 45 |
| top-100 dominant precision | 0.7867680237 | 0.14882483193183474 |
| MRR | 0.0220239289 | 0.008209251465795356 |
| qualified matches | 244 | 97 |
| fragmentation median top500 | 1.0 | 2.0 |

Every frozen annual gate failed in both years and there was no strict recovered@100 improvement.

## Scientific interpretation

The earlier zero-label cross-scale stability result was real, but stable window-owned local persistence branches are not adequate stream-level recovery candidates. The deficit is not merely a ranking problem: even by rank 500 recovery is only `50/193` in 2022 and `45/192` in 2023, qualified-match coverage is much lower, and fragmentation worsens from `1` to `2`.

This exact architecture is permanently closed. Do **not** rerank, retune, merge, split, alter memberships, change persistence settings, or otherwise rescue it after truth. The pre-frozen conditional SonotaCo transfer benchmark is not authorized because the GMN prerequisite failed.

Protected solar longitude `[20°,55°]` remained excluded. OrbitTrace target information/events, SonotaCo, ASFN/EFN event rows, AMOS, MAARSY, and DMS were not accessed by the repair.