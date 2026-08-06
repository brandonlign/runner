# SonotaCo 2023 Valsecchi D_N one-shot transfer

The SonotaCo-2025-frozen D_N comparators transferred successfully to the independent SonotaCo 2023 replacement panel.

- workflow run: `31074254968`;
- artifact: `8956855273`;
- artifact digest: `sha256:fb9f5e37c5efed148c21dd49f0f44be00385f27182043dac3317ec5a520617b9`;
- result SHA-256: `112e09fba336e74d34b3dad03d9fba338ac3c449acca3e116c65c015f10a2c4d`;
- verdict: `PASS_SONOTACO_2023_DN_ONE_SHOT_TRANSFER`;
- all 12 frozen-source, parser, episode-count, fixed4-reproduction, D_N-equation, fold, and finite-score gates passed.

## Exact results

| Method | Classification | Weak AUROC | FPR .05 | FPR .01 |
|---|---|---:|---:|---:|
| fixed-4° | frozen candidate | 0.811631 | 0.050663 | 0.006629 |
| D_N, M=6 | published distance and single-neighbour linkage evaluated at six members | 0.714395 | 0.040720 | 0.007102 |
| D_N, M=4 | predeclared sparse benchmark transfer | 0.746209 | 0.047822 | 0.008523 |

Recall at alpha 0.05 for k=4/6/8/12:

- fixed-4°: 0.189024 / 0.432927 / 0.713415 / 0.896341;
- D_N, M=6: 0.091463 / 0.317073 / 0.676829 / 0.908537;
- D_N, M=4: 0.140244 / 0.378049 / 0.646341 / 0.853659.

Recall at alpha 0.01 for k=4/6/8/12:

- fixed-4°: 0.018293 / 0.262195 / 0.463415 / 0.640244;
- D_N, M=6: 0.012195 / 0.170732 / 0.323171 / 0.689024;
- D_N, M=4: 0.060976 / 0.225610 / 0.371951 / 0.634146.

## Replication judgment

The independent result closely reproduces the 2025 ordering:

- fixed4: 0.813250 → 0.811631;
- D_N, M=6: 0.731316 → 0.714395;
- D_N, M=4: 0.759251 → 0.746209.

The sparse D_N transfer remains the strongest classical sparse comparator, but fixed4 retains a reproducible AUROC advantage of approximately 0.054 in 2025 and 0.065 in 2023. D_N, M=6 again slightly exceeds fixed4 at a selected high-k operating point—k=12 recall at alpha 0.05 in 2023—so no claim of uniform superiority is justified.

## Transparent implementation repairs

The first execution computed all episode scores but failed because the inherited AUROC helper requires concrete lists rather than generators. After that compatibility repair, a bookkeeping assertion iterated fold-dictionary keys, causing integer key zero to evaluate false even though every fold contained positive episodes. The observed positive-episode counts were 32, 32, 192, 192, and 208. The accepted workflow reconstructs the immutable original runner and applies exactly three checksum-pinned implementation-only replacements before data access. No equation, weight, target membership, episode, seed, calibration panel, score, or metric changed; the metrics from the failed-gate run and successful run are identical.
