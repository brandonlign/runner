# Majority-conditioned recurrent stream evidence: authoritative reduced-screen result

Runner workflow `30880030523` completed the full frozen reduced screen. Artifact `8880969951` was preserved with digest `sha256:4607b61259aa79c357a8bdfa469792f2947635044af4834fc3f64e2f10f8d41c`.

Exact frozen design:

- candidate source SHA-256: `3d60e3622d7ec406bb03cd4ab43faec84be1eff4d0dd70afa6ed79b8fd777281`;
- seed: **20260805**;
- 30 calibration catalogs per null family;
- 30 fresh catalogs per null family;
- 40 recurrent and transient injections per strength;
- alpha: **0.10**;
- runtime: **138.94 seconds**.

## Result

False-positive control:

- ideal-null majority-conditioned FWER: **0.100**;
- shared-structure-null majority-conditioned FWER: **0.100**.

Weak-signal performance, averaging strengths 4 and 6 per active year:

- majority-conditioned recurrent recovery: **0.4000**;
- strongest valid comparator recurrent recovery: **0.2500**;
- recovery gain: **+0.1500**;
- majority-conditioned one-year-artifact detection: **0.0000**;
- majority-conditioned recurrence margin: **0.4000**;
- strongest comparator recurrence margin: **0.2500**;
- recurrence-margin gain: **+0.1500**.

Strong-signal performance, averaging strengths 8 and 12:

- majority-conditioned recurrent recovery: **0.9375**;
- strongest valid comparator recurrent recovery: **0.9000**;
- difference: **+0.0375**.

All six frozen gates passed. Verdict: **`CONTINUE_MAJORITY_CONDITIONED_FULL_STAGE0`**.

## Interpretation

Subtracting the pointwise median annual evidence directly removed structures shared by most observing years while preserving a signal active in five of fifteen years. In this reduced screen it controlled both predeclared null families, completely rejected equal-total one-year artifacts, and materially improved weak recurrent recovery over every valid comparator.

This is not validation. Thirty null catalogs and forty injections per strength are only a kill screen, and median conditioning may suppress genuinely persistent streams active in most years. The result authorizes only a separately frozen, larger, independently seeded simulation Stage-0. No real-shower benchmark, confirmation panel, catalogue scan, or GhostStream application is authorized.