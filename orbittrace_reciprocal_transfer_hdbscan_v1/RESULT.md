# Reciprocal-transfer HDBSCAN v1 — binding GMN development result

## 🔴 NEGATIVE scientific result

Reciprocal-transfer HDBSCAN v1 **failed** its frozen target-excluded GMN 2022+2023 promotion gate against promoted recurrent-EOM HDBSCAN v1.

This is the first technically valid scientific endpoint for the frozen reciprocal-transfer method and is therefore binding.

### Binding provenance

- workflow run: `31849645782`
- artifact: `9237240523`
- artifact digest: `sha256:61dbc835c77d2a6172d30e152a03c90adecfaa5bf021be222904a1d937c49432`
- execution commit: `9fe25fd0640eecd45cd9b337fb51a45bc1c96d13`
- frozen result SHA-256: `901c6f7af6d16fcbbdee8b8afaf424d52a16fc901661fc23ce7d47f2feb70469`
- frozen prelabel SHA-256: `de07d5cbc29abd3862710a0915bc8f04c774ac5bb8e9531af15c8bd1d3b202da`
- verdict: `FAIL_RECIPROCAL_TRANSFER_HDBSCAN_V1_GMN_DEVELOPMENT`

Both zero-data prerequisites were satisfied before execution:

- synthetic audit run `31849167489`, artifact `9236929569`, result SHA-256 `8c39cb44258df6b8fbc3160dd2c2d2d98bc58de6910bda017cf6f726182cbea1`;
- source/firewall audit run `31849390666`, artifact `9237000627`, result SHA-256 `930659eabef994d6977b5b38a92efab5b36ade64f22fa23e4d399376bb1aeeed`.

The binding workflow reproduced the promoted recurrent-EOM parent metrics exactly before accepting any comparison.

## Exact outcome versus promoted recurrent-EOM

| Year | Metric | recurrent-EOM parent | reciprocal-transfer | Direction |
|---|---|---:|---:|---|
| 2022 | recovered @25 | 22 | **24** | better |
| 2022 | recovered @50 | 45 | **47** | better |
| 2022 | recovered @100 | 89 | **84** | worse |
| 2022 | recovered @500 | 193 | **85** | worse |
| 2022 | top-100 dominant precision | 0.7856486013 | **0.7465163318** | worse |
| 2022 | MRR | 0.0224982696 | **0.0581657549** | better |
| 2022 | median top-500 fragmentation | 1.0 | 1.0 | tie |
| 2022 | full-catalogue qualified matches | 236 | **85** | worse |
| 2023 | recovered @25 | 23 | **24** | better |
| 2023 | recovered @50 | 46 | **49** | better |
| 2023 | recovered @100 | 89 | **87** | worse |
| 2023 | recovered @500 | 192 | **88** | worse |
| 2023 | top-100 dominant precision | 0.7867680237 | **0.7151039872** | worse |
| 2023 | MRR | 0.0220239289 | **0.0568746868** | better |
| 2023 | median top-500 fragmentation | 1.0 | 1.0 | tie |
| 2023 | full-catalogue qualified matches | 244 | **88** | worse |

The two independently fitted annual HDBSCAN models contained:

- 954 native 2022 clusters;
- 1,253 native 2023 clusters.

Strict-majority bidirectional transport retained only **103 reciprocal families**, versus **2,097** candidates in promoted recurrent-EOM. `mechanism_active=true` and the candidate catalogue is plainly non-identical to the parent.

## Frozen-gate interpretation

The preregistered gate required:

1. recovered@100 strictly higher in at least one year and not lower in the other;
2. recovered@50 not lower in either year;
3. top-100 dominant precision not lower in either year;
4. MRR not lower in either year;
5. median top-500 fragmentation not higher in either year;
6. an active non-identical catalogue.

Reciprocal-transfer passed:

- recovered@50 in both years;
- MRR in both years;
- fragmentation in both years;
- mechanism activity.

It failed:

- recovered@100 in both years (`89 -> 84`, `89 -> 87`);
- top-100 dominant precision in both years (`0.78565 -> 0.74652`, `0.78677 -> 0.71510`);
- therefore the required strict @100 improvement is absent.

The FAIL is binding and unambiguous.

## Scientific interpretation and closure

The exact experiment supports one narrow diagnostic conclusion: **strict reciprocal cross-year transport concentrates known showers very effectively near the very top of the catalogue, but is too selective to preserve broader recovery.**

Evidence for the top-ranking concentration is consistent in both years:

- @25 improves from 22/23 to 24/24;
- @50 improves from 45/46 to 47/49;
- MRR rises from ~0.0225/~0.0220 to ~0.0582/~0.0569.

At the same time, only 103 reciprocal families survive, and @100 recovery drops to 84/87. Thus this version behaves more like a high-confidence recurrent-core catalogue than a replacement for the broader recurrent-EOM discovery catalogue.

This interpretation **does not authorize** relaxing strict majority, adding a prediction-probability threshold, matching orphan annual clusters, using centroid/radius fallback, changing HDBSCAN parameters, switching EOM/leaf, blending reciprocal-transfer with recurrent-EOM ranks, or otherwise rescuing v1 after seeing the result.

Reciprocal-transfer HDBSCAN v1 is permanently closed as a failed successor. Promoted recurrent-EOM HDBSCAN v1 remains the OrbitTrace methodology parent.

The dormant SonotaCo recurrent-parent benchmark preregistered before this outcome must remain scientifically unused for reciprocal-transfer v1.

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
