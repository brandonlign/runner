# OrbitTrace final methodology evaluation

## Historical separation

OrbitTrace was historically discovered by the blind HDBSCAN workflow. The observational validation program is separate. fixed4, the wavelet episode comparator, and the hybrid were developed afterward and must not be described as the original discovery procedure.

fixed4 remains the novel methodological component: a frozen coverage-normalized anchored four-clique detector developed without OrbitTrace access. The Brown-family wavelet episode method is literature-inspired. The Tippett hybrid is a later post-comparison ensemble.

## Sparse-episode results

All episode methods use the same 128-event windows, calibration negatives, held-out negatives, folds, member counts, seeds, and metrics.

### Overall weak-stream AUROC

| Method | SonotaCo 2025 | SonotaCo 2023 one-shot | SonotaCo 2022 prospective |
|---|---:|---:|---:|
| fixed4 | 0.813250 | 0.811631 | 0.791405 |
| Brown-family 3D wavelet episode core | **0.828506** | **0.831972** | **0.820936** |
| fixed4-wavelet Tippett hybrid | 0.835878* | — | 0.815525 |

`*` Retrospective development evidence; the hybrid decision was determined only from prospective SonotaCo 2022.

The wavelet episode adaptation is the strongest overall discriminator tested. It exceeded fixed4 in development, one-shot transfer, and a genuinely prospective third-year validation. fixed4 can no longer be claimed to outperform every implemented comparator.

### Member-count tradeoff

The ordering differs in the hardest ultra-sparse regime. At alpha .05, fixed4 retained the highest four-member recall in all three evaluated years. On prospective SonotaCo 2022:

| Method | k=4 | k=6 | k=8 | k=12 |
|---|---:|---:|---:|---:|
| fixed4 | **0.171053** | 0.401316 | 0.585526 | 0.815789 |
| wavelet | 0.092105 | 0.421053 | 0.703947 | 0.921053 |
| hybrid | 0.131579 | **0.447368** | **0.723684** | **0.947368** |

fixed4 therefore retains a reproducible ultra-sparse niche. The wavelet is stronger once the stream contains enough members for a smooth radiant-speed concentration to emerge.

## Wavelet classification

The successful wavelet comparator is a separately labelled sparse-episode adaptation using:

- Sun-centered ecliptic radiant longitude and latitude plus geocentric speed;
- 4° angular and 10% fractional-speed probes;
- the three-dimensional Mexican-hat kernel `(3-r^2) exp(-r^2/2)`;
- truncation at four probe radii;
- leave-one-out coefficients at observed-event locations;
- maximum coefficient as the episode score.

It is not a faithful reproduction of the full Brown et al. CMOR catalogue survey. The full survey remains formally deferred because the seven-year optical stack failed the frozen global-support breadth gate. No full-survey coefficient or detection endpoint was computed.

## Hybrid decision

The hybrid uses the frozen bin-calibrated Tippett union of fixed4 and wavelet empirical p-values. No weight or alternative combiner was tested.

On prospective SonotaCo 2022:

- wavelet AUROC: 0.820936;
- hybrid AUROC: 0.815525;
- fixed4 AUROC: 0.791405;
- balanced alpha-.05 recall: 0.534539, 0.562500, and 0.493421, respectively.

The hybrid failed the promotion gate because it did not exceed the wavelet’s AUROC. Its frozen decision is **`RETAIN_AS_OPTIONAL_ENSEMBLE`** because it produced the strongest balanced recall and highest k=6/8/12 recall.

## Catalogue-track context

The published HDBSCAN configuration and full uncertainty-aware Sugar reconstruction remain strong for large catalogue populations and weak in the smallest annual strata. Those results establish task complementarity rather than a universal head-to-head victory.

The full CMOR-style survey was handled with frozen feasibility gates rather than a weakened imitation. The successful episode wavelet result does not change that catalogue-level defer decision.

## Revised independent judgment

**Retain fixed4 as a real but narrower methodological contribution.**

The prior judgment—fixed4 as the best overall sparse detector tested—is no longer supported. The correct scientific interpretation is:

1. **Wavelet episode adaptation:** primary overall sparse-episode discriminator by reproducible AUROC across three years.
2. **fixed4:** novel topology-based ultra-sparse detector with higher four-member recall, independent targeted OrbitTrace recovery, and complementary value.
3. **Hybrid:** optional high-recall ensemble, not the primary method.

This is not a reason to remove fixed4. Its value is now clearer: it captures a regime the smoother wavelet method misses. The paper should frame the methodology as a **multi-regime sparse-stream analysis**, not as one new detector beating all established methods.

The original fixed4 weaknesses also remain: the frozen k=4 alpha-.01 replication failure and calibration-seed robustness failure were not erased by later comparisons. The fixed4-specific conclusion is therefore:

> **Promising strong transfer and useful ultra-sparse complement, but not fully robustly replicated under the complete preregistered standard.**

## OrbitTrace-specific application

The frozen targeted fixed4 application remains valid evidence that the novel detector recognizes the OrbitTrace structure. It is not a blind catalogue rediscovery and not the original discovery method. A targeted wavelet or hybrid application, if later performed, must retain the same boundary.

## Allowed manuscript claim

> A frozen Brown-family three-dimensional wavelet core achieved the highest overall weak-stream discrimination on the common sparse-episode benchmark, exceeding the novel fixed4 detector in SonotaCo 2025, a one-shot SonotaCo 2023 transfer, and a prospectively frozen SonotaCo 2022 validation. fixed4 nevertheless retained consistently higher four-member recall at alpha .05 and independently recovered the OrbitTrace structure under a targeted protocol, supporting it as a complementary topology-based detector for the hardest ultra-sparse regime. A preregistered Tippett hybrid did not exceed the wavelet’s prospective AUROC and was retained only as an optional high-recall ensemble. None of these later methods was the historical OrbitTrace discovery procedure.

## Prohibited claims

- “OrbitTrace was discovered by fixed4, wavelet, or the hybrid.”
- “fixed4 is the best overall sparse-stream method tested.”
- “Wavelet is uniformly superior at every member count and operating point.”
- “The full CMOR catalogue survey was reproduced or beaten.”
- “The hybrid is the primary overall discriminator.”
- “The targeted fixed4 recovery is a blind catalogue rediscovery.”
- “fixed4 fully passed its complete independent-validation standard.”
