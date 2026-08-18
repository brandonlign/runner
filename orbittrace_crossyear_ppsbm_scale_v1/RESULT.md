# Cross-year degree-corrected PP-SBM scale v1 — binding Stage-1 result

## Verdict

`FAIL_CROSSYEAR_PPSBM_SCALE_V1_PRETRUTH`

This is the binding zero-label Stage-1 scientific result. Shower truth was never opened. The exact raw-cross-year degree-corrected PP-SBM v1 lane is closed; there is no parameter/model rescue.

## Frozen science

- protocol blob: `939c529ca1db732d23fd6e8b4f0b6957176a5042`
- graph builder blob: `d43af9a95c0d273a6c2bfe2be44a7cb5b434c51b`
- PP-SBM runner blob: `18de1020ccc8cfc159e03be6c25a3f26f0c31516`
- pretruth evaluator blob: `4f1ebda9894f8134831c98631222f25dad242e7a`

## Binding execution

- execution branch: `agent/orbittrace-crossyear-ppsbm-scale-v1-activate`
- execution commit: `b5162163dcd410a45dd5ecc3f7c2fd7e1b229590`
- workflow run: `32089375186`
- artifact: `9307888176`
- artifact digest: `sha256:f00f8eddcf1ddd6133d34c43c1a142e376b1ef9ca152e35c3ba435ffcf7a9e4f`
- graph-freeze SHA-256: `98300e2d0463b09e91ad48d04ce23a621f3931dc84c3538261fe1c8556b8a117`
- partitions SHA-256: `63e625379da420041909047c007ebeb8428b0afe6428bcd71bcb014d9b2360cb`
- pretruth-result SHA-256: `26d4a2f88f0c7d235cb7162a111e5b8fc40b9c35d161788279c0eb02dec8281b`

## Gate count

Passed **9/12** frozen structural gates.

Passed:

- annual support floor in every panel;
- candidate membership stayed inside the frozen universe;
- fixed-seed repeatability in every panel;
- positive-degree inference only;
- pairwise-disjoint candidates;
- strict cross-year graph construction;
- immutable endpoint source;
- runtime pin;
- complete firewall.

Failed:

1. `capacity_at_least_reference_k_all_8`
2. `cross_scale_nonlower_4_of_4`
3. `cross_scale_mean_not_lower`

## Capacity diagnosis

Eligible PP-SBM candidate counts versus frozen equal-budget reference K:

| scale | bucket | PP-SBM candidates | reference K |
|---|---:|---:|---:|
| d128 | 0 | 6 | 29 |
| d128 | 1 | 6 | 35 |
| d128 | 2 | 17 | 38 |
| d128 | 3 | 6 | 33 |
| d1024 | 0 | 6 | 8 |
| d1024 | 1 | 6 | 5 |
| d1024 | 2 | 29 | 6 |
| d1024 | 3 | 20 | 9 |

The PP-SBM partition therefore lacked catalogue breadth in all four coarse panels and one fine panel. The problem is not a truth-label ranking defect; it appears before truth is available.

## Cross-scale structural agreement

Mean best-Jaccard agreement between matched coarse/fine bucket representations:

| bucket | PP-SBM | reference | non-lower? |
|---:|---:|---:|---|
| 0 | 0.6620487635 | 0.5606150794 | yes |
| 1 | 0.7452537796 | 0.7051527695 | yes |
| 2 | 0.1410133791 | 0.5504804711 | no |
| 3 | 0.1137746536 | 0.6571853102 | no |

Aggregate cross-scale mean:

- PP-SBM: `0.41552264393968347`
- reference: `0.6183584075451847`
- bucket wins/ties: `2/4`

## Scientific interpretation

The statistical block model did solve the earlier giant-connected-component problem in the narrow sense that it returned repeatable, disjoint assortative partitions without touching shower truth. But its inferred partition granularity was far too coarse in the high-population d128 panels and structurally unstable across scale in buckets 2 and 3. This fails the frozen authorization criterion before any retrieval evaluation is scientifically permitted.

The result argues against replacing the recurrent sparse-candidate catalogue with this exact global raw-cross-year PP-SBM partition. It does not authorize changing the block-model family, priors, nesting, edge construction, block-count handling, or postprocessing after observing this failure.

## Firewall

Binding artifact records all of the following as false: target information access, target-region event access, shower-truth use, SonotaCo 2013/2014 access, ASFN/EFN event-level access, AMOS/MAARSY/DMS scientific access, orbital information access, station metadata access, uncertainty metadata access, and post-result parameter search.
