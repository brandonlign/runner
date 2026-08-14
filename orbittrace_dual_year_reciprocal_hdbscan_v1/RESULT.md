# Dual-Year Reciprocal HDBSCAN v1 — binding GMN development result

**Scientific classification: NEGATIVE. Exact successor closed.**

Binding run: `31830941401`  
Artifact: `9230795883`  
Artifact digest: `sha256:63bb11aba0083357c49158c6911fafd3cfa138db09ccaa7e3762f75584fc0905`  
Execution commit: `34235b6f4a9aff7be273f3ebe42251924790db67`  
Prelabel SHA-256: `420d192b3593a83fbc13f1ed49307cf693bc1acd22e61da9992d117b7a71116a`  
Result SHA-256: `2c4a355cb2d16fe8add39c95b0ec1ae96da0e039958aeccb0deaec67cc6c846b`

Zero-truth authorization:

- run `31830868990`;
- artifact `9230610874`;
- digest `sha256:65a74e690dac905169d512ac1ef164283a3a6353c09f65c86c4dfbed31462299`;
- deterministic reciprocal matching and annual HDBSCAN compact-label/node mapping passed before GMN access.

## Frozen comparison

Accessible target-excluded GMN events:

- 2022: 315,024
- 2023: 423,658

Annual ordinary-EOM HDBSCAN cluster counts:

- 2022: 954
- 2023: 1,253

Promoted recurrent-EOM parent emitted 2,097 candidates. Parameter-free reciprocal-nearest annual coupling emitted only 598 families. The mechanism was active.

### 2022

| Metric | recurrent-EOM parent | dual-year reciprocal | Direction |
|---|---:|---:|---|
| recovered @25 | 22 | **23** | higher |
| recovered @50 | 45 | **46** | higher |
| recovered @100 | 89 | 79 | **lower by 10** |
| recovered @500 | 193 | 151 | lower by 42 |
| top-100 dominant precision | 0.7856486013 | 0.7198215161 | **lower by 0.0658271** |
| MRR | 0.0224982696 | **0.0325903972** | higher |
| median top-500 fragmentation | 1.0 | 1.0 | equal |
| full-catalogue qualified matches | 236 | 158 | lower by 78 |

Frozen failures: `recovered_at_100_not_lower=false`, `top100_precision_not_lower=false`.

### 2023

| Metric | recurrent-EOM parent | dual-year reciprocal | Direction |
|---|---:|---:|---|
| recovered @25 | 23 | **24** | higher |
| recovered @50 | 46 | **47** | higher |
| recovered @100 | 89 | 83 | **lower by 6** |
| recovered @500 | 192 | 154 | lower by 38 |
| top-100 dominant precision | 0.7867680237 | 0.6944281257 | **lower by 0.0923399** |
| MRR | 0.0220239289 | **0.0315230753** | higher |
| median top-500 fragmentation | 1.0 | 1.0 | equal |
| full-catalogue qualified matches | 244 | 166 | lower by 78 |

Frozen failures: `recovered_at_100_not_lower=false`, `top100_precision_not_lower=false`.

Binding verdict:

`FAIL_DUAL_YEAR_RECIPROCAL_HDBSCAN_V1_GMN_DEVELOPMENT`

## Interpretation

The structural idea is informative but rejected. Independently estimating annual density and keeping only reciprocal-nearest annual EOM clusters concentrates true showers very strongly at the earliest ranks (higher @25/@50 and substantially higher MRR), but it discards too much of the recoverable family universe and lowers top-100 purity. It therefore does not replace recurrent-EOM v1 under the frozen no-regression gate.

No distance threshold, one-to-many matching, alternate centroid, Hungarian matching, unmatched-cluster rescue, score blend, HDBSCAN setting, representation, or ranking change is authorized after this result. This exact lane is permanently closed.

Recurrent-EOM HDBSCAN v1 remains the methodology parent.

## Firewall

- protected `[20°,55°]` remained excluded;
- `target_information_access=false`;
- `target_region_events_accessed=false`;
- `sonotaco_2013_2014_access=false`;
- `gmn_2020_2021_access=false`;
- `maarsy_scientific_access=false`;
- `dms_scientific_access=false`;
- `post_result_parameter_search=false`.
