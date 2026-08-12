# OrbitTrace GMN local-background trajectory contrast v1 — binding result

## Verdict

`FAIL_GMN_LOCAL_BACKGROUND_TRAJECTORY_CONTRAST_V1`

The first technically valid workflow execution was run `31562287131` on execution head `2bcb676b6c614fbe1787881f90c90ba393d0c32c`. This result is binding under the frozen protocol. A later rerun cannot replace it.

## Frozen provenance

- protocol blob: `dfbfb0dd13b9ab651bb9ae18ce5d39229758b555`
- scientific implementation blob: `2b3ffba2f5a9a3c2a3de0820f12ded09406c6f16`
- inherited predictive-tube source blob: `25d91e92c41f83416ad87766c2d96884c30b714c`
- binding workflow run: `31562287131`
- binding artifact ID: `9128231625`
- artifact digest: `sha256:66e213765cf4d450eb3d0651e9501f729fc1121335d56b1836f9e36229baef61`
- result JSON SHA-256: `1543e2ee214c8980f88e38ab92d356ebde266045b30aff5f2934f855f1600514`
- prelabel JSON SHA-256: `7a62bbcd5e439d44a7e97836c446d596e990ae0477f3c769bae63885e16b2ce7`

## Exact active #839 baseline

- recovered@25: **22**
- recovered@50: **40**
- recovered@100: **75**
- recovered@500: **159**
- top-100 dominant precision: **0.7645689180574315**
- MRR: **0.019037817654898162**
- median first rank: **238.0**
- qualified matches: **256**

## Background-contrast-only order

- recovered@25: **17**
- recovered@50: **28**
- recovered@100: **44**
- recovered@500: **91**
- top-100 dominant precision: **0.48966117216117216**
- MRR: **0.015069913965423927**
- median first rank: **864.5**

## Binding equal-rank fusion

- recovered@25: **10**
- recovered@50: **15**
- recovered@100: **27**
- recovered@500: **91**
- top-100 dominant precision: **0.246293702281473**
- MRR: **0.01155483586639499**
- median first rank: **793.5**
- qualified matches: **256**

All five promotion gates failed. The direction is not marginally wrong; the local-background intrusion order is strongly anti-useful for the active ranking objective when fused as preregistered.

## Scientific interpretation

A candidate trajectory occupying a low-intrusion local tube is not, by itself, a reliable proxy for recoverable shower quality in the frozen 4,504-family union. The statistic appears to reward isolated candidate geometry that is often not the same thing as catalogue-recoverable shower structure. The result therefore rejects this particular background-contrast mechanism rather than motivating a weight/bin-width rescue.

## Permanent closure

Do not rescue this exact rule by changing solar-longitude bin width, local-background pool definition, predictive-q90 tube radius, trajectory fit degree, residual scales, fusion weight, source class, rank window, threshold, or budget. Any future method must use a genuinely distinct mechanism and be separately frozen before outcome.

## Protected-data firewall

The binding run preserved protected `[20.0,55.0]` exclusion and recorded no SonotaCo 2013/2014, OrbitTrace target, MAARSY, or DMS scientific access.
