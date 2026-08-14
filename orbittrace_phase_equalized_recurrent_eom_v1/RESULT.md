# Phase-intensity-equalized recurrent-EOM HDBSCAN v1 — binding GMN result

## 🔴 NEGATIVE scientific result

The first technically valid target-excluded GMN 2022/2023 endpoint **failed** the frozen promotion gate against promoted recurrent-EOM HDBSCAN v1.

Verdict:

`FAIL_PHASE_EQUALIZED_RECURRENT_EOM_V1_GMN_DEVELOPMENT`

The result is binding. The exact phase-equalization successor is permanently closed; no alternate origin, per-year/equal-year CDF, smoothing, binning, blending strength, HDBSCAN setting, recurrent combiner, ranking, or fusion rescue is authorized.

## Binding provenance

- workflow run: `31851330153`;
- execution head: `ecfa7fb83e0c8bfe7897ca5592dd348c9ac6fa93`;
- artifact: `9237680835`;
- artifact digest: `sha256:2b1f68ca89401410126f04dfe5170f95ff73b3f6d98784ccbc73484667e4245e`;
- result SHA-256: `b0602fd7bd024733c0960332318124e62a9889e1531d9676e9b1ec8f820352d9`;
- prelabel SHA-256: `c6548176b24728113edbe46fb56f069846405f36da43e2fa5564cb21a8649817`.

The workflow completed the scientific endpoint, exact parent-metric reproduction, scientific-firewall enforcement, provenance preservation, and artifact upload successfully. This is not a technical no-result.

## Mechanism activity

The transform was nonidentity on the real pooled GMN input and changed the HDBSCAN candidate universe:

- promoted recurrent-EOM parent candidates: **2,097**;
- phase-equalized successor candidates: **2,014**;
- `mechanism_active=true`.

Thus the failure is scientifically informative rather than an inactive-transform tie.

## Exact metrics

### 2022

| Metric | recurrent-EOM parent | phase-equalized successor |
|---|---:|---:|
| recovered @25 | 22 | 22 |
| recovered @50 | **45** | 42 |
| recovered @100 | **89** | 81 |
| recovered @500 | **193** | 189 |
| top-100 dominant precision | **0.7856486013** | 0.7501905607 |
| MRR | **0.0224982696** | 0.0222945172 |
| median top-500 fragmentation | 1.0 | 1.0 |
| qualified matches | **236** | 228 |

Frozen 2022 gates failed for recovered@50, recovered@100, top-100 precision, and MRR. Fragmentation tied.

### 2023

| Metric | recurrent-EOM parent | phase-equalized successor |
|---|---:|---:|
| recovered @25 | **23** | 22 |
| recovered @50 | **46** | 42 |
| recovered @100 | **89** | 82 |
| recovered @500 | 192 | **193** |
| top-100 dominant precision | **0.7867680237** | 0.7580210390 |
| MRR | **0.0220239289** | 0.0216283270 |
| median top-500 fragmentation | 1.0 | 1.0 |
| qualified matches | **244** | 236 |

Frozen 2023 gates failed for recovered@50, recovered@100, top-100 precision, and MRR. Fragmentation tied. The one-event @500 increase is reporting-only and cannot rescue the failed primary gates.

Across the two years, `strict_recovered_at_100_improvement_some_year=false`.

## Interpretation

Empirical phase-intensity equalization substantially changes the density geometry, but on the permanent target-excluded GMN development split it removes or demotes useful stream structure faster than it removes seasonal/background-density distortion. The net result is lower fixed-budget recovery, lower top-100 precision, and lower MRR in both years.

This result does not authorize partial equalization or a blend with raw solar phase. Those are outcome-informed variants explicitly prohibited by the pre-outcome protocol.

Promoted recurrent-EOM HDBSCAN v1 remains the methodology parent.

## Dormant SonotaCo contingency

The separately preregistered SonotaCo parent benchmark in PR #1260 must remain dormant and be closed without scientific execution because activation required a GMN PASS. No SonotaCo value was accessed by this successor.

## Firewall

Binding result records/guarantees:

- target-excluded GMN 2022/2023 development only;
- inclusive blind exclusion `[20.0,55.0]`;
- `target_information_access=false`;
- `target_region_events_accessed=false`;
- `sonotaco_2013_2014_access=false`;
- `amos_scientific_access=false`;
- `efn_scientific_access=false`;
- `asfn_scientific_access=false`;
- `maarsy_scientific_access=false`;
- `dms_scientific_access=false`;
- `post_result_parameter_search=false`.
