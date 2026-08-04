# Local-contrast recurrence: frozen full Stage-0 protocol

Status: frozen before any full-stage catalog, threshold, null-family endpoint, injection endpoint, or continuation decision is computed.

## Scientific question

Does the local high-pass recurrence statistic that passed the prospectively written reduced-screen gates retain conditional false-positive control and its recurrent-versus-transient power advantage under a substantially larger, independently seeded simulation benchmark?

The detector is unchanged. This stage increases Monte Carlo resolution and changes the random stream before any new result is observed.

## Prior boundary

- Reduced-screen workflow `30877969736` used seed `20260803`, 20 calibration trials, 20 trials per null family, and 15 injection trials per condition.
- Its generated source accidentally enforced a 0.15 null-family ceiling although the pre-run written reduced-screen protocol specified 0.20.
- PR #76 hash-verified the immutable artifact and established that all six written reduced-screen gates passed.
- The reduced screen is retired. Its catalogs, random stream, thresholds, and endpoints cannot enter this full Stage-0.

## Exact pinned implementation

The workflow fetches exact commit `372ed6aa1ec9da07edd1748ba0f6514bf03c5f81`, reconstructs the exact worst-family source, and applies the exact committed local-contrast derivation.

Required hashes:

- decoded worst-family source SHA-256: `4384dd0352174e57ca1f93a2c3bd070002f026cef8acace035ba4ec05e577dac`;
- local-contrast derivation script is taken byte-for-byte from the pinned commit;
- derived candidate source SHA-256: `b7589d8d140a37596f19d4993be1e2fdd99a18b8eaa087a02e3c4ce585000071`;
- exact public subset MD5: `f57a2ac71832ceca9227441c00b8cd58`.

No detector source byte, histogram geometry, null generator, injection, comparator, threshold algorithm, or reporting function may change.

## Independent full-stage design

- random seed: **20260804**;
- calibration trials: **100**;
- ideal-null trials: **100**;
- shared-structure-null trials: **100**;
- injection trials per strength and condition: **100**;
- alpha: **0.10**;
- exact observed SonotaCo/Shober public subset used by the prior recurrence family;
- same 24 × 24 × 12 × 10 histogram;
- same four predefined kernels;
- same three-of-years recurrence requirement;
- same recurrent strengths 4, 6, 8, and 12 per active year;
- same five active years;
- same one-year transient injections with equal total injected count;
- same ideal and shared-structure null families;
- same pooled, hard annual-confirmation, replicate, soft-recurrence, and local-contrast methods.

The new seed is fixed solely to separate this run from the reduced screen. No seed replacement is allowed.

## Frozen full Stage-0 gates

Every gate must pass:

1. ideal-null local-contrast FWER at most **0.15**;
2. shared-structure-null local-contrast FWER at most **0.15**;
3. weak one-year-artifact detection at most **0.20**;
4. weak recurrent recovery no more than **0.05** below the strongest valid comparator;
5. weak recurrence-margin gain over the strongest valid comparator at least **0.05**;
6. strong recurrent recovery no more than **0.05** below the strongest valid comparator.

These are exactly the candidate source's six gate definitions, now prospectively adopted for the higher-resolution full stage. No confidence interval, rounding exception, family removal, or secondary rescue endpoint is permitted.

## Continuation boundary

A complete pass authorizes only a separately frozen real-shower feasibility/data gate. It does not authorize training on labels, confirmation-year access, catalogue scanning, GhostStream scoring, or a discovery claim.

Any failed gate kills this exact local-contrast recurrence formulation. Do not alter the Gaussian high-pass width, recurrence order, kernels, active-year count, null families, shared-structure variance, injection geometry, strength grid, comparators, alpha, seed, trial counts, thresholds, gates, or data subset after execution.