# OrbitTrace P3 — cross-year dual-null membership freeze

## Status and activation

This protocol is frozen **before any canonical P2 scientific PASS/FAIL exists**. It is dormant unless the sole authoritative P2 lineage returns a genuine target-excluded scientific development no-go with every integrity/source/firewall gate passing. A technical P2 failure cannot activate P3.

P3 is a distinct successor architecture, not a P2 threshold adjustment. It uses no fitted logistic classifier and no P1 posterior/background-intensity rule.

## Immutable discovery core

P3 inherits exactly the promoted-v8 target-excluded development core:

- years: GMN 2022 and 2023;
- blind exclusion: solar longitude 20°–55° before labels and before orbit use;
- exact 226 recurrent v8 families;
- exact promoted-v8 multiplicity rank order;
- immutable v8 seed event IDs;
- no family merge, split, deletion, reranking, or recursive growth;
- newly admitted members never become seeds or recalibrate any family.

The exact promoted-v8 source identity and baseline endpoints remain the same ones already pinned by P1/P2: 95 qualified matches, recovery@100 58, MRR 0.045531138942766655, top-100 dominant precision 0.6884631112636006, macro F1 0.1736657194465356.

## P3 membership architecture

For each family and target year, evidence is built **only from immutable seeds in the opposite year**.

### 1. Local candidate universe

- family activity center is the opposite-year immutable-seed circular mean solar longitude transported by the same centered coordinate semantics used by the frozen v8 runtime;
- target-year nonseed candidates are restricted to a fixed ±5.0° solar-longitude window;
- all immutable seeds from all families are excluded from the candidate/background pool;
- no shower label may select candidates or background rows.

### 2. Observation-space view

Use the same four observation coordinates already used by the membership lineages: centered solar longitude, sun-centered ecliptic longitude, ecliptic latitude, and geocentric speed.

For the opposite-year immutable seeds:

- center by the exact frozen pooled/circular coordinate helpers;
- estimate one 4D OAS covariance from immutable seeds only;
- candidate nonconformity is squared Mahalanobis distance to that opposite-year seed model;
- every eligible target-year local nonseed receives the same observation nonconformity score.

No learned class weights or probability model is fit.

### 3. Orbit-space view

Use the exact already-frozen Southworth–Hawkins implementation and exact native orbit semantics. For every candidate/background event with a valid orbit:

- orbital nonconformity is the minimum exact D_SH to any valid immutable opposite-year seed orbit;
- exact physical compatibility additionally requires D_SH < 0.05;
- no orbit value may be used to change the family rank, candidate window, observation covariance, or seed set.

### 4. Empirical local-background evidence

For each family-direction, the target-year local nonseed pool is the fixed empirical null for both views.

For candidate c:

- `p_obs = (1 + #{background rows with observation distance <= distance(c)}) / (N_obs + 1)`;
- `p_orbit = (1 + #{valid-orbit background rows with min D_SH <= min D_SH(c)}) / (N_orbit + 1)`;
- the intersection-union evidence value is `p_dual = max(p_obs, p_orbit)` so both views must independently be unusual under the same fixed local null.

No null trimming, stream removal, iterative cleaning, density weighting, tail fitting, smoothing, or alternative p-value estimator is permitted.

A family-direction is membership-eligible only with at least 128 local nonseed rows and at least 128 valid-orbit local nonseed rows. Otherwise that direction proposes no new member; this is not grounds for relaxing the minimum.

### 5. Candidate-wise family multiplicity and conflict resolution

For each nonseed event, collect every family-direction hypothesis for which the event is inside the fixed local window and has both evidence views.

Let `m` be that event's number of eligible family hypotheses. Define the fixed Bonferroni-adjusted evidence `p_adj = min(1, m * p_dual)`.

A new member is admitted only if all are true:

- exact D_SH < 0.05;
- `p_adj <= 0.01`;
- it is the unique best family by `(p_adj, p_dual, observation_distance, min_D_SH, original_family_rank, family_id)` lexicographic order.

The 0.01 familywise candidate threshold is fixed a priori. No alternative 0.05/0.02/0.005 threshold may be tried.

All seed IDs remain members regardless of P3 evidence. New members are appended once after the complete two-year proposal table is frozen. Multiplicity ranking remains byte-for-byte unchanged.

## Hard pre-truth chronology

Before the first native shower-label value is read, the implementation must durably freeze and SHA-256 hash:

1. exact target-excluded scan event IDs/geometry and valid-orbit identities;
2. exact 226-family seed universe and multiplicity order;
3. every family-direction OAS model and opposite-year seed IDs;
4. every eligible local background ID and both null-score arrays;
5. every candidate/family hypothesis with raw `p_obs`, `p_orbit`, `p_dual`, hypothesis count `m`, and `p_adj`;
6. every conflict-resolution row;
7. every final P3 added event ID and complete expanded family membership;
8. explicit proof that family order is unchanged and new members never seed/refit.

Only after that complete membership payload is frozen may known-shower truth be parsed for evaluation.

## Development integrity / nonvacuity gates

All must pass:

- exact promoted-v8 source/result identity reproduced;
- exact 226 seed families and multiplicity order reproduced;
- target interval excluded before labels and orbit use;
- zero shower-label value access pretruth;
- exact D_SH source identity;
- every seed remains in its original family;
- no new member seeds/refits any model;
- no parameter search;
- at least 20 families gain >=1 member;
- at least 200 total nonseed events are admitted.

A technical/integrity failure is not a scientific P3 no-go.

## Frozen scientific development gates

P3 passes development only if **all** are true relative to exact promoted v8:

- qualified known-shower matches >= 95;
- recovery@100 >= 58;
- MRR >= 0.95 × 0.045531138942766655;
- top-100 dominant-label precision >= 0.68;
- macro F1 >= 0.25.

The macro-F1 floor is deliberately absolute rather than tuned to P1/P2 output; it requires a large improvement over promoted v8 while preserving every catalogue-coverage count. Failure of any scientific gate permanently rejects P3 as frozen.

Verdicts:

- `PASS_CROSSYEAR_DUAL_NULL_MEMBERSHIP_P3_DEVELOPMENT`
- `FAIL_CROSSYEAR_DUAL_NULL_MEMBERSHIP_P3_NO_GO`

## Downstream rule

Only a genuine P3 development PASS may enter a separately frozen same-information matched Sugar/HDBSCAN comparison. P3 may not access an external/pristine panel or the OrbitTrace target region before that matched-literature gate passes.

No OrbitTrace target coordinate, target member ID, target identity, prior target rank, target activity profile, or target-containing event is accessed or encoded by this protocol.
