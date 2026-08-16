# OrbitTrace topomodal orbital Fréchet ordering v1 — binding result

## Verdict

**FAIL_TOPOMODAL_ORBITAL_FRECHET_V1**

The frozen orbital ordering failed 4/10 truth gates and passed 6/10. It retained the #1284 fine-scale recovery gain but substantially worsened MRR, and at the coarse sparse scale it also reduced qualified recovery and early recovery. The entire preregistered orbital-D ordering family is therefore closed; no result-informed substitute D function, robust dispersion statistic, size correction, root-tier change, threshold, fusion, or orbital-feature rescue is permitted.

## Binding provenance

- GitHub Actions run: `31979181650`
- Job: `95243157193`
- Artifact: `9271901043`
- Artifact ZIP SHA-256: `837138d659e0ca4a15001c5e5eb86854e9463f54d79fc2f5570046a74e44ad2c`
- Immutable orbital prelabel SHA-256: `a098e42077d18b06f3b9fb0813031b4e6e90f0c39cd17848dccb57c80c692bb6`
- Source #1284 pretruth SHA-256: `db608f84bf333d18d624199f2d31c27b4183ee3a75a3d930cef4b9766a19d4de`
- Orbit mapping SHA-256: `a99fdc71beb8ea78b957c0951191c66bf8c04e6ce04773952ac0c43695619f44`
- #1284 structural result SHA-256: `e8cf7d92e96db9a1c99578f6efc63baf1534b94ab975e94f789fa6bc4a718497`

The candidate order was computed in a label-inaccessible job, serialized, and SHA-256 bound before the truth evaluator started. The truth workflow accepted that exact hash before parsing shower labels. The protected solar-longitude interval 20°–55° remained excluded. No OrbitTrace target information was accessed. SonotaCo 2013/2014, ASFN/EFN event-level data, AMOS, MAARSY, and DMS were not accessed scientifically.

## Exact aggregate metrics

### Fine sparse scale — denominator 1024 (~700 events)

| Metric | recurrent-EOM | successor |
|---|---:|---:|
| Qualified recovery | 20 | 31 |
| Recovered @25 | 20 | 31 |
| Recovered @50 | 20 | 31 |
| Recovered @100 | 20 | 31 |
| Recovered @500 | 20 | 31 |
| Mean MRR | 0.6959325396825397 | 0.34490575396825396 |
| Mean top-100 dominant precision | 0.3530315709574533 | 0.5886672679172679 |
| Mean fragmentation | 1.0 | 1.0 |

- Qualified nonlower panels: **8/8**
- Qualified strict-win panels: **6/8**

### Coarse sparse scale — denominator 128 (~5.8k events)

| Metric | recurrent-EOM | successor |
|---|---:|---:|
| Qualified recovery | 94 | 92 |
| Recovered @25 | 87 | 73 |
| Recovered @50 | 94 | 92 |
| Recovered @100 | 94 | 92 |
| Recovered @500 | 94 | 92 |
| Mean MRR | 0.23584530975502274 | 0.13162537110879657 |
| Mean top-100 dominant precision | 0.3396191653933494 | 0.4484765237893734 |
| Mean fragmentation | 1.0 | 1.0 |

- Qualified nonlower panels: **3/8**
- Qualified strict-win panels: **2/8**
- Qualified-loss panels: **5/8**

## Truth gates

PASS:
- `fine_qualified_total_strictly_greater`
- `fine_qualified_nonlower_at_least_6_of_8`
- `fine_precision_mean_not_lower`
- `fine_fragmentation_mean_not_higher`
- `coarse_precision_mean_not_lower`
- `coarse_fragmentation_mean_not_higher`

FAIL:
- `fine_mrr_mean_not_lower`
- `coarse_qualified_total_not_lower`
- `coarse_qualified_nonlower_at_least_6_of_8`
- `coarse_mrr_mean_not_lower`

## Scientific interpretation

The negative result is stronger than another MRR-only miss. Orbital self-coherence is not merely an insufficient ordering score for this hierarchy: at the coarse sparse scale it systematically moves enough true stream-bearing candidates past the equal recurrent-EOM budget that total recovery falls from 94 to 92 and @25 falls from 87 to 73. The improved top-100 dominant precision does not compensate for this loss.

This reinforces the broader #1284 conclusion: the hierarchy contains many useful stream-bearing candidates, but generic within-candidate notions of compactness/coherence — topological prominence, station support, orbital self-coherence, and related scalar rankers — do not identify the correct early canonical representative of each stream.

## Closure

Per the frozen protocol, close the whole post-outcome orbital-D rescue family for this project: no Drummond/Jopek/other D substitutions, mean→median/trimmed/quantile changes, pairwise min/max criteria, size normalization, orbital-element subset selection, orbital thresholds, root/finite tier changes, rank fusion, station/orbit fusion, or result-informed weights.

SonotaCo/external transfer is not authorized because all ten GMN gates did not pass.
