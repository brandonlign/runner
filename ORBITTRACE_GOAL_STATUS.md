# OrbitTrace goal status — final paper-facing state

## Final project claim

The final OrbitTrace claim is deliberately bounded:

> A frozen recurrence-aware HDBSCAN extraction method outperforms the tested relevant unsupervised comparator implementations under fair fixed-capacity evaluation on GMN and an exposed SonotaCo benchmark, while a separate fixed-scale TopoModal method improves sparse-sample robustness and a separately frozen fixed-4° detector independently recovers the canonical OrbitTrace candidate. Pristine cross-survey generalization is not claimed.

This is the final paper-facing scientific scope. Algorithm development is closed.

## A. Literature superiority — PAPER METHOD: COMPLETE for tested major unsupervised comparators

Preferred paper/full-catalogue method: **recurrent-EOM HDBSCAN v1**.

Matched-capacity target-excluded GMN audit:

- binding run `32156065072`;
- result SHA-256 `6c3c7fe927b80f5913088d3698609d07cca0174a95650b6cd6ec69712e31a0ff`;
- exact verdict `PASS_RECURRENT_EOM_GMN_MATCHED_CAPACITY_LITERATURE_4_OF_4`.

Exact panels:

| Comparator | Year | K | recurrent-EOM macro-F1 / recovered | literature macro-F1 / recovered |
|---|---:|---:|---:|---:|
| Sugar deterministic published core | 2022 | 525 | `0.4101880487 / 159` | `0.1560767368 / 51` |
| Sugar deterministic published core | 2023 | 751 | `0.4331949969 / 168` | `0.1867479121 / 59` |
| published-config catalogue HDBSCAN | 2022 | 74 | `0.1604026871 / 69` | `0.1178314415 / 43` |
| published-config catalogue HDBSCAN | 2023 | 88 | `0.1863409900 / 79` | `0.1323561897 / 57` |

All four require strict macro-F1 superiority and no recovered-shower loss at **identical catalogue capacity**.

Independent exposed SonotaCo 2013/2014 development/validation evidence also gives recurrent-EOM 4/4 wins over the corresponding frozen literature comparator under the established matched-panel evaluator.

### Claim boundary

This supports superiority to the **tested** major unsupervised comparator implementations, not universal superiority to every meteor-stream algorithm.

The GMN Sugar route represents the deterministic published DBSCAN core, not its full uncertainty-resampling pipeline. The SonotaCo benchmark is exposed, not pristine external validation.

## B. Literature superiority — density-sync cross-check: COMPLETE

Density-synchronous recurrent-EOM is not the preferred paper method, but it independently passed the same matched-capacity GMN characterization after its method bytes were already frozen:

- run `32193713209`;
- result SHA-256 `b4f4aea785ea309f66dda31f60f54f0a798b88f036493c456e9b89d4b7bf6619`;
- verdict `PASS_DENSITY_SYNC_GMN_MATCHED_CAPACITY_LITERATURE_4_OF_4`.

This shows that the literature advantage is not fragile to the small recurrent-vs-density-sync ordering difference, while the direct SonotaCo tie still favors recurrent-EOM for the paper by parsimony.

## C. Sample-size generalization — SPARSE TOPOMODAL: STRONG WITHIN-GMN EVIDENCE

Fixed-scale native TopoModal remains the sparse-survey/sample-size robustness method.

Frozen GMN sparse-stress evidence shows large gains versus fixed-support HDBSCAN/recurrent-EOM across ~5.8k and ~0.7k sample scales, including:

- ~0.7k qualified recovery `20 → 31`, dominant precision `0.3530 → 0.5887`;
- ~5.8k qualified recovery `94 → 140`, dominant precision `0.3396 → 0.5544`;
- no qualified-recovery loss in the frozen 16 bucket-year panels;
- 4/4 cross-scale structural wins.

This is **sample-size robustness**, not cross-survey external validation.

