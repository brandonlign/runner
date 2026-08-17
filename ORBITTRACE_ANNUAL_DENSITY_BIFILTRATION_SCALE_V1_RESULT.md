# OrbitTrace annual-density bifiltration scale v1 — binding result

## Verdict

🟢 **SUPPORTS_ANNUAL_DENSITY_BIFILTRATION_CROSS_SCALE_COHERENCE**

Binding zero-label workflow run: `32036777809`

Execution head: `d86d649106e3434362c73cc1da524e65bc6bb1ab`

Artifact: `9291012921` (`orbittrace-annual-density-bifiltration-scale-v1`)

Artifact ZIP digest:

`sha256:0c44eb4039a2504ba815ad0511538300b576f7edc5a90bb1b8dee33d5be53605`

Immutable pretruth candidate freeze SHA-256:

`63519bbd8a95b0bd5db0d0f5fdccbdb67b3f1dac0158529bb808f4c798170b0b`

Structural result SHA-256:

`d930e9a8221cbe6b56026618f513f3f8b84143f2f43deb0a5b1ccc1ca7e4bbe7`

## Architecture

The exact physical graph and target-excluded GMN scale-stress construction from the fixed-scale TopoModal work were retained. The scientific change was to preserve the two annual local-density fields as separate filtration coordinates instead of reducing them to a scalar such as `min(rho_2022, rho_2023)`.

For every observed positive threshold pair, the method enumerated connected components of the joint annual-density superlevel graph, deduplicated exact event memberships, and assigned each membership its exact two-dimensional **bifiltration persistence area**: the area in annual-density threshold space over which that exact component exists.

Before this result, the protocol froze the only allowed future total order:

1. persistence area descending;
2. member count descending;
3. membership SHA-256 ascending.

No shower truth entered this run and the ranking was not evaluated here.

## Candidate capacity

| scale | bucket | events | bifiltration candidates | recurrent-EOM candidates |
|---|---:|---:|---:|---:|
| d=128 | 0 | 5,567 | 3,399 | 29 |
| d=128 | 1 | 5,840 | 3,233 | 35 |
| d=128 | 2 | 5,857 | 2,733 | 38 |
| d=128 | 3 | 5,816 | 2,554 | 33 |
| d=1024 | 0 | 677 | 72 | 8 |
| d=1024 | 1 | 739 | 87 | 5 |
| d=1024 | 2 | 736 | 82 | 6 |
| d=1024 | 3 | 766 | 118 | 9 |

Fine-scale candidate non-collapse passed in all `4/4` buckets.

## Cross-scale structural result

Candidate-unweighted fine→coarse mean best Jaccard:

- annual-density bifiltration: **`0.86507969983373`**
- recurrent-EOM comparator recomputed in this endpoint: `0.6183584075451847`

Median bucket mean best Jaccard:

- annual-density bifiltration: **`0.8675760061261779`**
- recurrent-EOM: `0.6089001947872916`

Strict bucket wins: **4/4** for the bifiltration.

All five preregistered structural gates passed:

- nonempty in all eight subsets;
- fine candidate non-collapse in all four buckets;
- pooled mean Jaccard strictly above recurrent-EOM;
- median bucket Jaccard strictly above recurrent-EOM;
- at least 3/4 strict bucket wins (observed 4/4).

## Interpretation boundary

This establishes a positive **zero-label structural/generalization** result for a genuinely two-parameter annual-density topology. It does not establish known-shower recovery, MRR, catalogue ranking quality, full-GMN superiority, SonotaCo transfer, or external validation.

The frozen protocol authorizes at most one separately preregistered target-excluded GMN truth endpoint using the already-frozen persistence-area ordering. No alternate area transform, score blend, Pareto layer, path/slice, support weighting, station/orbit evidence, threshold selection, or post-result reranking is authorized.

Even if that sparse-scale truth endpoint passes, promotion against the current full-GMN density-synchronous recurrent-EOM champion would require a separate prospective comparison.

## Firewall

The protected `[20°,55°]` interval remained excluded before method operations. OrbitTrace target information/events, shower truth, SonotaCo 2013/2014, ASFN/EFN event-level data, AMOS, MAARSY, DMS, and pristine external endpoints were not accessed.
