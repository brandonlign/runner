# Binding result — FAIL

Protocol frozen before outcome at `e04549df9a7dbc52dfcc1db306524b8a19454a0a`.

Exact v31 offline parent reproduced: @25 23, @50 41, @100 66, precision 0.7229521515453452, MRR 0.050244164168646674, qualified 95.

Frozen ExtraTrees OOF + inherited diversity + equal hard-rank fusion:
- @25 = 22
- @50 = 41
- @100 = 66
- top100 precision = 0.7433527462484217
- MRR = 0.047995893633696975
- qualified = 95

Classifier-only diagnostic order: @25 21, @50 42, @100 67, precision 0.7063696781469325, MRR 0.04900977847114484; it was predeclared non-promotable.

Hashes: OOF probability `c6cab9402b2eead31b6dd948d872694b60c2276f5da8ffe7527e4be4a3e71747`; local order `43e2cd316607249f7266a737c18e3d3d874ea9653c700b89b9d34773bbc042df`; fused order `5069c3219bcfc757ac375dfb376a9cf63d34b719201c6061481a29a2088716d9`; grouped weights `078e17fe98e15a67869d74ba17bad8c59c52ef0bdab71fa7606d1940c4ea3abb`; target `f078a94f6d9187a987529f2b04bc65870202aff144d15e2b155c37c94c1bebca`.

Verdict: `FAIL_GMN_V31_INTRINSIC_EXTRATREES_TRANSFER_V1`. No full model freezes and no SonotaCo portability test is authorized. Do not rescue with classifier-only promotion, tree-capacity changes, class weighting/resampling/calibration, target/feature changes, or fusion/diversity changes.