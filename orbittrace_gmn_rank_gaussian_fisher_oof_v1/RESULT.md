# Rank-Gaussian Fisher OOF v1 — binding GMN development result

Verdict: `FAIL_GMN_RANK_GAUSSIAN_FISHER_OOF`

This is the first technically valid outcome under the frozen protocol at `100b65bc0e78ac70fccd67166ce453b71ec5cd85` and frozen implementation at `7cb868b71dd3c34f390f471a82ea684c5b2f4ac5`.

Binding workflow run: `31602974935`

Binding artifact: `9143898156`

Binding artifact digest: `sha256:73383c51978118f7b80f58d7dd0aae7b185fe2c65354e0f3ce5696933d728c77`

Execution workflow commit: `89ac5e124778d129c895cf6480a53271eae845b3`

## Frozen candidate metrics

- recovered@100: **65**
- recovered@50: **41**
- recovered@25: **23**
- recovered@500: **95**
- top-100 dominant precision: **0.7366955845828959**
- MRR: **0.05054293569882356**
- qualified matches: **95**
- median first rank: **59.0**

## Fisher parent reproduced in the same binding run

- recovered@100: **69**
- recovered@50: **41**
- recovered@25: **24**
- recovered@500: **95**
- top-100 dominant precision: **0.7677499561973543**
- MRR: **0.05055989766869565**
- qualified matches: **95**
- median first rank: **63.0**

## Frozen pass gates

- recovered@100 strictly above Fisher parent: **FAIL**
- recovered@50 not below Fisher parent: **PASS**
- top-100 precision not below Fisher parent: **FAIL**
- MRR not below Fisher parent: **FAIL**
- qualified count identical: **PASS**

The method is therefore terminated. No transform variant, quantile clipping, plotting-position change, raw/rank blend, covariance estimator/weight change, feature change, diversity change, threshold change, regularization change, family deletion, or post-result rescue is authorized.

## Preserved identities

- feature matrix SHA256: `fea3b063772c75b675e37a227b53a4aa3c5b86fdcbfcef1487b1e1448689cdf5`
- hard order SHA256: `2dcaaffaefca68e877fea82ff46a68bbd4c7960dedfdd00a114311d41605b65e`
- parent margin SHA256: `f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`
- Fisher scaled SHA256: `9957292fbe41efa407b9bc5b1f4160cdc0899632135a10b56d2f91f04d54c46e`
- rank-Gaussian raw SHA256: `c1a05022190a07b4bf9f46b66ae749e203cf9d18ec7abf4c9964a1cef7e95ef8`
- rank-Gaussian scaled SHA256: `5ff85f9db61736e70b0b8221c354ee3fddd2150caacfca954bb6eeae335a09c7`

## Firewall

The binding result records protected solar-longitude exclusion `[20.0, 55.0]`, SonotaCo 2013/2014 access `false`, OrbitTrace target-information access `false`, target-region event access `false`, MAARSY scientific access `false`, and DMS scientific access `false`.

Technical runs `31602379105`, `31602654881`, and `31602805169` ended before producing `GMN_RANK_GAUSSIAN_FISHER_OOF_RESULT.json`; they are preserved as non-scientific infrastructure failures and are not alternate outcomes.