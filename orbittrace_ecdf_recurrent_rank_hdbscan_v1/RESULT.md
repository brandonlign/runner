# ECDF recurrent-rank HDBSCAN v1 — binding GMN result

## 🔴 NEGATIVE scientific result

Exact verdict:

`FAIL_ECDF_RECURRENT_RANK_HDBSCAN_V1_GMN_DEVELOPMENT`

The first technically valid target-excluded GMN 2022/2023 endpoint completed successfully end-to-end under the frozen protocol.

Binding workflow run: `31851273161`  
Binding artifact: `9237628549`  
Artifact digest: `sha256:3c77a0be386d5cac063adcc6a90742a8efd3a3f5a887c58e8ba296432e423247`  
Binding execution commit: `def75a5bc180e17f1fc0edeb39dffcd14f64bc80`  
Result SHA-256: `c43c8c5044d3b9af755fd6719a5e8eede3cbbd1dc6a16d24950df8b707899d1e`  
Prelabel SHA-256: `2fdef7b4f99b8bc977455aa7f4d9b3524a7060449cbc440425329eb601d6aa70`

## Mechanism integrity

The frozen mechanism was active and behaved exactly as intended:

- parent candidates: **2,097**;
- ECDF successor candidates: **2,097**;
- candidate memberships: **exactly identical** to promoted recurrent-EOM;
- parent order SHA-256: `f224b3a9744890e31d5bd0ced87449fcf4df734a4e3a0b143ff2633cf3dcd303`;
- successor order SHA-256: `185720728270bfe69cac300e9ad5e122bc15e16b352fe9165e61cd322bc27ae3`;
- `mechanism_active=true`.

Thus this is a genuine ranking result rather than a no-op or candidate-selection confound.

## Exact comparison versus promoted recurrent-EOM

### GMN 2022

- recovered@25: `22 -> 22`
- recovered@50: `45 -> 45`
- recovered@100: `89 -> 89`
- recovered@500: `193 -> 192`
- full-catalogue qualified matches: `236 -> 236`
- top-100 dominant precision: `0.7856486012780942 -> 0.7856486012780942`
- MRR: `0.022498269587309373 -> 0.02240930301892303`
- median top-500 fragmentation: `1.0 -> 1.0`

### GMN 2023

- recovered@25: `23 -> 23`
- recovered@50: `46 -> 46`
- recovered@100: `89 -> 89`
- recovered@500: `192 -> 191`
- full-catalogue qualified matches: `244 -> 244`
- top-100 dominant precision: `0.7867680236864514 -> 0.7867680236864514`
- MRR: `0.0220239288966045 -> 0.02194359237400517`
- median top-500 fragmentation: `1.0 -> 1.0`

The frozen gate required a strict recovered@100 improvement in at least one year, with no regression in @50/@100, top-100 precision, MRR, or fragmentation in either year. There was **no strict @100 improvement**, and MRR regressed slightly in both years. Therefore the exact successor fails.

## Scientific interpretation

Per-year empirical-CDF normalization is a mathematically valid way to remove arbitrary monotone differences in the numerical scales of the two annual EOM contributions. The synthetic audit proved that property before GMN access. However, on the permanent GMN development split, that scale invariance does not improve fixed-budget shower recovery and slightly worsens the ordering of known showers overall.

This result rejects the exact hypothesis that replacing raw annual-EOM magnitude comparison with within-year ECDF ranks improves recurrent-EOM's catalogue ranking under the frozen evaluation.

## Permanent closure

Do **not** rescue this version by:

- blending raw recurrent stability with ECDF rank;
- changing the ECDF definition or denominator;
- changing exact-tie handling;
- weighting years differently;
- using a percentile threshold;
- using a different rank fusion or tie break;
- applying ECDF only to a subset of candidates;
- tuning on the observed GMN result.

The pre-outcome dormant SonotaCo protocol must remain unexecuted and be closed because the GMN activation condition failed.

Promoted recurrent-EOM HDBSCAN v1 remains the methodology parent.

## Firewall

Binding execution preserved:

- protected `[20.0,55.0]` inaccessible;
- OrbitTrace target information/events inaccessible;
- SonotaCo 2013/2014 not accessed;
- ASFN not accessed;
- AMOS not accessed;
- EFN not accessed;
- MAARSY not accessed;
- DMS not accessed;
- no post-result parameter search or scientific modification.
