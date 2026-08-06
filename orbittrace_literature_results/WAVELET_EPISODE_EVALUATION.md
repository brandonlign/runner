# Brown-family sparse-episode wavelet evaluation

## Result

The separately labelled Brown-family three-dimensional Mexican-hat wavelet core transferred successfully from SonotaCo 2025 to the frozen SonotaCo 2023 episode benchmark without changing its angular scale, speed scale, kernel, truncation, test locations, self-contribution rule, episode score, calibration panels, seeds, or metrics.

This is an episode adaptation of the published wavelet family. It is not a reproduction of the full CMOR catalogue survey, whose global optical transfer remains formally deferred by the separate input-support audit.

## Frozen method

- coordinates: Sun-centred geocentric ecliptic radiant longitude and latitude plus geocentric speed;
- angular probe: **4°**;
- speed probe: **10%** of local geocentric speed;
- kernel: **`(3-r²) exp(-r²/2)`**;
- truncation: **4 probe radii**;
- test locations: each observed event;
- self-contribution: excluded;
- episode score: maximum leave-one-out coefficient;
- no scale search or post-result tuning.

## Preserved executions

| Analysis | Workflow | Artifact | Result SHA-256 |
|---|---:|---:|---|
| SonotaCo 2025 development | `31104654956` | `8969020016` | `526544fc39fd441fd73472c36e8d563b245728b3d33e858f0b1da11aa024070a` |
| SonotaCo 2023 one-shot transfer | `31105278114` | `8969274303` | `450c8db66dd2644a617573c5aadcf4d554c6d4c642e2a0654652dcec3391f964` |
| Paired cluster-bootstrap inference | `31106813236` | `8969900492` | `0881b5c449a80867b46341a4c681440b911ee6033dd857cc49b74f3561ff08e2` |

Every source, freeze, parser, episode-count, fixed4-reproduction, wavelet-parameter, fold, complete-case, record-hash, and finite-output gate passed.

## Overall discrimination

| Method | 2025 weak AUROC | 2023 weak AUROC |
|---|---:|---:|
| Brown-family wavelet episode core | **0.828506** | **0.831972** |
| fixed4 | 0.813250 | 0.811631 |
| D_N M=4 sparse transfer | 0.759251 | 0.746209 |

The wavelet core exceeded fixed4 by **0.015255 AUROC** in 2025 and **0.020341** in the independent 2023 transfer. The point-estimate ordering therefore replicated.

## Paired uncertainty analysis

The preserved records were evaluated with **20,000 paired cluster-bootstrap replicates**. Positive episodes were resampled by shower-complex unit, negatives by Mondrian bin, and identical bootstrap multiplicities were applied to both methods.

| Corpus | Wavelet − fixed4 AUROC | 95% cluster-bootstrap CI | P(difference > 0) |
|---|---:|---:|---:|
| 2025 | +0.015255 | [−0.019895, +0.051030] | 0.8061 |
| 2023 | +0.020341 | [−0.007006, +0.048011] | 0.9269 |
| Equal-weight combined | +0.017798 | [−0.004337, +0.040646] | 0.9399 |

The direction is consistent across both years, but every reported 95% interval includes zero. The frozen classification is therefore:

**`CONSISTENT_BUT_UNCERTAIN_WAVELET_AUC_ADVANTAGE`**

This supports saying that the wavelet adaptation produced the higher overall point estimate in both years. It does not support calling the difference statistically decisive.

## Operating-point trade-off

### Recall at α = 0.05

| Corpus and method | k=4 | k=6 | k=8 | k=12 |
|---|---:|---:|---:|---:|
| 2025 wavelet | 0.081 | 0.596 | 0.831 | 0.949 |
| 2025 fixed4 | 0.154 | 0.522 | 0.691 | 0.934 |
| 2023 wavelet | 0.134 | 0.543 | 0.799 | 0.921 |
| 2023 fixed4 | 0.189 | 0.433 | 0.713 | 0.896 |

### Recall at α = 0.01

| Corpus and method | k=4 | k=6 | k=8 | k=12 |
|---|---:|---:|---:|---:|
| 2025 wavelet | 0.007 | 0.265 | 0.632 | 0.912 |
| 2025 fixed4 | 0.059 | 0.184 | 0.294 | 0.654 |
| 2023 wavelet | 0.012 | 0.287 | 0.604 | 0.872 |
| 2023 fixed4 | 0.018 | 0.262 | 0.463 | 0.640 |

The paired bootstrap confirms a genuine task split:

- at α=.05, wavelet-minus-fixed4 k=8 recall was +0.1397 in 2025 with CI [+0.0278, +0.2432] and +0.0854 in 2023 with CI [+0.0125, +0.1585];
- at α=.01, the wavelet k=8 and k=12 advantages excluded zero in both years;
- fixed4 retained higher k=4 recall, including a 2025 α=.01 difference of −0.0515 with CI [−0.0938, −0.0135].

False-positive rates at α=.05 were 0.0596 versus 0.0479 in 2025 and 0.0554 versus 0.0507 in 2023. The paired false-positive differences were not decisive, but their direction generally favoured fixed4.

## Scientific interpretation

The previous statement that fixed4 was the strongest implemented overall sparse-episode method is no longer correct. The frozen wavelet adaptation has the highest overall point-estimate AUROC in both available years, although its margin over fixed4 is not statistically decisive under cluster resampling.

That does **not** make fixed4 useless or remove its methodological contribution. The results establish a sharper division:

- fixed4 is specialised for the extreme four-member regime and generally maintains tighter false-positive control;
- the wavelet core is stronger for moderate sparse streams, especially k=8 and k=12 under strict false-positive thresholds;
- neither method is uniformly best.

For OrbitTrace, fixed4 remains an independently developed extreme-sparse recognition method and targeted recovery mechanism. It should not be presented as the top overall benchmark performer. The wavelet result is an additional literature comparator and does not change the historical HDBSCAN discovery path or the observational validation evidence.

## Claim boundary

Allowed:

> The frozen Brown-family wavelet episode adaptation produced a reproducibly higher overall AUROC point estimate than fixed4 across development and one-shot transfer, while fixed4 retained the four-member advantage and generally tighter false-positive control. Paired cluster-bootstrap uncertainty did not establish a statistically decisive overall difference.

Not allowed:

- statistically decisive wavelet superiority;
- uniform wavelet dominance;
- the claim that fixed4 is invalid or useless;
- the claim that fixed4 is the strongest overall episode method;
- the claim that the full CMOR catalogue survey was reproduced or beaten.
