# Affine stream-tube quartet: authoritative pinned preflight result

Runner workflow `30879045015` completed the exact pinned preflight from repository commit `e06867d8c60aaeb8cb1a73d2c5bfdbb63de936ea`. Artifact `8880608665` was preserved with digest `sha256:067526b079961eeb3b0da6bedd1a55bd020d83b715abe796f9cb085e27bcd54a`.

All source, input, and interface checks passed:

- affine candidate SHA-256 `7ec195a34fa286129f01d181b7a8365623a0266d76c153a155d98d220cc833f3`;
- exact baseline/episode source SHA-256 `7718ac5229475f4240305ad9c1e073c49702c771df36612d9be5baa877b46a50`;
- exact passed Mondrian scorer SHA-256 `f1c121e97a660a3820a11814c4325eb3ab33d34a031e83bdfb03b4b392e259b8`.

## Frozen panel

- eligible showers: **181**;
- supported 10° bins: **33**, each supported independently in both 2019 and 2025;
- positive windows: **724**;
- independent negative windows: **1,056**;
- five nonempty complex-disjoint folds.

## Result

Weak-window AUROC:

- affine stream-tube: **0.747215**;
- ordinary anchored quartet: **0.787638**;
- split statistic: **0.773978**;
- density / DBSCAN: **0.759319 / 0.748606**.

Calibration:

- pooled FPR at alpha 0.05 / 0.01: **0.056818 / 0.000000**;
- worst individual 10°-bin FPR at alpha 0.05: **0.156250**.

Affine recall at alpha 0.05 / 0.01:

- k=4: **0.149171 / 0.000000**;
- k=6: **0.237569 / 0.000000**;
- k=8: **0.342541 / 0.000000**;
- k=12: **0.530387 / 0.000000**.

Ordinary anchored-quartet recall at alpha 0.05 was higher at every size:

- k=4: **0.154696**;
- k=6: **0.386740**;
- k=8: **0.480663**;
- k=12: **0.718232**.

Affine fold AUROCs were **0.788715, 0.751681, 0.679442, 0.742560, 0.772271**.

## Frozen-gate outcome

Ten of nineteen gates passed. The formulation failed:

- minimum weak AUROC;
- proximity to the strongest comparator;
- required k=4 gain over the anchored quartet;
- all absolute k=4, k=6, and k=8 recall gates at alpha 0.01;
- k=4, k=6, and k=8 recall gates at alpha 0.05.

Verdict: **`KILL_AFFINE_TUBE_PREFLIGHT`**.

## Interpretation

The local affine-fit hypothesis is not supported. Allowing each four-event neighborhood to fit a solar-longitude trajectory removed genuine compact-coherence information and increased the effective flexibility of accidental background quartets. Calibration remained acceptable, but discrimination and sensitivity worsened materially relative to the simpler anchored quartet.

No ridge, residual definition, neighborhood size, coordinate set, calibration count, seed, fold, threshold, or gate will be changed. No full four-year affine benchmark, confirmation panel, catalogue scan, or GhostStream application is authorized.