# Balanced Logit OOF v1 — binding GMN development result

Verdict: `FAIL_GMN_BALANCED_LOGIT_OOF_V1`

This is the first technically valid outcome under frozen protocol `5b2cf9aae07a2a84da03233a1e3a7105cc1eb5d0` and frozen implementation `6331a0fbe9731cf1f7a02cc199a08e726ab0ac04`.

- binding workflow run: `31604162091`
- binding job: `94138706324`
- execution head: `eb4daad59f742c2b2e202382a4f41f6d1a97428d`
- artifact: `9144375753`
- artifact digest: `sha256:990f126052dd15bca2d76ca80dcd4a9382dc749129f4d2c73e84009c867439e3`

## Exact Fisher parent reproduced

- recovered@100: **69**
- recovered@50: **41**
- recovered@25: **24**
- top-100 dominant precision: **0.7677499561973543**
- MRR: **0.05055989766869565**
- qualified matches: **95**

## Binding candidate

- recovered@100: **65**
- recovered@50: **40**
- recovered@25: **22**
- recovered@500: **95**
- top-100 dominant precision: **0.7424686983895634**
- MRR: **0.04512278674164271**
- qualified matches: **95**
- median first rank: **61.0**
- raw logit median absolute score: **1.5542673476732274**
- unit factor: **0.2869726297900627**
- raw score SHA256: `17fd080f4013f01056dc0945fe69ca40025a99a4fe2ef4dc2a172182f2426012`
- scaled score SHA256: `038332691fbcaf71f6264cd7a8ecd84eda07836f70720546a1aff118c379df2b`

Fold optimization converged in 197–342 LBFGS iterations, below the frozen 10,000-iteration ceiling. This is therefore a scientific outcome, not an engineering no-result.

## Frozen gates

- recovered@100 strictly above Fisher: **FAIL**
- recovered@50 not below Fisher: **FAIL**
- top-100 precision not below Fisher: **FAIL**
- MRR not below Fisher: **FAIL**
- qualified count identical: **PASS**

The architecture is permanently closed. No C, ridge/penalty, solver, class-weight, group-weight, calibration, feature transform/subset/interaction, nonlinear basis, score blend, diversity/fusion change, threshold, rank-window, family deletion, or post-result rescue is authorized.

## Firewall and immutable inputs

- feature matrix SHA256: `fea3b063772c75b675e37a227b53a4aa3c5b86fdcbfcef1487b1e1448689cdf5`
- hard order SHA256: `2dcaaffaefca68e877fea82ff46a68bbd4c7960dedfdd00a114311d41605b65e`
- parent margin SHA256: `f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`
- Fisher scaled SHA256: `9957292fbe41efa407b9bc5b1f4160cdc0899632135a10b56d2f91f04d54c46e`
- blind exclusion: `[20.0, 55.0]`
- SonotaCo 2013/2014 access: false
- target information access: false
- target-region event access: false
- MAARSY scientific access: false
- DMS scientific access: false
