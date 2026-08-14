# Recurrent-EOM HDBSCAN v1 — binding GMN 2020/2021 archival transfer result

**Scientific classification: NEGATIVE retrospective robustness result.**

Binding run: `31830129499`  
Artifact: `9230386230`  
Artifact digest: `sha256:3573d2bf56e85f57c0ffbdf01c5bae91921ed7e7272d8f3cc4787b32cb292d0f`  
Execution commit: `07f7cd0caecb6e31aa446dd7f9a0050ab5e0977d`  
Result SHA-256: `c500bf74b5fbf516860c9aa19d1f13cfc636276c3ff5720663d3917bad59bf66`  
Frozen transfer-runner SHA-256: `92a19b4b7881519bd9b883e1a84d31ee3c5e81c6fd5640824db315ec24e2942a`  
Frozen transfer-runner git blob: `0a34d0cc5cf1d374158201d0c559a870cfb488de`

Source-only authorization run `31830042638`, artifact `9230300205`, digest `sha256:7fc9a2bb9dc42f517b2d5049c0fa137861ec73fac58d33dbc4b90f537ab59db5`, proved before catalogue access that the transfer runner was a mechanical calendar/provenance transport of the binding 2022/2023 implementation with no scientific-method or gate change.

## Role boundary

GMN 2020/2021 was already historically exposed in earlier OrbitTrace work. This result is therefore a **target-excluded retrospective archival temporal transfer only**, not pristine validation and not an authorization gate for target access.

## Frozen outcome

Accessible events:

- 2020: 116,464
- 2021: 198,617
- pooled: 315,081

Vanilla HDBSCAN emitted 918 candidates; recurrent-EOM emitted 903. The recurrent mechanism was active.

### 2020

| Metric | Vanilla HDBSCAN | Recurrent-EOM | Direction |
|---|---:|---:|---|
| recovered @25 | 21 | 21 | equal |
| recovered @50 | 43 | 43 | equal |
| recovered @100 | 76 | 76 | equal |
| recovered @500 | 145 | 144 | lower |
| top-100 dominant precision | 0.6830540402 | 0.6785455285 | **lower by 0.0045085** |
| MRR | 0.0307953401 | 0.0311820211 | higher |
| median top-500 fragmentation | 1.0 | 1.0 | equal |
| qualified matches | 161 | 157 | lower |

Frozen annual gate failure: `top100_precision_not_lower=false`.

### 2021

| Metric | Vanilla HDBSCAN | Recurrent-EOM | Direction |
|---|---:|---:|---|
| recovered @25 | 20 | **22** | higher |
| recovered @50 | 43 | **44** | higher |
| recovered @100 | 77 | **78** | higher |
| recovered @500 | 161 | 158 | lower |
| top-100 dominant precision | 0.6945394546 | 0.6825274414 | **lower by 0.0120120** |
| MRR | 0.0278370492 | 0.0279765203 | higher |
| median top-500 fragmentation | 1.0 | 1.0 | equal |
| qualified matches | 181 | 180 | lower |

Frozen annual gate failure: `top100_precision_not_lower=false`.

The cross-year strict recovered@100 condition passed because 2021 improved from 77 to 78, and the mechanism was active, but the preregistered purity no-regression gate failed in **both** years.

Binding verdict:

`FAIL_RECURRENT_EOM_HDBSCAN_V1_GMN_2020_2021_RETROSPECTIVE_TRANSFER`

## Interpretation

This result shows that recurrent-EOM's benefit is **not temporally universal**: on this older exposed GMN pair it improves or preserves the early recovery/MRR endpoints while causing a small but binding top-100 purity regression.

No threshold, annual normalization, ranking tie-break, min-cluster size, min-samples setting, feature, or recurrent objective may be changed in response. The 2020/2021 lane is closed for recurrent-EOM v1.

This retrospective failure does not rewrite the separate binding facts that recurrent-EOM v1 passed the target-excluded GMN 2022/2023 development protocol and beat exact v31 on all four frozen exposed SonotaCo 2013/2014 panels. It does, however, narrow the claim: recurrent-EOM v1 is a strong promoted development method with demonstrated cross-survey exposed-development superiority, **not a uniformly dominant HDBSCAN replacement across all historical GMN epochs**.

## Firewall

- `target_information_access=false`
- `target_region_events_accessed=false`
- `sonotaco_2013_2014_access=false` in this transfer
- `maarsy_scientific_access=false`
- `dms_scientific_access=false`
- protected `[20°,55°]` remained excluded
- `post_result_parameter_search=false`