Attempts to extend the sparse recurrent–TopoModal Pareto architecture cleanly to denser d=64 panels failed frozen structural/truth gates. Those failures are preserved and prohibit claiming general full-scale TopoModal portability.

## D. Targeted OrbitTrace recovery — COMPLETE for the separately frozen fixed-4° detector

The canonical OrbitTrace/GhostStream target was opened in the already-frozen fixed-4° candidate-recovery application, PR #153. This was a one-shot targeted recovery after the detector, calibration procedure, application code, and interpretation gates were fixed.

Binding evidence:

- run `30927310565`;
- artifact `8899766878`;
- artifact digest `sha256:0288bd50c88c1dee8bf5b72bd52937116d81026f074667450c99cb8d8c56653c`;
- exact verdict `FULL_FROZEN_GHOSTSTREAM_RECOVERY`;
- all 14 frozen gates passed;
- negative-window FPR `0.0515625` at alpha 0.05 and `0.00703125` at alpha 0.01;
- recall at alpha 0.05 / 0.01: k=4 `0.70/0.30`, k=6 `1.00/0.70`, k=8 `1.00/0.95`, k=12 `1.00/1.00`.

Every application year 2022–2026 produced nominally significant recovery.

### Claim boundary

This strongly links the independently developed fixed-4° detector to the canonical OrbitTrace structure under a frozen targeted application. It is **not** the historical discovery method, **not** a blind catalogue rediscovery, and **not** evidence used to select or tune recurrent-EOM.

## E. Cross-survey transport — MIXED; pristine generalization not established

Existing evidence:

- NASA ASFN 2018/2019: binding negative for recurrent-EOM; recurrent mechanism inactive and superiority not established.
- EFN 2017/2018: mechanism inactive at pretruth; labels left unopened.
- SonotaCo 2013/2014: positive exposed benchmark, not pristine external validation.
- AMOS 2023/2024: never accessed; historical preregistration remains unexecuted.

Therefore the paper method **cannot and will not claim pristine cross-survey generalization**.

This is a final limitation, not an invitation to search for another survey or alter the method.

## F. Historical AMOS endpoint — ABANDONED / UNEXECUTED

PR #1268 froze a prospective density-sync AMOS endpoint and PR #1351 froze a recurrent-EOM secondary characterization before any AMOS scientific access. Those documents remain valid provenance for what would have been tested.

Project decision now closes that lane:

- no AMOS event row or shower association was opened;
- no provider request was sent;
- no AMOS result exists;
- no AMOS outreach or execution is authorized as part of the current paper;
- no replacement external survey is authorized to rescue the missing pristine-generalization claim.

The correct manuscript treatment is simply that pristine cross-survey validation was not established.

## G. Method-search closure

No new algorithm version is justified or authorized for the current paper.

Do not launch:

- recurrent-EOM successors;
- density-sync successors;
- dense-scale TopoModal rescue variants;
- another external-survey search;
- post-target-reveal tuning;
- gate relaxation after a negative result.

The remaining work is evidence presentation and writing only.

## Firewall clarification

The target interval `[20°,55°]` is **not globally unopened**. It was accessed only for the frozen PR #153 targeted fixed-4° application. Recurrent-EOM development/selection and all literature comparisons remained target-excluded: no target event, target label, target coordinate, or target result was allowed to alter the selected paper method or its gates. AMOS rows/labels, MAARSY, and DMS were not opened.

## Bottom line

- **Beats tested literature fairly:** YES, binding 4/4 for the selected recurrent-EOM paper method.
- **Generalizes across sample size:** YES for fixed-scale TopoModal on frozen GMN sparse stress.
- **Independently recovers the canonical OrbitTrace target under a frozen targeted test:** YES for the separately frozen fixed-4° detector.
- **Generalizes to a pristine independent survey:** NO CLAIM; not established.
- **Algorithm development:** CLOSED.
- **Remaining scientific blocker for the bounded paper claim:** NONE.
- **Remaining project work:** figures, tables, manuscript integration, and final claim-to-evidence audit.