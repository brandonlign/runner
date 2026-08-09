# OrbitTrace P5 joint held-out-seed support protocol

## Status

Preregistered source/protocol only after authoritative P4 development returned `FAIL_DUAL_VIEW_SEED_ENVELOPE_MEMBERSHIP_P4_NO_GO` in workflow `31292258243`.

P5 is not a new detector and does not alter the promoted-v8 family universe or rank. It is a strict structural refinement of P4 membership assignment.

## Immutable base

P5 preserves exactly:

- promoted v8 226 recurrent families, immutable seed membership, multiplicity rank and family order;
- the exact P2 two-view representation: opposite-year OAS Mahalanobis observation distance `d_obs` and exact Southworth-Hawkins `D_SH` (`d_orb`);
- the exact P2 weighted StandardScaler + L2 logistic model architecture and unit-background responsibility competition;
- the exact P3 deterministic five-fold family cross-fit, held-out seed-floor rule, strict seed-floor >0.5 reliability requirement, <=10% local negative tail requirement, final probability >= held-out seed floor, nonrecursive growth and responsibility >0.5;
- the exact P4 coordinate-wise maximum held-out-seed envelope;
- the target exclusion and truth firewall: solar longitude 20°–55° is removed before any geometry, model, candidate, membership or truth operation.

No OrbitTrace target identity, coordinates, members, activity profile, historical target result, target-containing result, comparator result or external-validation result may be accessed.

## Sole P5 change: joint held-out-seed support

P4 accepts a candidate when its two coordinates are separately no worse than the largest held-out recurrent-seed value in each coordinate. Those two maxima can be supplied by different seeds, allowing an unobserved rectangular corner of the two-view space.

P5 removes only that rectangular-corner extrapolation.

For each reliable family-direction, let the held-out recurrent-seed feature vectors be

`S = {(d_obs_j, d_orb_j)}`.

Before any known-shower label value is read, freeze the componentwise-maximal (Pareto-maximal under larger-is-worse distance coordinates) subset `M` of those held-out seed vectors. A P4 proposal survives P5 iff there exists at least one `m in M` such that

- candidate `d_obs <= m.d_obs`, and
- candidate `d_orb <= m.d_orb`.

Equivalently, the candidate must be at least as coherent as one actual held-out recurrent seed in both existing P3/P4 views simultaneously.

This rule:

- preserves every held-out recurrent seed by construction;
- is a strict subset of the P4 coordinate envelope;
- introduces no new numeric threshold;
- uses no quantile, multiplier, offset, shrinkage, interpolation weight, label, catalogue identity or parameter search;
- does not alter model fitting, candidate probabilities, family competition, responsibility, seed membership or ranking.

There is exactly one primary P5 configuration. No alternate support rule, convex-hull rule, quantile rule, relaxed rule or tuned fallback is eligible after observing P5 truth metrics.

## Development data and truth firewall

Development remains only the exact target-excluded GMN 2022/2023 universe used by P2/P3/P4. Known-shower label values remain unread until cross-fit state, model, P5 decisions and P5 expanded membership are all frozen and hashed.

P5 must record the exact generated source SHA-256, cross-fit SHA-256, model SHA-256, decision SHA-256 and membership SHA-256.

## Immutable scientific gates

The substantive gates are unchanged from P2/P3/P4. P5 passes development only if every integrity gate passes and all of the following hold:

- exact promoted-v8 baseline reproduced;
- every v8 seed preserved and exact 226-family order preserved;
- qualified known-shower matches >=95;
- recovery@100 >=58;
- top-100 dominant precision >=0.65;
- macro F1 >=0.2536657194465356;
- large-shower mean recall >=1.5 × exact-v8 large-shower mean recall;
- large-shower mean precision >=0.85;
- expansion is nonvacuous;
- P5 joint support is frozen before truth;
- every held-out recurrent seed is supported by the frozen P5 support set;
- every surviving P5 proposal satisfies exact P3 seed-floor, exact P4 coordinate envelope and P5 joint held-out-seed support.

PASS token: `PASS_JOINT_SEED_SUPPORT_MEMBERSHIP_P5_DEVELOPMENT`.

FAIL token: `FAIL_JOINT_SEED_SUPPORT_MEMBERSHIP_P5_NO_GO`.

A FAIL closes this exact configuration. It cannot be repaired by threshold relaxation or second-chance variants on the same revealed development truth.

## Downstream hierarchy

Only a genuine P5 development PASS can become eligible for a separately frozen matched Sugar/HDBSCAN benchmark. The stronger project hierarchy still requires sparse-stream superiority against both comparators in both matched SonotaCo years before pristine external validation, and external PASS before any target-containing final search.
