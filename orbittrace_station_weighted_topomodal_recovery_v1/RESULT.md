# OrbitTrace station-weighted topomodal recovery v1 — binding result

## Verdict

**FAIL_STATION_WEIGHTED_TOPOMODAL_RECOVERY_V1**

The frozen successor passed 8/10 truth gates. The only failed gates were MRR non-inferiority at both sparse scales. The station-weighted lane is closed; no result-informed station-weight transform, cap, normalization, imputation, threshold, rank fusion, or related rescue is permitted.

## Binding provenance

- GitHub Actions run: `31977802895`
- Artifact: `9271574918`
- Artifact ZIP SHA-256: `1b2563a34e1f59b93565023c5a513b561e186240843d3f3b2a1b0f23487c4499`
- Immutable prelabel SHA-256: `0367cab3bd8a11df0a603c30f82c031dc3f3f2ed9a371ff5d004d8825359f393`
- Station-weighted structural result SHA-256: `a7cc8921a9431028f08c92479a001021160ee0e8cce6ed346a80d0d2510a8bb8`
- Audited `Num (stat)` mapping SHA-256: `92f6ce1961b0e8642f6bdd1cc455b07785ed8224c8f8f3d467d69fac2b82921c`

The prelabel hash was asserted before the evaluator opened shower truth. The protected solar-longitude interval 20°–55° remained excluded. No OrbitTrace target information was accessed. SonotaCo 2013/2014, ASFN/EFN event-level data, AMOS, MAARSY, and DMS were not accessed scientifically in this experiment.

## Exact aggregate metrics

### Fine sparse scale — denominator 1024 (~700 events)

| Metric | recurrent-EOM | successor |
|---|---:|---:|
| Qualified recovery | 20 | 31 |
| Recovered @25 | 20 | 31 |
| Recovered @50 | 20 | 31 |
| Recovered @100 | 20 | 31 |
| Recovered @500 | 20 | 31 |
| Mean MRR | 0.6959325396825397 | 0.5361383928571428 |
| Mean top-100 dominant precision | 0.3530315709574533 | 0.5964797679172679 |
| Mean fragmentation | 1.0 | 1.0 |

- Qualified nonlower panels: **8/8**
- Qualified strict-win panels: **6/8**

### Coarse sparse scale — denominator 128 (~5.8k events)

| Metric | recurrent-EOM | successor |
|---|---:|---:|
| Qualified recovery | 94 | 134 |
| Recovered @25 | 87 | 121 |
| Recovered @50 | 94 | 134 |
| Recovered @100 | 94 | 134 |
| Recovered @500 | 94 | 134 |
| Mean MRR | 0.23584530975502274 | 0.19078985331790804 |
| Mean top-100 dominant precision | 0.3396191653933494 | 0.516231628755591 |
| Mean fragmentation | 1.0 | 1.0 |

- Qualified nonlower panels: **8/8**
- Qualified strict-win panels: **8/8**

## Truth gates

- `fine_qualified_total_strictly_greater`: PASS
- `fine_qualified_nonlower_at_least_6_of_8`: PASS
- `fine_mrr_mean_not_lower`: **FAIL**
- `fine_precision_mean_not_lower`: PASS
- `fine_fragmentation_mean_not_higher`: PASS
- `coarse_qualified_total_not_lower`: PASS
- `coarse_qualified_nonlower_at_least_6_of_8`: PASS
- `coarse_mrr_mean_not_lower`: **FAIL**
- `coarse_precision_mean_not_lower`: PASS
- `coarse_fragmentation_mean_not_higher`: PASS

## Structural result retained as positive evidence

The preceding zero-label station-weighted structural diagnostic remains a strong structural PASS:

- pooled fine→coarse mean-best Jaccard: **0.8396117926550738** vs recurrent-EOM **0.6152941107471891**
- median-bucket value: **0.8442350088183421** vs recurrent-EOM **0.6089001947872916**
- strict bucket wins: **4/4**
- all five preregistered structural gates passed

This strengthens the repeated conclusion from the #1284 family: candidate generation, sparse recovery, purity, fragmentation, and sample-size stability are substantially improved relative to recurrent-EOM, while early candidate ordering remains the unresolved bottleneck.

## Closure

This exact station-weighted successor is permanently closed after its first technically valid truth outcome. Do not rescue it with transformed/capped station weights, alternative station-support thresholds, alternate graph scales, rank fusion, changed support floors, or other result-informed variants. SonotaCo transfer is not authorized because all ten GMN gates did not pass.
