# OrbitTrace goal status — literature superiority + external generalization

## Target claim

The project goal tracked here is deliberately narrower than “best algorithm ever”:

> A frozen meteor-stream detection methodology outperforms relevant published unsupervised comparator implementations under fair fixed-capacity evaluation and demonstrates that its improvement transfers to a genuinely unseen meteor survey without post-result method changes.

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

Fixed-scale native TopoModal remains the sparse-survey flagship.

Frozen GMN sparse-stress evidence shows large gains versus fixed-support HDBSCAN/recurrent-EOM across ~5.8k and ~0.7k sample scales, including:

- ~0.7k qualified recovery `20 → 31`, dominant precision `0.3530 → 0.5887`;
- ~5.8k qualified recovery `94 → 140`, dominant precision `0.3396 → 0.5544`;
- no qualified-recovery loss in the frozen 16 bucket-year panels;
- 4/4 cross-scale structural wins.

This is **sample-size robustness**, not yet cross-survey external validation.

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

## E. Pristine cross-survey generalization — NOT YET ESTABLISHED

### Existing evidence

- NASA ASFN 2018/2019: binding negative for recurrent-EOM; recurrent mechanism inactive and superiority not established.
- EFN 2017/2018: mechanism inactive at pretruth; labels left unopened.
- SonotaCo: useful exposed benchmark, not pristine external validation.
- AMOS 2023/2024: still pristine; no event row or shower association has been opened.

Therefore the paper method currently **cannot** claim pristine cross-survey generalization.

## F. AMOS one-shot readiness

Primary historical endpoint remains the pre-data density-sync AMOS pipeline frozen in PR #1268, preserving the earlier no-method-switch governance. Its pretruth already contains ordinary HDBSCAN, recurrent-EOM and density-sync candidate catalogues before labels.

A pre-data secondary recurrent-EOM characterization is frozen in PR #1351. It consumes only the single #1268 post-freeze result JSON—never raw AMOS geometry or labels—and applies the exact recurrent-EOM development gate on the same one-shot receipt:

- five annual no-regression conditions in each of 2023 and 2024: @50, @100, top-100 precision, MRR, fragmentation;
- strict @100 improvement in at least one year;
- recurrent mechanism active versus ordinary EOM;
- 12/12 booleans required.

Positive token:

`PASS_RECURRENT_EOM_HDBSCAN_V1_AMOS_2023_2024_EXTERNAL_CHARACTERIZATION`

Negative token:

`FAIL_RECURRENT_EOM_HDBSCAN_V1_AMOS_2023_2024_EXTERNAL_CHARACTERIZATION`

A valid FAIL closes pristine generalization for recurrent-EOM and does not authorize another survey.

## G. Acquisition blocker

No current public source was found that satisfies the exact frozen AMOS 2023/2024 complete multi-station field/sample contract. EDMOND cannot silently substitute for AMOS under the frozen survey definition.

Current official provider contact checked 2026-08-18:

- Prof. RNDr. Juraj Tóth, PhD.
- AMOS Principal Investigator, Comenius University in Bratislava
- `Juraj.Toth@fmph.uniba.sk`

The staged request is ready but has not yet been sent from the repository workflow state.

## Firewall clarification

The target interval `[20°,55°]` is **not globally unopened**. It was accessed only for the frozen PR #153 targeted fixed-4° application. Recurrent-EOM development/selection and all literature/AMOS gates remain target-excluded: no target event, target label, target coordinate, or target result may alter the selected paper method or its external-validation endpoint. AMOS rows/labels, MAARSY, and DMS remain unopened.

## Bottom line

- **Beats tested literature fairly:** YES, binding 4/4 for the selected recurrent-EOM paper method.
- **Generalizes across sample size:** YES for fixed-scale TopoModal on frozen GMN sparse stress.
- **Independently recovers the canonical OrbitTrace target under a frozen targeted test:** YES for the separately frozen fixed-4° detector.
- **Generalizes to a pristine independent survey:** NOT YET.
- **Remaining scientific blocker:** obtain the frozen AMOS 2023/2024 staged transfer and execute the already-frozen one-shot endpoint plus recurrent-EOM secondary adjudication. No further method search is justified before that test.
