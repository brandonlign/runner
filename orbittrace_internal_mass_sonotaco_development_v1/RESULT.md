# OrbitTrace support-cut × annual-density internal-mass — SonotaCo development v1

## Verdict

🟢 **PASS_INTERNAL_MASS_SONOTACO_DEVELOPMENT_V1**

Binding GitHub Actions reproduction: `32259703637`

The first technically valid score was produced locally after the protocol was frozen and after the exact direct accumulator passed deterministic brute-force zero-label audits. GitHub Actions subsequently reproduced that result from immutable artifacts and exact source bytes. The earlier CI attempts `32259187318` and `32259238847` failed before scientific scoring because the committed C++ file was not byte-identical to the locally validated accelerator; restoring the exact bytes was an engineering/provenance repair only.

## Binding development result

Support-resolved TopoModal + frozen annual-density internal mass (`M_2D`) versus tuned ordinary HDBSCAN on the exact symmetric-v2 SonotaCo common universe:

| metric | internal-mass TopoModal | tuned HDBSCAN |
|---|---:|---:|
| mean AUC macro-F1 | **0.35364538749003405** | 0.345475559012312 |
| mean macro-F1 @40 | **0.5012446318461822** | 0.46086713246967964 |
| total recovered @40 | **58** | 52 |
| mean native macro-F1 | **0.7266723655790133** | 0.4762894120871253 |

Primary AUC improvement over tuned HDBSCAN: **+0.00816982847772205 absolute** (~2.36% relative to HDBSCAN).

The same 888 support-resolved candidate memberships were retained. Only the already-GMN-frozen ordering was changed from modal contrast to the exact internal two-density persistence mass

`M_2D(S) = (1 / |S|) * sum_{B subseteq S} |B| A(B)`.

## Annual curves

### 2013

- AUC macro-F1: `0.3409964214444565`
- K10/K20/K30/K40 macro-F1: `0.17600248961791834 / 0.3167872010999374 / 0.39105168928185147 / 0.48014430577811906`
- recovered @40: `29`
- native macro-F1: `0.7212989262980645`

### 2014

- AUC macro-F1: `0.36629435353561157`
- K10/K20/K30/K40 macro-F1: `0.18928897121161103 / 0.34060402795521405 / 0.412939457061376 / 0.5223449579142453`
- recovered @40: `29`
- native macro-F1: `0.7320458048599622`

## Frozen gates

All five preregistered development gates passed:

1. AUC strictly beats tuned HDBSCAN;
2. AUC strictly beats the fixed modal-transfer baseline;
3. recovered @40 is at least 52;
4. candidate memberships exactly reproduce the fixed 888-candidate catalogue;
5. candidate generation and internal-mass ranking are label-free.

No post-result parameter search was performed.

## Exact-accelerator audit

The direct maximum-spanning-forest accumulator was checked against brute-force threshold enumeration on five deterministic candidates before the score endpoint. Absolute discrepancies were at floating-point roundoff (`0` to `5.3e-23`). The binding source SHA-256 is

`4eef6f1b70b5baee5d1983d2480c02d73569b12af868ec23bbb6009d6ca1fa37`.

Ranked-pretruth SHA-256:

`9be0e77d650cabd94eccf0623f005705bb86e84793c76190b0065621631f2ecd`.

## Claim boundary

This is **real SonotaCo development benchmark progress**, not pristine independent generalization. The earlier fixed-modal SonotaCo aggregate was already observed before this ranking was selected for testing, even though the `M_2D` mechanism itself had been frozen previously on target-excluded GMN with SonotaCo inaccessible. Therefore the next scientific step is a separately frozen, untouched external validation. The negative symmetric-v2 result for recurrent-EOM remains unchanged: recurrent-EOM does not beat tuned HDBSCAN there.
