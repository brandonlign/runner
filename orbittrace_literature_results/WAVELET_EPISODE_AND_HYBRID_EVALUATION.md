# OrbitTrace wavelet-episode and hybrid evaluation

## Result

A separately labelled Brown-family three-dimensional wavelet core was transferred to the exact frozen 128-event sparse-episode benchmark. This is not a reproduction of the full CMOR catalogue survey. It preserves the published method family’s Sun-centered radiant-speed coordinates, 4° angular probe, 10% fractional speed probe, three-dimensional Mexican-hat kernel, and four-probe truncation, while using the maximum leave-one-out coefficient at observed-event locations as the episode score.

The method was frozen before SonotaCo 2025 scoring and transferred unchanged to the one-shot SonotaCo 2023 benchmark. A third, prospectively frozen evaluation was then run on SonotaCo 2022.

| Corpus | fixed4 AUROC | wavelet AUROC | Wavelet advantage |
|---|---:|---:|---:|
| SonotaCo 2025 development | 0.813250 | **0.828506** | +0.015255 |
| SonotaCo 2023 one-shot transfer | 0.811631 | **0.831972** | +0.020341 |
| SonotaCo 2022 prospective validation | 0.791405 | **0.820936** | +0.029531 |

The ordering transferred across all three years. The wavelet adaptation is therefore the strongest overall sparse-episode discriminator tested by weak-stream AUROC.

## Operating-point tradeoff

The AUROC result does not mean uniform dominance. At alpha .05, fixed4 retained higher four-member recall in every evaluated year, while the wavelet was generally stronger for six- to twelve-member episodes.

### SonotaCo 2022 prospective recall at alpha .05

| Method | k=4 | k=6 | k=8 | k=12 |
|---|---:|---:|---:|---:|
| fixed4 | **0.171053** | 0.401316 | 0.585526 | 0.815789 |
| wavelet | 0.092105 | 0.421053 | 0.703947 | 0.921053 |
| fixed4-wavelet hybrid | 0.131579 | **0.447368** | **0.723684** | **0.947368** |

On the same prospective corpus, pooled FPR at alpha .05 was 0.040246 for fixed4, 0.039299 for wavelet, and 0.040720 for the hybrid. Worst-sector FPR was 0.052083, 0.054688, and 0.049479, respectively.

## Frozen hybrid

One hybrid was specified before any hybrid score was calculated. It converts fixed4 and wavelet scores to bin-specific empirical survival p-values, applies the unweighted Tippett statistic `-log(min(p_fixed4, p_wavelet))`, and recalibrates that statistic against leave-one-out hybrid null scores in the same solar-longitude bin. No alternative combiner or learned weight was tested.

The retrospective 2025 hybrid AUROC was 0.835878, above both components. The preregistered decision, however, depended solely on fresh SonotaCo 2022.

### Prospective SonotaCo 2022 decision

| Method | Weak AUROC | Balanced recall at alpha .05 |
|---|---:|---:|
| fixed4 | 0.791405 | 0.493421 |
| wavelet | **0.820936** | 0.534539 |
| hybrid | 0.815525 | **0.562500** |

The hybrid did not exceed the wavelet’s prospective AUROC and therefore failed the promotion gate. It received the frozen decision **`RETAIN_AS_OPTIONAL_ENSEMBLE`** because it had the highest balanced alpha-.05 recall, the highest k=6/8/12 recall, and recall no lower than both components at any tested k.

## Revised methodological interpretation

The evidence no longer supports describing fixed4 as the best overall sparse-stream detector tested. The correct division is:

- **Wavelet episode adaptation:** primary overall weak-stream discriminator by reproducible AUROC across 2025, one-shot 2023, and prospective 2022.
- **fixed4:** novel topology-based ultra-sparse component with consistently better four-member recall at alpha .05, independent targeted OrbitTrace recovery, and value as a complementary ensemble component.
- **Tippett hybrid:** optional high-recall ensemble, not the primary AUROC leader.

This strengthens the methodological analysis but narrows the novel claim. The wavelet adaptation is literature-inspired, while fixed4 remains the original methodological contribution. The combined result supports a complementary multi-regime recognition framework rather than a claim that fixed4 universally outperforms established approaches.

## Provenance

### Wavelet 2025

- Workflow `31104654956`
- Artifact `8969020016`
- Artifact digest `sha256:c8d72fa8b051da05c0e4701a48302f97bf53232bd623df30a6953e05b8522232`

### Wavelet 2023 transfer

- Workflow `31105278114`
- Artifact `8969274303`
- Artifact digest `sha256:d00faaf9d781b988bbab0af09e1e27ddf0a824be63f96778bf295b4bf56c404b`

### Hybrid 2022 prospective validation

- Workflow `31107311777`
- Artifact `8970137965`
- Artifact digest `sha256:5cc0404f486e7ca060349345e42b042201a0a4732dfe680c98b1243d0ae1da43`
- Verdict `PASS_SONOTACO_2022_PROSPECTIVE_HYBRID_VALIDATION`
- Decision `RETAIN_AS_OPTIONAL_ENSEMBLE`

## Allowed claim

> On the common sparse-episode benchmark, a frozen Brown-family three-dimensional wavelet core achieved higher overall weak-stream AUROC than fixed4 in SonotaCo 2025, the one-shot SonotaCo 2023 transfer, and the prospectively frozen SonotaCo 2022 validation. fixed4 retained higher four-member recall at alpha .05, while the wavelet was stronger for moderate-member episodes. A preregistered Tippett hybrid did not exceed the wavelet’s prospective AUROC and was retained only as an optional high-recall ensemble.

## Prohibited claims

- The full CMOR catalogue survey was reproduced or beaten.
- The wavelet was uniformly superior at every member count and operating point.
- The hybrid is the primary overall discriminator.
- Wavelet, fixed4, or the hybrid historically discovered OrbitTrace.
- fixed4 is the best general sparse-stream method tested.
- The original fixed4 preregistration fully passed every robustness gate.
