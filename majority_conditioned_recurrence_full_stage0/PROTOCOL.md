# Majority-conditioned recurrence: frozen full Stage-0 protocol

Status: frozen before any full-stage calibration maximum, null endpoint, injection endpoint, or continuation decision is computed.

## Scientific question

Does subtracting the pointwise median annual evidence before recurrence retain the reduced-screen power gain while controlling both independent-year and persistent shared-structure catalog false discoveries under a larger, independently seeded benchmark?

The candidate statistic and simulator are unchanged. Only Monte Carlo resolution and the random stream increase.

## Prior boundary

The reduced screen in PR #86 used exact candidate SHA-256 `3d60e3622d7ec406bb03cd4ab43faec84be1eff4d0dd70afa6ed79b8fd777281`, seed `20260805`, 30 calibration catalogs per null family, 30 fresh catalogs per null family, and 40 injections per strength and condition.

It passed all six gates:

- ideal/shared FWER 0.10 / 0.10;
- weak recurrent recovery 0.40 versus strongest comparator 0.25;
- zero weak one-year-artifact detection;
- recurrence-margin gain +0.15;
- strong recovery difference +0.0375.

That reduced screen is retired. Its catalogs, thresholds, random stream, and endpoints cannot enter this stage.

## Exact pinned implementation

The workflow fetches exact commit `b8748f3e641e52dfe3b1500d6c7356bd9732f54a`, reconstructs the exact worst-family source, and applies the exact committed majority-conditioning derivation.

Required hashes:

- decoded worst-family source SHA-256: `4384dd0352174e57ca1f93a2c3bd070002f026cef8acace035ba4ec05e577dac`;
- derived majority-conditioned candidate SHA-256: `3d60e3622d7ec406bb03cd4ab43faec84be1eff4d0dd70afa6ed79b8fd777281`;
- exact public observed-subset MD5: `f57a2ac71832ceca9227441c00b8cd58`.

No detector source byte, histogram, kernel, null generator, injection, comparator, evaluation function, or threshold algorithm may change.

## Independent full-stage design

- seed: **20260806**;
- calibration catalogs per null family: **100**;
- fresh ideal-null catalogs: **100**;
- fresh shared-structure-null catalogs: **100**;
- recurrent injections per strength: **100**;
- transient injections per strength: **100**;
- alpha: **0.10**;
- unchanged 15 observed years, 24 × 24 × 12 × 10 histogram, four kernels, third-strongest-year recurrence, five active injected years, strengths 4/6/8/12, shared-structure distortion, and five methods.

The seed is fixed solely to separate this run from all prior screens. No seed replacement is permitted.

## Frozen full-stage gates

Every gate must pass:

1. ideal-null majority-conditioned FWER at most **0.15**;
2. shared-structure-null majority-conditioned FWER at most **0.15**;
3. weak one-year-artifact detection at most **0.20**;
4. weak recurrent recovery no more than **0.05** below the strongest valid comparator;
5. weak recurrence-margin gain over the strongest valid comparator at least **0.05**;
6. strong recurrent recovery no more than **0.05** below the strongest valid comparator.

No confidence interval, rounding exception, null-family removal, or secondary rescue endpoint is permitted.

## Continuation boundary

A complete pass authorizes only a separately frozen real-shower feasibility benchmark on retired labeled data. That stage must explicitly stratify established showers by the number of active years, because pointwise median subtraction may suppress streams present in most of the 15-year span.

A pass does not authorize confirmation data, catalogue scanning, GhostStream scoring, or a discovery claim.

Any failed gate kills this exact majority-conditioned formulation. Do not alter the median subtraction, recurrence order, active-year count, kernel, null family, shared-distortion variance, injection geometry, strength grid, comparator, alpha, seed, trial count, threshold, FWER ceiling, or power gate after execution.