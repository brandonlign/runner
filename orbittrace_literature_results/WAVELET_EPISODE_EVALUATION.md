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

| Corpus | Workflow | Artifact | Result SHA-256 |
|---|---:|---:|---|
| SonotaCo 2025 development | `31104654956` | `8969020016` | `526544fc39fd441fd73472c36e8d563b245728b3d33e858f0b1da11aa024070a` |
| SonotaCo 2023 one-shot transfer | `31105278114` | `8969274303` | `450c8db66dd2644a617573c5aadcf4d554c6d4c642e2a0654652dcec3391f964` |

Every 2023 source, freeze, parser, episode-count, fixed4-reproduction, wavelet-parameter, fold, complete-case, and finite-score gate passed.

## Overall discrimination

| Method | 2025 weak AUROC | 2023 weak AUROC |
|---|---:|---:|
| Brown-family wavelet episode core | **0.828506** | **0.831972** |
| fixed4 | 0.813250 | 0.811631 |
| D_N M=4 sparse transfer | 0.759251 | 0.746209 |

The wavelet core exceeded fixed4 by **0.015255 AUROC** in 2025 and **0.020341** in the independent 2023 transfer. The ordering therefore replicated.

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

The methods have different strengths:

- **wavelet:** higher overall AUROC and higher k=6, k=8, and k=12 recall in both years at both reported α levels;
- **fixed4:** higher k=4 recall in both years and tighter α=.05 false-positive control.

False-positive rates at α=.05 were 0.0596 versus 0.0479 in 2025 and 0.0554 versus 0.0507 in 2023. The wavelet core was therefore slightly liberal relative to fixed4 at that operating point, although both remained close to the nominal level.

## Scientific interpretation

The previous statement that fixed4 was the strongest implemented overall sparse-episode method is no longer correct. The frozen wavelet episode adaptation achieved the highest weak-stream AUROC in both available years.

That does **not** make fixed4 useless or remove its methodological contribution. The results instead reveal a sharper division:

- fixed4 is specialised for the extreme four-member regime and maintains better false-positive control;
- the wavelet core is stronger once the stream supplies approximately six or more members;
- neither method is uniformly best.

For OrbitTrace, fixed4 can still be retained as an independently developed sparse four-member recognition method and targeted recovery mechanism. It should not be presented as the top overall benchmark performer. The wavelet result is an additional literature comparator and does not change the historical HDBSCAN discovery path or the observational validation evidence.

## Next analysis

A checksum-pinned paired cluster-bootstrap analysis will use the preserved 2025 and 2023 positive and negative records to quantify uncertainty in:

1. wavelet-minus-fixed4 AUROC;
2. k-specific recall differences;
3. false-positive-rate differences.

That analysis changes no method, score, episode, threshold, or result.
