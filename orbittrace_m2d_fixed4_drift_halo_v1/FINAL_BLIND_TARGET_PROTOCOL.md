# M2D fixed4-seeded drift halo v1 — final blind OrbitTrace application

## Activation hierarchy

This protocol is frozen before the GMN development outcome exists. It is dormant unless both upstream stages pass without any scientific change:

1. PR #1401 returns `PASS_M2D_FIXED4_DRIFT_HALO_V1_GMN_DEVELOPMENT`;
2. the exact no-retuning SonotaCo transfer frozen in `SONOTACO_TRANSFER_PROTOCOL.md` returns its frozen PASS.

A scientific FAIL at either stage permanently disables this target application.

## Immutable blind discovery parent

Use the already-frozen **baseline** support-resolved TopoModal + exact M2D blind replay from PR #1378, not support-pruned or later variants.

The complete parent ranking was frozen before the canonical OrbitTrace IDs were revealed:

- candidate count `8,469`;
- frozen pretruth gzip SHA-256 `6d72b0f9558b89228953dd73b3760c61df039b713f233473079ae4fac563a100`;
- frozen pretruth inner SHA-256 `7ff3b13bc45e19b4b886453b4d8cc3b4f18090bf8a2291e39850540fd69b5e53`.

Historical reveal later showed one parent at rank 84 contains all 18 canonical 2022+2023 target IDs. That fact is known history only and may not enter Stage A construction, selection, ranking, fitting or membership.

## Stage A — full target-reference-absent halo freeze

With the canonical OrbitTrace reference and every reveal artifact absent from the workspace, apply the exact frozen drift-halo method to **all 8,469 parent candidates**:

- parent M2D membership and rank unchanged;
- exact two-anchor fixed4 consensus seed inside each parent/year;
- fixed /5 deg solar-longitude predictor, /4 deg Sun-centered radiant responses and /log(1.1) speed response;
- annual unweighted affine drift using `numpy.linalg.lstsq(..., rcond=None)` and the frozen rank-deficient zero-slope fallback;
- OAS covariance on the 3D seed drift residuals;
- membership inside exact `chi2.ppf(0.95, df=3)` plus explicit retention of all seed members;
- halo restricted to the immutable parent envelope.

The complete parent/seed/model/covariance/event-score/halo mapping for all candidates must be serialized and SHA-256 frozen before target-reference access. Stage A must record `target_reference_access=false`, `target_information_used=false`, and unchanged complete parent order.

No best-parent choice, target interval, target coordinates, family merge, halo expansion, threshold change or reranking is allowed.

## Stage B — exact-ID-only reveal

Only after Stage A is sealed may the canonical 2022 and 2023 OrbitTrace event-ID sets be loaded.

Reveal is exact set intersection only. No coordinate/orbit/radiant/activity matching, nearest-target matching, halo recomputation, parent switch, family merge, event expansion or reranking.

For each frozen parent/halo pair report:

- parent rank and size;
- seed size;
- halo size;
- exact target overlap in 2022, 2023 and total;
- halo precision = exact overlap / halo size;
- target recall = exact overlap / 18;
- exact target F1.

## Frozen classification

The rank and minimum annual-support requirements inherit the pre-existing method-agnostic exact-ID firewall:

- parent rank <=100;
- >=4 exact canonical target IDs in 2022;
- >=4 exact canonical target IDs in 2023;
- >=8 exact canonical IDs total.

The cleanliness requirement is the same recovery-quality threshold already used throughout the frozen OrbitTrace literature benchmarks:

- exact halo-vs-target F1 >0.5.

No arbitrary new member-count or precision cutoff is introduced.

Classification:

- `CLEAN_M2D_FIXED4_DRIFT_HALO_ORBITTRACE_REDISCOVERY`: rank/support conditions pass and exact target F1 >0.5;
- `PARTIAL_M2D_FIXED4_DRIFT_HALO_ORBITTRACE_RECOVERY`: rank/support conditions pass but exact target F1 <=0.5;
- `NO_M2D_FIXED4_DRIFT_HALO_ORBITTRACE_RECOVERY`: rank/support conditions fail.

A clean result supports the claim that an independently frozen M2D discovery envelope contains a high-quality fixed4-seeded, drift-conditioned target membership. It does not rewrite historical discovery chronology, constitute pristine external validation, or establish formal IAU status.

## No-rescue rule

The first technically valid Stage-B classification is final. No confidence-level change, covariance change, clipping, background term, orbital term, seed alteration, best-component selection, target-aware trimming, family merge, parent switch, rank cutoff change, annual-support change, F1 threshold change or second reveal is authorized.