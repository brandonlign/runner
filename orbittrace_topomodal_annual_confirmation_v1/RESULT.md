# OrbitTrace topomodal annual topology confirmation v1 — binding result

## Verdict

**FAIL_TOPOMODAL_ANNUAL_CONFIRMATION_V1**

The frozen annual-confirmation successor passed 8/10 truth gates. The only failed gates were MRR non-inferiority at both sparse scales. This exact annual-topology-confirmation ordering family is permanently closed under the frozen no-rescue rule.

## Binding provenance

- GitHub Actions truth run: `31979766910`
- Truth job: `95244571744`
- Binding result artifact: `9272055069`
- Binding result artifact ZIP SHA-256: `91c2b4d613f7ad3b6d66fd6473ffc25471335c83167a60247dbf378f52b64833`
- Immutable annual-confirmation prelabel SHA-256: `b8a4d3687e9545bb8bcce1bc1b75fb30321b0d627a0e47ff81261ce272d2071f`
- Prelabel artifact: `9272007725`
- Prelabel artifact ZIP SHA-256: `34e98f9326f506094ea36a1583b0f2666d806f6a324a1958498f00568d06c6e8`
- Source #1284 pretruth SHA-256: `db608f84bf333d18d624199f2d31c27b4183ee3a75a3d930cef4b9766a19d4de`
- Exact sparse-universe manifest SHA-256: `3ed5c33216d7d1cf2cbc703da088b3a86132e50532fb996cfe475d7f6052d7f8`

The annual topologies and complete candidate order were computed with shower truth inaccessible, serialized, and SHA-256 sealed. The truth workflow accepted that exact hash before the evaluator parsed shower labels. The protected solar-longitude interval 20°–55° remained excluded. No OrbitTrace target information was accessed. SonotaCo 2013/2014, ASFN/EFN event-level data, AMOS, MAARSY, and DMS were not accessed scientifically.

## Exact aggregate metrics

### Fine sparse scale — denominator 1024 (~700 events)

| Metric | recurrent-EOM | successor |
|---|---:|---:|
| Qualified recovery | 20 | 30 |
| Recovered @25 | 20 | 30 |
| Recovered @50 | 20 | 30 |
| Recovered @100 | 20 | 30 |
| Recovered @500 | 20 | 30 |
| Mean MRR | 0.6959325396825397 | 0.5531498015873015 |
| Mean top-100 dominant precision | 0.3530315709574533 | 0.5918964345839346 |
| Mean fragmentation | 1.0 | 1.0 |

- Qualified nonlower panels: **8/8**
- Qualified strict-win panels: **6/8**

### Coarse sparse scale — denominator 128 (~5.8k events)

| Metric | recurrent-EOM | successor |
|---|---:|---:|
| Qualified recovery | 94 | 117 |
| Recovered @25 | 87 | 103 |
| Recovered @50 | 94 | 117 |
| Recovered @100 | 94 | 117 |
| Recovered @500 | 94 | 117 |
| Mean MRR | 0.23584530975502274 | 0.20142900980275852 |
| Mean top-100 dominant precision | 0.3396191653933494 | 0.6072831975600865 |
| Mean fragmentation | 1.0 | 1.0 |

- Qualified nonlower panels: **7/8**
- Qualified strict-win panels: **6/8**
- Qualified-loss panels: **1/8**

## Gates

PASS:
- `fine_qualified_total_strictly_greater`
- `fine_qualified_nonlower_at_least_6_of_8`
- `fine_precision_mean_not_lower`
- `fine_fragmentation_mean_not_higher`
- `coarse_qualified_total_not_lower`
- `coarse_qualified_nonlower_at_least_6_of_8`
- `coarse_precision_mean_not_lower`
- `coarse_fragmentation_mean_not_higher`

FAIL:
- `fine_mrr_mean_not_lower`
- `coarse_mrr_mean_not_lower`

## Interpretation

Independent annual topology confirmation is meaningful evidence: compared with recurrent-EOM it substantially increases recovery and nearly doubles top-100 dominant precision at the coarse sparse scale while preserving fragmentation. It also gives better MRR than several other #1284 scalar rankers, but still does not put the first representative of each known stream early enough to clear recurrent-EOM.

The persistent pattern is now stronger: the #1284 family solves much of candidate generation, purity, fragmentation, and sample-size generalization, but ordering all complete hierarchy states remains the bottleneck. Generic scalar ranking — including intrinsic topology, lineage variants, station support, orbital self-coherence, and independent annual topology confirmation — has not solved first-hit ordering.

## Closure

Per the frozen protocol, do not rescue this outcome by replacing `min` with mean/geometric mean/product, adding a confirmation threshold, restoring/blending root priority, changing annual support, asymmetric year weights, HDBSCAN overlap, graph-scale changes, or result-informed tie breaks.

SonotaCo/external transfer is not authorized because all ten GMN gates did not pass.
