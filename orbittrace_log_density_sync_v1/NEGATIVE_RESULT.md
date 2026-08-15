# Log-density synchronous EOM v1 — binding negative result

This method is permanently closed under its frozen no-rescue rule.

Binding run: `31905143040`

Execution head: `a62ea00f8f6ab8d359bfab44335d865d96eada58`

Artifact: `9252187529`

Artifact digest: `sha256:20d58d555b8779de44b4b3c62063c1aa74a35a7d4ae29dfd1d83bb5907c5892e`

Exact verdict: `FAIL_LOG_DENSITY_SYNCHRONOUS_EOM_V1_GMN_DEVELOPMENT`

## Parent — density-synchronous recurrent-EOM

- candidate count: `2094`
- 2022 recovered@50 / @100: `45 / 89`
- 2022 top-100 precision: `0.7873334042799703`
- 2022 MRR: `0.022505373166085363`
- 2023 recovered@50 / @100: `46 / 90`
- 2023 top-100 precision: `0.7898245986099988`
- 2023 MRR: `0.02203028490649908`
- total recovered@100: `179`

## Successor — pure dlog(lambda) synchronous objective

- candidate count: `3`
- 2022 recovered@25 / @50 / @100 / @500: `1 / 1 / 1 / 1`
- 2022 top-100 precision: `0.26680477425763843`
- 2022 qualified matches: `1`
- 2023 recovered@25 / @50 / @100 / @500: `1 / 1 / 1 / 1`
- 2023 top-100 precision: `0.23536083829754595`
- 2023 qualified matches: `1`
- total recovered@100: `2`
- gain versus parent: `-177`

## Interpretation

The intended multiplicative-density-scale invariance was real and passed the zero-data audit, but using pure `d log(lambda)` as the EOM integration measure is far too aggressive. It strongly favors a tiny number of high relative-density-contrast structures and destroys the broad family recovery that raw-density mass contributes.

This is a useful structural negative: **survey-relative density contrast cannot replace absolute density-mass persistence wholesale.**

Do not rescue this result by changing logarithm base, adding a lambda offset, clipping lambda, blending raw and log stability, applying the transform to a subset of nodes, retuning HDBSCAN, or reranking the failed catalogue.

SonotaCo was never opened for this successor. ASFN, EFN and AMOS were not used. Protected `[20.0,55.0]`, OrbitTrace target information/events, MAARSY and DMS remained inaccessible.
