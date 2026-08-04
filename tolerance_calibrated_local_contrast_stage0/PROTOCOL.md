# Tolerance-calibrated local-contrast recurrence: frozen Stage-0 protocol

Status: frozen before any new calibration maximum, null endpoint, injection endpoint, or continuation decision is computed.

## Scientific question

Can the real recurrent-power gain of local-contrast recurrence be retained while replacing its conditionally unstable nearest-rank threshold with a distribution-free one-sided tolerance bound for each predeclared null family?

The detector score is unchanged. Only the calibration rule and Monte Carlo resolution change.

## Prior authoritative boundary

The independently seeded full Stage-0 in PR #82 used exact candidate SHA-256 `b7589d8d140a37596f19d4993be1e2fdd99a18b8eaa087a02e3c4ce585000071`, seed `20260804`, 100 calibration catalogs, 100 fresh catalogs per null family, and 100 injections per condition.

It retained genuine power:

- weak recurrent recovery 0.545 versus strongest comparator 0.470;
- recurrence-margin gain +0.075;
- strong recovery difference +0.005;
- zero weak one-year-artifact recovery.

But shared-structure FWER was 0.220 against the frozen 0.150 ceiling. That formulation remains killed. Its calibration catalogs, threshold, seed, null catalogs, injections, and endpoints are retired.

## Exact score and simulation source

The workflow fetches exact commit `372ed6aa1ec9da07edd1748ba0f6514bf03c5f81`, reconstructs the exact local-contrast source, and applies one deterministic calibration-only derivation.

Required hashes:

- decoded worst-family source SHA-256: `4384dd0352174e57ca1f93a2c3bd070002f026cef8acace035ba4ec05e577dac`;
- exact prior local-contrast candidate SHA-256: `b7589d8d140a37596f19d4993be1e2fdd99a18b8eaa087a02e3c4ce585000071`;
- calibration derivation script SHA-256: `cd4a0286a0dafc5bc9616fdb35d8e31d492a5b04fe5e25ae1008e301670b0f52`;
- derived tolerance-calibrated source SHA-256: `a97f207760234313b7949616fdbd506586da7b104a35a983104fdf7fb110cbfe`;
- exact public observed-subset MD5: `f57a2ac71832ceca9227441c00b8cd58`.

The derivation preserves every histogram, kernel, Poisson evidence calculation, spatial high-pass, recurrence order, null generator, injection, comparator, evaluation function, and scientific gate. It also fixes only the already documented stale Markdown reporter keys; that reporting repair occurs after authoritative JSON construction and cannot affect any score or verdict.

## Frozen tolerance calibration

For each method and each null family separately:

1. generate **512** exchangeable calibration catalog maxima;
2. sort the maxima ascending;
3. choose the smallest one-based order statistic `k` satisfying

   `P[Beta(k, n + 1 - k) >= 1 - alpha] >= 0.95`;

4. use that order statistic as the family threshold;
5. use the maximum of the ideal-null and shared-structure family thresholds as the final complete-search threshold.

With `n = 512` and `alpha = 0.10`, the frozen order statistic is **473 of 512**. Under exchangeability, this is a one-sided nonparametric tolerance construction: with at least 95% confidence, the true exceedance probability of each family threshold is no greater than 0.10.

No interpolation, asymptotic approximation, fitted tail distribution, family weighting, retry, rank change, or confidence change is allowed.

## Independent Stage-0 design

- seed: **20260805**;
- calibration catalogs per null family: **512**;
- fresh ideal-null catalogs: **200**;
- fresh shared-structure-null catalogs: **200**;
- recurrent injections per strength: **100**;
- transient injections per strength: **100**;
- alpha: **0.10**;
- calibration confidence: **0.95**;
- unchanged 15 observed years, 24 × 24 × 12 × 10 histogram, four kernels, three-year recurrence requirement, five active injected years, strengths 4/6/8/12, shared-structure distortion, and five methods.

The seed is fixed solely to separate this formulation from every prior run. No seed replacement is permitted.

## Frozen continuation gates

Every gate must pass:

1. ideal-null local-contrast FWER at most **0.15**;
2. shared-structure-null local-contrast FWER at most **0.15**;
3. weak one-year-artifact detection at most **0.20**;
4. weak recurrent recovery no more than **0.05** below the strongest valid comparator;
5. weak recurrence-margin gain over the strongest valid comparator at least **0.05**;
6. strong recurrent recovery no more than **0.05** below the strongest valid comparator;
7. recorded tolerance rank exactly **473**;
8. recorded calibration confidence exactly **0.95**.

The first six gates are unchanged from the killed full Stage-0. The final two verify that the frozen calibration mechanism actually executed.

## Kill and continuation rules

Any failed gate kills this exact tolerance-calibrated formulation. Do not alter the confidence, order-statistic rule, calibration count, alpha, score, high-pass width, recurrence order, null family, shared-distortion variance, injection, seed, comparator, threshold, FWER ceiling, or power gate after execution.

A complete pass authorizes only a separately frozen real-shower feasibility benchmark on retired labeled data. It does not authorize confirmation data, catalogue scanning, GhostStream scoring, or a discovery claim.