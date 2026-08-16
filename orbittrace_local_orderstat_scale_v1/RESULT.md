# OrbitTrace local order-statistic scale calibration v1 — result

## 🔴 NEGATIVE

Binding run: `31933773388`

Artifact: `9260078491`

Artifact digest: `sha256:4a94de98d7648c69a3f2974acf6be575254e050f220b69ab083627b4ab083fce`

Result SHA-256: `9e24684e8a2a310fa94eb7645406a408ec65138120fa875234af5a05e4005366`

Exact frozen interpretation:

`REFUTES_LOCAL_ORDERSTAT_SCALE_CALIBRATION`

### What passed

The analytic local-null transform is correctly calibrated under the predeclared homogeneous 4-D periodic-torus null:

- all `8/8` Bonferroni-screened KS tests passed;
- synthetic mean/median p-values remained approximately `0.5` at both `n=768` and `n=6144` for supports `4,8,16,32`.

The dimensionless inner/outer volume ratio also strongly reduced **marginal distribution drift** under target-excluded GMN thinning at all four supports:

- support 4: KS raw radius `0.4608926` -> local ratio `0.0731717`
- support 8: `0.5136392` -> `0.0827618`
- support 16: `0.5597971` -> `0.1082361`
- support 32: `0.5810383` -> `0.1590504`

Thus the probability coordinate is globally scale-normalized in distribution.

### What failed

It is **not event-identity stable** under thinning. Across the same events in paired ~5.8k/~0.7k nested subsets, local surprise rank changed much more than raw local compactness rank.

Support-specific median Spearman correlations across the four buckets:

- support 4: local surprise `0.1324787` vs raw compactness `0.8530191`
- support 8: `0.1195980` vs `0.8844626`
- support 16: `0.0958221` vs `0.8949820`
- support 32: `0.0273106` vs `0.8938079`

Overall median across supports:

- local surprise `0.1077101`
- raw compactness `0.8891353`

Rank-stability wins: `0/4`.

### Interpretation

The exact inner-vs-outer order-statistic test succeeds as a **distributional normalization** but fails as a stable per-event scientific coordinate. Resampling changes which points occupy the inner and outer order statistics, so the spacing ratio is much noisier than the underlying local-density ordering.

A key zero-label observation is that absolute kNN radii drift strongly with sample size while their **same-event density ordering is remarkably stable**. This does not rescue the closed local-order-statistic method, but it redirects the structural problem: the next justified question is whether a survey-relative/empirical-rank density representation can retain that stable ordering while removing the absolute scale that caused fixed HDBSCAN support failure.

### Closure

The exact `D=4`, supports `{4,8,16,32}`, outer scale `2s`, lower-tail Beta local-order-statistic architecture is closed. Do not rescue it by changing dimension, support scales, outer-neighborhood ratio, Beta tail, combination rule, salt, subset, or gate.

No shower truth, protected target information/events, SonotaCo, ASFN/EFN event rows, AMOS, MAARSY, or DMS were accessed.
