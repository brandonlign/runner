# Density-synchronous stratified-core HDBSCAN v1 — binding result

## 🔴 NEGATIVE — permanent GMN development failure

The first technically valid binding endpoint was GitHub Actions run `31861760176` at execution head `7419a1788b8b34b5a491633f6cc979ec3d512428`.

Artifact `9240971435`, digest `sha256:21663ae010be00117fc659d14a74b6360a5f342745a13707e640cb08d464b431`.

Binding result SHA-256: `a9b43a6f470765530f7d1fab22cfc361d90fb4ef8aa9f2ea9511ecc924bdb6e5`.
Binding prelabel SHA-256: `ef7fc381f8f529ae913c1e25b28d51eef0fb6252d7ed5904cd4100ef37a77eb6`.

Exact verdict: `FAIL_DENSITY_SYNC_STRATIFIED_CORE_V1_GMN_DEVELOPMENT`.

The mechanism was active. The direct parent is the exact binding #1263 density-synchronous recurrent-EOM champion (`2,094` candidates). The successor changed the hierarchy as intended and produced `1,706` candidates, a reduction of `388` (`18.53%`).

## Exact frozen head-to-head

### 2022

- recovered@25: `22 -> 21`
- recovered@50: `45 -> 44`
- recovered@100: `89 -> 81`
- recovered@500: `192 -> 190`
- qualified matches: `236 -> 227`
- top-100 dominant precision: `0.7873334042799703 -> 0.762888734878507`
- MRR: `0.022505373166085363 -> 0.022950593135498472`
- median top-500 fragmentation: `1.0 -> 1.0`

### 2023

- recovered@25: `23 -> 21`
- recovered@50: `46 -> 44`
- recovered@100: `90 -> 78`
- recovered@500: `191 -> 185`
- qualified matches: `244 -> 224`
- top-100 dominant precision: `0.7898245986099988 -> 0.7637124161009488`
- MRR: `0.02203028490649908 -> 0.02318450855004525`
- median top-500 fragmentation: `1.0 -> 1.0`

The frozen no-regression gate failed in both years for recovered@50, recovered@100, and top-100 precision. There was no strict recovered@100 improvement. Higher MRR and unchanged fragmentation do not rescue those failures.

## Interpretation

The balanced `5+5` annual core construction is too aggressive for this hierarchy. Requiring each event's core radius to accommodate the fifth neighbor from each year suppresses useful local density structure strongly enough to remove nearly one fifth of the selected candidate families. The loss is not merely a rank reshuffle: recovered@100 falls by `8` in 2022 and `12` in 2023, and top-100 precision drops by roughly `0.0244` and `0.0261` respectively.

This exact mechanism is therefore scientifically closed. The result does **not** authorize an alternate annual `k`, softer max/mean/quantile combination, blend with pooled core distance, partial stratification, score rescue, reranking, or any other result-informed variant of this frozen version.

No SonotaCo validation is authorized because the GMN train gate failed. AMOS remains sealed. ASFN and EFN were not used. Protected solar longitude `[20°,55°]` remained excluded inclusively; OrbitTrace target information/events, MAARSY and DMS were not accessed scientifically.

#1263 remains the current full-GMN development champion, while PR #1265 separately records that its strict @100 gain is not robust under the frozen 10-fold perturbation diagnostic.
