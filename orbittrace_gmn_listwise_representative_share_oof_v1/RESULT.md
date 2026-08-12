# Binding result — GMN listwise representative-share OOF v1

## Verdict

`FAIL_GMN_LISTWISE_REPRESENTATIVE_SHARE_OOF_V1`

This is the first technically valid and therefore binding scientific outcome for the exact method frozen in `PROTOCOL.md`. The lane is closed exactly as preregistered. No regularization, temperature, intercept, alternate optimizer, ListMLE/Plackett-Luce variant, pairwise hybrid, nonlinear basis, feature/model search, fold-score transform, diversity change, rank fusion, budget-specific reranking, or SonotaCo-informed rescue is permitted under this v1.

## Binding provenance

- protocol freeze commit, before implementation/outcome: `f361da71cdc86291aeae423911a502f489e02333`
- protocol git blob: `1c592a45da7a57e4458993a25f4efec7cb1aa5c7`
- implementation commit: `f7e7d1494329859554f3d595fb0a3698e0d77882`
- implementation git blob: `2546213a3fbb61258a11d73219f2f051eaf5c649`
- binding execution head: `8a85a45d9f36fd056b1deeaee724466a13b06732`
- GitHub Actions run: `31611223377`
- job: `94162754810`
- artifact ID: `9147377170`
- artifact name: `orbittrace-gmn-listwise-representative-share-oof-v1`
- artifact digest: `sha256:c6d07967b993f6d99fb13eadc3090985278f1ed5b82f3208c55e33e7d335b98d`
- binding result JSON SHA-256: `dbbc36651d1e9b1eb48f4ac471c72e81c7c4039b6d35509c9bfce74cb1b6490c`
- full-model-freeze JSON SHA-256: `07c74e6731eb497831c61ae7fce679c93338b804ea30031ef2df16dcf5e25574`
- exact #839 source SHA-256: `dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990`
- exact 34D feature matrix SHA-256: `5d215c5562c0ccce967d81ff0a087ca83b1afda95a269888d2219ef669d198d1`
- exact representative-share target SHA-256: `4433b443030a568f9d5f6ddceab2077e9d78e50497f7ce2473bad5c113f8ab39`
- exact grouped weights SHA-256: `4ee439f0f04c9763a3dcc1527be66681496ea730df369f3c2f1815c9ef4a67f6`
- listwise OOF score SHA-256: `8a676977518d98ac5fffa93109ad9733446fea3ad8ffa0badd338f57a4aa0fc8`
- listwise order SHA-256: `94b1c0b84eff91f420573ff34ea5e485a2b617d22088fea39d165d372330f628`

## Exact controls reproduced before candidate evaluation

### #839 quality/diversity control

- recovered@25 / @50 / @100 / @500 = `22 / 40 / 75 / 159`
- top-100 dominant precision = `0.7645689180574315`
- MRR = `0.019037817654898162`
- qualified matches = `256`
- median first rank = `238`

### #1194 representative-share parent

- recovered@25 / @50 / @100 / @500 = `22 / 43 / 80 / 171`
- top-100 dominant precision = `0.8075287489258385`
- MRR = `0.02016666446026534`
- qualified matches = `256`
- median first rank = `225`

## Frozen listwise candidate

- recovered@25 / @50 / @100 / @500 = **`21 / 41 / 65 / 178`**
- top-100 dominant precision = **`0.7242009331313757`**
- MRR = **`0.02001380153744821`**
- qualified matches = **`256`**
- median first rank = **`251`**
- mean qualified candidates per recovered label = `7.87890625`
- maximum qualified candidates for one label = `260`

Relative to the frozen #1194 parent, the candidate lost 15 recovered showers at rank 100, lost 2 at rank 50, lost 1 at rank 25, reduced top-100 precision by about 0.08333 absolute, and slightly reduced MRR. It recovered 7 additional showers by rank 500, but the preregistered objective prioritizes useful early catalogue ordering and explicitly requires no regression in the frozen secondary metrics. The deep-recovery improvement therefore cannot rescue the result.

## Promotion gates

- recovered@100 > 80: **FAIL** (`65`)
- recovered@50 >= 43: **FAIL** (`41`)
- recovered@25 >= 22: **FAIL** (`21`)
- recovered@500 >= 171: PASS (`178`)
- top-100 precision >= parent: **FAIL** (`0.7242009331313757`)
- MRR >= parent: **FAIL** (`0.02001380153744821`)
- qualified matches == 256: PASS

No full model was frozen: `NOT_FROZEN_GMN_LISTWISE_REPRESENTATIVE_SHARE_FAIL`.

## Technical validity

All five L-BFGS-B fits converged with finite coefficients, loss, gradient and partition values. Iteration counts were `232, 216, 190, 206, 219`. The result is therefore not attributable to an optimizer or workflow failure.

The scientific interpretation is narrow: replacing the successful #1194 pointwise nonlinear ExtraTrees fit with this frozen **linear whole-list softmax cross-entropy** shifts useful signal too far down the ranking. It does not establish that every possible listwise learner is impossible, but the protocol permanently closes this exact listwise representative-share architecture and all preregistered rescue variants.

## Firewall

The binding artifact asserts throughout:

- `scientific_role = GMN_2022_2023_TARGET_EXCLUDED_METHOD_DEVELOPMENT_ONLY`
- `sonotaco_2013_2014_access = false`
- `target_information_access = false`
- `target_region_events_accessed = false`
- `maarsy_scientific_access = false`
- `dms_scientific_access = false`
- `blind_exclusion = [20.0, 55.0]`
- strict same-shower whole-fold grouping = true
- no target, feature, model, hyperparameter, diversity, source-quota, or post-result search occurred.
