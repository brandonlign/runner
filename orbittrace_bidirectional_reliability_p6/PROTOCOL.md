# OrbitTrace P6 bidirectional-reliability membership protocol

## Status

Preregistered after authoritative P5 development returned `FAIL_JOINT_SEED_SUPPORT_MEMBERSHIP_P5_NO_GO` in workflow `31293431873`.

P6 is not a new detector. It is an artifact-only conservative refinement of the exact frozen P5 memberships. It does not refit, rescore, rerank, regenerate geometry, change thresholds, or add any event that P5 did not already assign.

## Immutable inputs

P6 requires the exact canonical P5 artifact from workflow `31293431873`:

- artifact id `9032407268`;
- artifact ZIP digest `sha256:39ba9b6f40c0a07f326ae61f9f1dc06d9d3ed3d11c4400f41a75dfb4473c3ea6`;
- P5 membership SHA `933be44170bc91cf8e92a38b84689d590610ecdf809e911ac40022b5d4e806c9`;
- P5 decisions SHA `b9b87427e8d5521e92bca3d27ef9528da7509f2c9d5a647764789abc65323711`;
- P5 cross-fit SHA `55defa606101cfc0e0f9038d326fd19cfd99d0c423b68602ecd5581e00ff8ac1`;
- P5 model SHA `8ac8b13ab025a636884d44a2b19d478c9de5c138c3da190f3dfe3d73490257eb`;
- exact 226 promoted-v8 families and immutable rank.

No target information, target-region event, comparator result or external-validation result may be accessed.

## Pretruth structural diagnosis

The exact P5 cross-fit state contains 452 family-directions. Under the already-frozen P3 reliability rule, 439 directions are reliable and 13 are unreliable.

Eight of the 226 families have at least one unreliable direction. Five of those already receive no P5 additions. The remaining three receive 3,320 P5 assignments exclusively through the opposite surviving direction even though reciprocal cross-year transport failed:

- `G091aa6c2910b`: 1,185 additions;
- `Gacd9eac470df`: 863 additions;
- `Gd17a5f4465cf`: 1,272 additions.

These counts come only from the immutable pretruth P5 decisions/cross-fit payload and do not use known-shower labels.

## Sole P6 change

A family may receive **any** expanded membership only if **both** of its two opposite-year directions satisfy the exact frozen P3 reliability gate.

For each family:

- if both 2022→2023 and 2023→2022 directions are P3-reliable, keep its exact P5 additions unchanged;
- otherwise remove all P5 additions from that family and revert it to its exact immutable v8 seed membership in both years.

Dropped P5 assignments are not reassigned to another family. No competition is rerun. P6 is therefore a strict subset of P5 membership.

This rule adds no numerical parameter. It enforces the same cross-year recurrence principle already used to define the family universe at the membership-expansion level: an expansion is permitted only when the frozen membership discriminator transports reliably in both directions.

## Frozen pretruth output identity

Applying the sole P6 rule to the exact P5 artifact must produce exactly:

- bidirectionally reliable families: 218;
- ineligible families: 8;
- dropped P5 assignments: 3,320;
- retained P6 additions: 21,626;
- families gaining members: 214;
- P6 membership canonical SHA-256: `40b0b720ef37427bc2d89aeb71c145683cbc69eff9b56ac5516e87fc34348ff6`;
- P6 decisions canonical SHA-256: `5e76bbf2fd75acdf1d1bc770dc3c60de338a6388524c956544afe4c1aabc8490`.

These identities must be source-audited and frozen before any known-shower truth is opened.

There is exactly one primary P6 configuration. No one-direction exception, ratio tolerance, minimum-addition exception, threshold relaxation, reassignment, fallback or parameter search is allowed after P6 truth is observed.

## Truth firewall

The P6 transform operates only on the immutable P5 pretruth artifact. Known-shower truth remains inaccessible until P6 expanded membership and P6 decisions have been regenerated and verified against the exact SHA-256 values above.

Truth evaluation then uses only the exact prior target-excluded GMN 2022/2023 evaluator. Solar longitude 20°–55° remains excluded. The family order/rank is unchanged.

## Immutable development gates

P6 passes only if every integrity gate passes and all substantive gates inherited unchanged from P2/P3/P4/P5 pass:

- exact promoted-v8 baseline reproduced;
- exact 226-family order and every v8 seed preserved;
- P6 membership and decisions equal the preregistered hashes above;
- expansion occurs only in families with both frozen P3 directions reliable;
- qualified known-shower matches >=95;
- recovery@100 >=58;
- top-100 dominant precision >=0.65;
- macro F1 >=0.2536657194465356;
- large-shower mean recall >=1.5 × exact-v8 large-shower mean recall;
- large-shower mean precision >=0.85;
- expansion is nonvacuous.

PASS token: `PASS_BIDIRECTIONAL_RELIABILITY_MEMBERSHIP_P6_DEVELOPMENT`.

FAIL token: `FAIL_BIDIRECTIONAL_RELIABILITY_MEMBERSHIP_P6_NO_GO`.

A genuine FAIL closes this exact configuration. Later parallel P5 branches are not eligible second-chance promotion routes.

## Downstream hierarchy

Only a genuine P6 development PASS may proceed to a separately frozen matched Sugar/HDBSCAN comparison. Promotion still requires sparse-stream superiority against both comparators in both matched SonotaCo 2023 and 2025 panels, followed by pristine no-retuning external validation, before any target-containing final search.
