# Topomodal lineage-interleaved v2 — binding result

## Verdict

🔴 **FAIL_TOPOMODAL_LINEAGE_INTERLEAVED_V2 — CLOSED.**

Binding workflow run: `31964062627`

Binding artifact: `9268054492` (`orbittrace-topomodal-lineage-interleaved-v2`)

Immutable prelabel SHA-256:

`336a3226aa54e9bab9fb28345548fdcbbb52eced1c8cdd1021abf9d29fdccf82`

The complete exact #1284 candidate universe and exact previously-frozen intrinsic ranking were reproduced before lineage assignment. The lineage-interleaved order was then sealed before shower truth was opened. The evaluator used the unchanged recurrent-EOM truth metric and the same ten frozen gates.

## Aggregate truth result

### Fine sparse scale — denominator 1024 (~0.7k events per pooled subset)

| Metric | recurrent-EOM | lineage-interleaved v2 |
|---|---:|---:|
| qualified total | 20 | **31** |
| recovered @25 | 20 | **31** |
| recovered @50 | 20 | **31** |
| recovered @100 | 20 | **31** |
| recovered @500 | 20 | **31** |
| mean dominant precision | 0.3530315709574533 | **0.5886672679172679** |
| mean MRR | **0.6959325396825397** | 0.5404513888888889 |
| mean fragmentation | 1.0 | 1.0 |

Panelwise qualified recovery: 8/8 nonlower, 6/8 strict wins, 0 losses.

### Coarse sparse scale — denominator 128 (~5.8k events per pooled subset)

| Metric | recurrent-EOM | lineage-interleaved v2 |
|---|---:|---:|
| qualified total | 94 | **140** |
| recovered @25 | 87 | **129** |
| recovered @50 | 94 | **140** |
| recovered @100 | 94 | **140** |
| recovered @500 | 94 | **140** |
| mean dominant precision | 0.3396191653933494 | **0.5543714415470113** |
| mean MRR | **0.23584530975502274** | 0.18702656347669294 |
| mean fragmentation | 1.0 | 1.0 |

Panelwise qualified recovery: 8/8 nonlower, 8/8 strict wins, 0 losses.

## Frozen gates

Passed:

- fine qualified total strictly greater;
- fine qualified nonlower in >=6/8 panels;
- fine precision not lower;
- fine fragmentation not higher;
- coarse qualified total not lower;
- coarse qualified nonlower in >=6/8 panels;
- coarse precision not lower;
- coarse fragmentation not higher.

Failed:

- **fine mean MRR not lower**;
- **coarse mean MRR not lower**.

Therefore 8/10 gates passed, but the preregistered verdict requires all ten.

## Scientific interpretation

The fixed-scale ToMATo/#1284 candidate generator remains strongly positive for sparse known-stream **coverage and purity**. Lineage-interleaving preserves those gains but does not repair early ordering enough to match recurrent-EOM MRR.

This result closes this exact lineage scheduling architecture. Do not change lineage definition, round scheduling, intrinsic order, radius, support floor, candidate universe, metric, or gates after outcome. In particular, do not create a lineage-v3 by tuning a lineage quota, round weight, overlap threshold, or alternative within-lineage order from this result.

The next architecture should change the *evidence used to prioritize stream-like candidates*, not cosmetically reorder the same hierarchy.

## Firewall

The protected inclusive solar-longitude interval `[20°,55°]` remained excluded. No OrbitTrace target information/events, SonotaCo event rows, ASFN/EFN event rows, MAARSY, or DMS entered the GMN experiment. The pre-frozen SonotaCo v2 transfer protocol was not executed because GMN v2 failed.