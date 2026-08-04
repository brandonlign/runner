# Consensus-lowpass recurrence reduced screen: authoritative no-go

Runner workflow `30882497352` completed the exact frozen reduced screen. Artifact `8881878421` was preserved with digest `sha256:f1864539c9309e66c4ca9f35d86e711a91430845fd09fe9bad9f1f20fbe74faf`.

## Frozen design

- exact candidate SHA-256: `9f630c8eca2ffb1a5bdbc0598b744dffccb6026d2476467b99c6caa3d410a9fa`;
- seed: `20260807`;
- 30 calibration catalogs per null family;
- 30 fresh catalogs per null family;
- 30 injection trials per strength for five-year recurrence, twelve-year persistent recurrence, and one-year artifacts;
- alpha: `0.10`;
- persistent activity: exactly 12 of 15 years;
- fixed consensus smoothing sigma: `(1.6, 1.6, 1.0, 0.9)`.

## Calibration

- ideal-null FWER: **0.1333** — pass against 0.20;
- shared-structure-null FWER: **0.2333** — fail against 0.20.

The shared-structure family set the candidate threshold at **3.91785**, above its ideal-null threshold **3.19878**, but broad shared hotspots still produced excessive complete-search false discoveries.

## Original five-year recurrence

- candidate weak recovery: **0.3667**;
- strongest comparator weak recovery: **0.3000**;
- difference: **+0.0667**;
- weak one-year-artifact detection: **0.0000**.

The candidate preserved the useful minority-active recurrence signal.

## Twelve-year persistent shared-background recurrence

- candidate weak recovery: **0.9167**;
- strongest comparator weak recovery: **0.9500**;
- candidate weak recurrence margin: **0.9167**;
- strongest comparator margin: **0.9500**;
- weak recovery gain versus best comparator: **−0.0333**;
- margin gain versus best comparator: **−0.0333**;
- candidate strong recovery: **1.0000**;
- strongest comparator strong recovery: **1.0000**.

The original hard third-year recurrence statistic was the strongest persistent comparator. The consensus-lowpass candidate retained high absolute power but did not improve the already strong baseline.

## Frozen-gate outcome

Four of seven gates passed. The formulation failed:

- shared-structure-null FWER at most 0.20;
- persistent shared-background weak-recovery gain at least +0.05;
- persistent shared-background recurrence-margin gain at least +0.05.

Verdict: **`KILL_CONSENSUS_LOWPASS_RECURRENCE`**.

## Interpretation

Subtracting the fixed smooth projection of cross-year consensus avoided the complete suppression caused by full-median subtraction and preserved a narrow signal active in most years. However, it did not remove broad shared-structure peaks sufficiently to control catalog-level false discoveries, and it sacrificed a small amount of persistent sensitivity relative to the unmodified hard recurrence statistic.

The result narrows the methodological problem: persistent-stream power is already strong. The unresolved issue is robust complete-search calibration of the hard recurrence score under shared spatial structure. Do not alter the smoothing sigma, persistent active-year count, subtraction rule, recurrence order, null family, seed, trial count, alpha, comparator, threshold construction, or gate to rescue this formulation.

No full benchmark, real-shower study, confirmation, catalogue scan, or GhostStream application is authorized.