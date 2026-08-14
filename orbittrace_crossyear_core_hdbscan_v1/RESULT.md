# Cross-year-core HDBSCAN v1 — binding GMN development result

## 🔴 NEGATIVE scientific result

Cross-year-core HDBSCAN v1 **failed** its frozen target-excluded GMN 2022+2023 development gate against promoted recurrent-EOM HDBSCAN v1.

This is the first technically valid scientific endpoint for the frozen cross-year-core method and is therefore binding.

### Binding provenance

- clean retry workflow run: `31848227596`
- artifact: `9236769577`
- artifact digest: `sha256:f03df39fce4ac8370a7e86fde94a88d555b838968ffc192964ed87fef52868a7`
- execution commit: `4023b94661631441ef96a17ad93cb2c0d8d66e3a`
- frozen result SHA-256: `f639faa90dfcad7948a98e6b73e59d2384dfde92d0105c9d90c3303056f47fd9`
- frozen prelabel SHA-256: `c53dd2cac0d228805fd9153f6d380b11d69895a2151f233b2190761f28058e12`
- verdict: `FAIL_CROSSYEAR_CORE_HDBSCAN_V1_GMN_DEVELOPMENT`

The prior run `31847359367` remains a preserved technical no-result: it stopped on the `SingleLinkageTree._raw_tree` accessor before prelabel freeze or truth evaluation. Its semantic-neutral compatibility repair was frozen and independently audited in run `31848115820` before this clean retry. The original scientific protocol, Boruvka adapter, original development runner, recurrent-EOM extraction, ranking, metrics, and gate remained unchanged.

## Exact outcome versus promoted recurrent-EOM

| Year | Metric | recurrent-EOM parent | cross-year-core | Direction |
|---|---|---:|---:|---|
| 2022 | recovered @25 | 22 | 22 | tie |
| 2022 | recovered @50 | 45 | **44** | worse |
| 2022 | recovered @100 | 89 | **84** | worse |
| 2022 | recovered @500 | 193 | **185** | worse |
| 2022 | top-100 dominant precision | 0.7856486013 | **0.7603372834** | worse |
| 2022 | MRR | 0.0224982696 | **0.0256350457** | better |
| 2022 | median top-500 fragmentation | 1.0 | 1.0 | tie |
| 2022 | full-catalogue qualified matches | 236 | **204** | worse |
| 2023 | recovered @25 | 23 | **22** | worse |
| 2023 | recovered @50 | 46 | **44** | worse |
| 2023 | recovered @100 | 89 | **86** | worse |
| 2023 | recovered @500 | 192 | **193** | better |
| 2023 | top-100 dominant precision | 0.7867680237 | **0.8001596970** | better |
| 2023 | MRR | 0.0220239289 | **0.0249383028** | better |
| 2023 | median top-500 fragmentation | 1.0 | 1.0 | tie |
| 2023 | full-catalogue qualified matches | 244 | **212** | worse |

Candidate count changed materially from **2,097 parent candidates to 1,197 cross-year-core candidates**. The frozen prelabel record confirms:

- `hierarchy_changed=true`;
- `memberships_changed=true`;
- `mechanism_active=true`.

Thus this is not a null implementation or inactive-mechanism result. The opposite-year core-distance hierarchy genuinely changed the catalogue.

## Frozen-gate interpretation

The preregistered gate required:

1. recovered@100 strictly higher in at least one year and not lower in the other;
2. recovered@50 not lower in either year;
3. top-100 precision not lower in either year;
4. MRR not lower in either year;
5. median top-500 fragmentation not higher in either year;
6. an active mechanism.

Cross-year-core passed the MRR, fragmentation, and mechanism-activity requirements, and improved 2023 top-100 precision. It failed the central recovery requirements in **both years** and also reduced 2022 precision. In particular:

- @100: `89 -> 84` (2022), `89 -> 86` (2023);
- @50: `45 -> 44` (2022), `46 -> 44` (2023).

Therefore the binding FAIL is unambiguous.

## Scientific interpretation and closure

The frozen experiment supports a narrow diagnostic conclusion: forcing local density to be supported by the opposite observing year can improve very-early ranking quality for some recovered showers, but in this implementation it makes the hierarchy too selective overall, removing or consolidating enough useful structure to reduce fixed-budget recovery and full-catalogue qualified matches.

That interpretation **does not authorize** changing the opposite-year neighbor order, blending ordinary and cross-year core distance, clipping/scaling the cross-year core, altering `k`, changing `min_cluster_size`, modifying mutual reachability, reranking, or relaxing the gate. Those would be outcome-informed rescues of this failed version.

Cross-year-core HDBSCAN v1 is permanently closed as a failed successor. Promoted recurrent-EOM HDBSCAN v1 remains the OrbitTrace methodology parent.

The dormant SonotaCo parent-superiority protocol frozen before this GMN outcome is not activated and must remain scientifically unused for cross-year-core v1.

## Firewall

The binding result records:

- development role: target-excluded GMN 2022+2023 only;
- blind exclusion: `[20.0,55.0]`;
- target information access: false;
- target-region event access: false;
- SonotaCo 2013/2014 access: false;
- AMOS scientific access: false;
- EFN scientific access: false;
- MAARSY scientific access: false;
- DMS scientific access: false;
- post-result parameter search: false.
