# Recurrent-EOM CV survival rank v1 — SonotaCo result

Binding workflow run: `31995822633`.

Artifact: `9276796864`.

Artifact digest: `sha256:575ce5f99fa6cd80babf3675559971b3ada3d2ffcabe1c45e2470d8eb17a6d74`.

Pretruth SHA-256: `a8862cb77c9c013667ef506d3a1cd3c40fd321e3854c43b979881337daa4fb25`.

Result SHA-256: `e6abd67cb48e7bd60993e3e071561495ea4236e3d287eba48529ba6e5b93d30c`.

Exact verdict: **`FAIL_RECURRENT_EOM_CV_SURVIVAL_RANK_V1_SONOTACO_DEVELOPMENT`**.

All ten deletion-fold catalogues for both routes and both complete successor orders were frozen before truth. Full parent memberships were unchanged. The CV-survival mechanism changed both route orders.

Matched exposed SonotaCo outcomes:

- Sugar 2013: `0.3752906816276458 / 23 -> 0.3752906816276458 / 23` — tie;
- Sugar 2014: `0.43773122295664196 / 24 -> 0.4250039502293692 / 23` — regression;
- HDBSCAN 2013: `0.1914598192215768 / 11 -> 0.1914598192215768 / 11` — tie;
- HDBSCAN 2014: `0.1685878550176112 / 9 -> 0.1685878550176112 / 9` — tie.

The frozen all-panel no-regression gate therefore fails. The exact CV-survival ranker is closed; its strong 10/10 GMN label-free stability result remains useful as a robustness diagnostic but does not establish a better primary shower ranking.

No exponent, fold weighting, blend, route-specific exception, threshold, or second SonotaCo ranking attempt is authorized from this result. Recurrent-EOM remains the stronger catalogue-scale method.