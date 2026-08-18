# OrbitTrace current method roles — post-development governance freeze

## Purpose

This file resolves the accumulated use of the words **paper method**, **flagship**, **sparse detector**, and **final AMOS method** without rewriting any historical PASS/FAIL result.

It is evidence/governance only. No scientific method is created or changed here and no external endpoint is executed.

## 1. Preferred full-catalogue / paper method: recurrent-EOM HDBSCAN v1

**Role:** primary methodology for the paper and full-catalogue recurrence-aware detection/ranking.

Exact selected kernel Git blob:

`30ac3fa3bc47910370df528fcf3ae8ecb6277b47`

This remains the preferred paper method under PR #1269 / `ORBITTRACE_PAPER_METHOD_SELECTION.md` because:

- it passed its frozen target-excluded GMN 2022/2023 development gate;
- it beat v31 and the corresponding frozen literature comparators on all four exposed SonotaCo 2013/2014 panels;
- it later passed the matched-capacity target-excluded GMN literature audit 4/4;
- density-synchronous recurrent-EOM (#1263) tied it exactly on all four direct SonotaCo validation panels;
- the strict density-sync full-GMN @100 gain was sample-sensitive in the frozen deletion diagnostic;
- the simpler recurrent-EOM objective therefore wins by parsimony.

This selection is not changed by later sparse-survey TopoModal work, because those methods were developed for a distinct finite-sample failure mode and have not demonstrated clean full-scale portability.

## 2. Frozen primary AMOS endpoint: density-synchronous recurrent-EOM v1

**Role:** historically frozen **primary** AMOS 2023/2024 one-shot endpoint under PRs #1267/#1268.

This role is retained to preserve the explicit no-method-switch governance frozen before AMOS access. It is **not** a statement that density-sync is the preferred paper method.

The still-unexecuted PR #1268 AMOS pipeline already freezes three complete full-catalogue outputs before labels:

1. ordinary HDBSCAN EOM;
2. recurrent-EOM;
3. density-synchronous recurrent-EOM.

Therefore preserving density-sync as the primary AMOS endpoint does not prevent the same single AMOS receipt from providing a separately predeclared external characterization of recurrent-EOM. No second external chance is needed or authorized.

### Retrospective literature characterization

After the method was already immutable, density-sync was evaluated against the sealed matched-capacity GMN literature comparators in run `32193713209`.

Verdict:

`PASS_DENSITY_SYNC_GMN_MATCHED_CAPACITY_LITERATURE_4_OF_4`

Binding result SHA-256:

`b4f4aea785ea309f66dda31f60f54f0a798b88f036493c456e9b89d4b7bf6619`

At matched complete catalogue capacity it beat the tested published-configuration HDBSCAN and deterministic Sugar-core comparators in macro-F1 without recovered-shower loss in both 2022 and 2023. This strengthens literature characterization but does not alter the paper-method selection or establish cross-survey generalization.

## 3. Sparse-survey flagship: fixed-scale native TopoModal

**Role:** flagship method for sparse-sample detection/recovery and sample-size robustness.

The fixed physical architecture from PRs #1284/#1285 remains the strongest cleanly promoted sparse-survey result:

- physical scale fixed at 5° solar halfwidth / 4° radiant / 10% speed;
- exact radius-1 graph and radius-count density;
- complete ToMATo mode-merging hierarchy;
- no shower truth used to construct the hierarchy;
- 4/4 cross-scale structural wins versus recurrent-EOM on frozen ~5.8k → ~0.7k GMN stress;
- sparse recovery increased from 20 → 31 at ~0.7k scale and 94 → 140 at ~5.8k scale, with large dominant-precision gains and no qualified-recovery loss across the frozen bucket-year panels.

The claim boundary remains **sparse detection/recovery, purity, fragmentation, and sample-size generalization**. It is not a demonstrated full-GMN replacement for recurrent-EOM.

## 4. Positive sparse auxiliary method: recurrent–TopoModal Pareto-prominence v1

The frozen recurrent–TopoModal Pareto-prominence method is a genuine positive sparse result. Binding run `32077260440` passed all frozen gates on d=128/d=1024 sparse GMN panels and materially improved recurrent-EOM at equal budget.

However, its exact d=64 translation failed structurally before truth because a support-resolved TopoModal child overlapped multiple recurrent parents. The binding result explicitly states that the architecture does **not** demonstrate straightforward scale portability to d=64.

Therefore Pareto-prominence is preserved as positive sparse evidence, not promoted to the general/full-catalogue paper-method role.

## 5. Dense-scale TopoModal portability attempts are closed, not hidden

The following later attempts did **not** supersede the roles above:

### Pareto scale-64 direct translation

`STRUCTURAL FAIL BEFORE TRUTH`

Unique-parent correspondence failed at d=64. No truth was opened.

### Overlap-barycenter Pareto v1

`FAIL_PARETO_OVERLAP_BARYCENTER_V1`

Passed 4/5 truth gates. Recovery and precision improved strongly, but zero-filled MRR regressed.

### Parent-set unanimous v1

Binding FAIL, 4/5 gates. It again improved total recovery and precision but regressed zero-filled MRR / earliest-slot retrieval.

### Recurrent-Pareto inactivity router v1

`STRUCTURAL_PRETRUTH_FAIL_RECURRENT_PARETO_INACTIVITY_ROUTER_V1`

The intended inactive d=64 route still encountered multi-parent TopoModal correspondence before truth.

### Cross-hierarchy DAG follow-ups

The refinement DAG itself had useful zero-label structural evidence, but detector/ranking follow-ups failed:

- `FAIL_DAG_CORROBORATION_MASS_RANK_V1` — native TopoModal ordering was materially better than the all-edge corroboration-mass rerank;
- `FAIL_DAG_ATOM_PARETO_PROMINENCE_V1` — the direct DAG-atom detector regressed sparse recovery/MRR against the already-positive Pareto comparator.

These failures reinforce, rather than overturn, the separation between the full-catalogue recurrent-EOM role and the sparse TopoModal role.

## 6. Recurrent local TopoModal trunk v1 is closed

Binding run `32191925070` returned:

`FAIL_RECURRENT_LOCAL_TOPOMODAL_TRUNK_V1`

It passed 15/16 frozen gates and improved many recovery metrics, but 2023 top-100 dominant precision regressed from `0.7898245986099988` to `0.7898042123909221`. The exact no-regression gate failed and is not relaxed.

No local-trunk literature or AMOS endpoint is activated from that failed method.

## 7. Historical targeted OrbitTrace recovery: fixed-4° detector

The canonical OrbitTrace/GhostStream target was already opened under the separately frozen fixed-4° targeted application in PR #153. This occurred only after the detector, application code, calibration streams, and interpretation gates were frozen.

Binding run `30927310565` returned:

`FULL_FROZEN_GHOSTSTREAM_RECOVERY`

Evidence artifact `8899766878`, digest `sha256:0288bd50c88c1dee8bf5b72bd52937116d81026f074667450c99cb8d8c56653c`.

All 14 frozen gates passed. Pooled candidate recall was `0.70/0.30` at k=4, `1.00/0.70` at k=6, `1.00/0.95` at k=8, and `1.00/1.00` at k=12 for alpha 0.05/0.01, with controlled negative-window FPR `0.0515625/0.00703125`.

**Role:** targeted independent recovery evidence for that fixed-4° detector. It is not the historical discovery method, not a blind catalogue rediscovery, and not evidence used to tune or select recurrent-EOM.

## 8. Current claim map

### Supported now

- recurrent-EOM is the preferred full-catalogue/paper method;
- recurrent-EOM has positive frozen GMN development evidence, 4/4 exposed SonotaCo superiority, and 4/4 matched-capacity GMN literature superiority versus the tested comparator implementations;
- fixed-scale TopoModal has strong sparse-sample recovery/purity and cross-scale robustness evidence;
- the separately frozen fixed-4° detector achieved full targeted recovery of the canonical OrbitTrace structure under its preregistered application;
- density-sync, while not the preferred paper method, has a 4/4 matched-capacity GMN literature-superiority characterization;
- the project preserves multiple negative portability results rather than result-informed rescues.

### Not yet supported

- pristine cross-survey external generalization of recurrent-EOM;
- pristine cross-survey external generalization of fixed-scale TopoModal;
- universal superiority to every meteor-stream algorithm;
- full-scale portability of sparse TopoModal/Pareto methods;
- a claim that the fixed-4° detector originally discovered OrbitTrace.

## 9. Next scientific action

Do **not** launch another method-search lane.

The secondary recurrent-EOM AMOS characterization gate is now frozen in PR #1351 and source/synthetic-audited. The only unresolved scientific step for the main generalization claim is to obtain the exact frozen AMOS 2023/2024 staged data transfer and execute the already-frozen one-shot #1268 endpoint plus the #1351 recurrent-EOM adjudication.

A recurrent-EOM PASS would support pristine cross-survey generalization of the paper method; a valid FAIL remains binding and must not trigger another survey or method switch.

## Firewall

No AMOS event row or shower label has been opened. No provider request has been sent. The canonical target interval `[20°,55°]` is **not globally unopened**: it was accessed only in the frozen PR #153 targeted fixed-4° application. Recurrent-EOM development/selection, literature audits, and AMOS work remain target-excluded and may not use target events or target results to change the method or gates. MAARSY and DMS remain scientifically inaccessible. No result-informed parameter search or replacement external survey is authorized by this role freeze.