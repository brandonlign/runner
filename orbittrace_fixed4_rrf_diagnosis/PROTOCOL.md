# Fixed4 reciprocal-rank fusion diagnosis

## Purpose

Use only the already revealed target-excluded v2 development artifact to identify a conservative rank fusion for a new, independently tested wrapper. This stage does not access OrbitTrace, rerun the detector, modify a family, or claim validation.

## Frozen input

- v2 development artifact ID `8971289223`;
- ZIP SHA-256 `01a7158ee5cf79e212689b3eb24438bbf98f959dc3588141f073412b1a9c5999`;
- target-excluded panels: 2022–2023 and 2024–2025.

## Candidate grid

For secondary ranking `mean_year_strength`, `min_year_strength`, or `size_penalized_strength`, and persistence weight `w` from 0.50 through 0.90 in increments of 0.01, compute reciprocal-rank fusion:

`RRF = w / (60 + persistence_rank) + (1 - w) / (60 + secondary_rank)`.

Higher RRF ranks first; ties use stable family identifier.

## Selection rule

Discard a candidate if either panel loses any qualified recovery at rank 500 or has negative MRR change relative to persistence. Among survivors maximize lexicographically:

1. minimum top-100 recovery change across the two panels;
2. summed top-100 recovery change;
3. minimum MRR change;
4. summed MRR change;
5. closeness of `w` to 0.67;
6. secondary-ranking order: mean, minimum-year, size-penalized.

This is development, not validation. The selected formula must be tested once on previously unused 2019–2021 known-shower labels before any OrbitTrace application.