# OrbitTrace P3 — cross-fitted seed-floor two-view membership

## Status and succession

This is a protocol-only successor frozen **before the authoritative P2 development result is known**. It is dormant unless exact canonical P2 returns a genuine scientific `FAIL_CROSSYEAR_TWO_VIEW_MEMBERSHIP_P2_NO_GO`. A technical/integrity P2 failure does not activate P3 and permits only equivalence-preserving P2 repair.

P3 is motivated only by evidence available before the P2 result: promoted v8 has good catalogue coverage but low membership F1, while P1 showed that aggressive label-free expansion can nearly double macro F1 yet dilute a small number of catalogue matches. P3 therefore preserves P2's two-view physical/observational representation but adds a fully self-supervised family-direction reliability gate intended to suppress expansion where the recurrent seeds themselves do not support transport.

No P2 outcome, P2 per-label result, OrbitTrace target information, or target-region event may be used to change this protocol.

## Immutable base

P3 preserves exactly:

- the 226 promoted-v8 recurrent seed families and multiplicity rank;
- exact v8 pooled-year centroids;
- immutable seed IDs;
- P2 feature definitions only: source-year OAS Mahalanobis observation distance `d_obs` and minimum exact Southworth–Hawkins distance `d_orb` to a source-year immutable seed;
- exact ±5° target-year nonseed windows;
- every target-excluded nonseed event in each window as the negative universe, with >=128 negatives per family-direction;
- equal 0.5 positive / 0.5 negative total weight per family-direction;
- weighted `StandardScaler` and L2 logistic regression `C=1.0`, `lbfgs`, `max_iter=1000`, `tol=1e-10`;
- unit-background joint conflict model;
- strict maximum responsibility `>0.5`;
- promoted-v8 rank then family ID for deterministic conflict ties;
- no refit after additions and no recursive growth.

The same exact target-excluded GMN 2022/2023 development universe, generic orbit parser, D_SH implementation and pretruth/truth firewall as canonical P2 are inherited unchanged. The audited header-whitespace transport wrapper may be used only as the same equivalence-preserving schema repair.

## P3 addition: deterministic five-fold family cross-fitting

Before the final all-family P2 model is fit, assign each immutable family to exactly one of five folds by:

`fold = int.from_bytes(SHA256(family_id UTF-8)[:8], 'big') % 5`.

No fold stratification, balancing, retry or search is permitted.

For each fold independently:

1. construct the exact P2 training examples from the other four folds only;
2. fit the exact same weighted scaler and logistic regression as P2;
3. score every held-out family-direction's immutable target-year seeds and its complete exact target-window negative universe;
4. do not fit or update any model using the held-out family's rows during that fold.

All five fold assignments, fitted cross-fit model parameters and held-out score vectors are SHA-frozen before any known-shower truth value is read.

## Family-direction seed-floor reliability gate

For each held-out family-direction define:

- `seed_floor_fd = min(p_cf(seed))` over all opposite-year immutable target seeds scored by the fold model;
- `negative_tail_fd = count(p_cf(negative) >= seed_floor_fd) / N_negative` over the exact nonseed window.

The direction is **reliable** if and only if all are true:

1. at least four immutable target-year seeds exist (already required by the recurrent-family base);
2. `seed_floor_fd > 0.5`;
3. `negative_tail_fd <= 0.10`;
4. every cross-fit score is finite and the fold classifier converged before `max_iter`.

These thresholds are fixed pre-P2-result. The seed floor is data-adaptive but label-free: a final candidate must look at least as stream-like as the weakest genuinely recurrent seed under a classifier that was not trained on that family. The 10% negative-tail ceiling is deliberately conservative because the nonseed window may itself contain unlabeled true stream members.

No unreliable direction may add any member. It remains present as an immutable v8 seed family/direction for ranking and evaluation.

## Final model and membership

After all cross-fit reliability quantities are immutable, fit the exact canonical P2 scaler/logistic model once on **all** family-directions using the original P2 training rules.

For each nonseed event/family proposal in a reliable direction:

1. compute the exact final-model stream probability and odds;
2. require `probability >= seed_floor_fd` for that family-direction;
3. discard the proposal otherwise.

Resolve the surviving proposals with the unchanged P2 joint denominator `1 + sum(stream_odds)` and assign only if the best family responsibility is strictly greater than 0.5. Preserve seeds exactly. Added events never alter centroids, cross-fit thresholds, the final classifier or any later proposal.

The complete fold assignment, cross-fit models, reliability table, final model, candidate proposal table, conflict responsibilities and final expanded memberships are SHA-frozen before truth access.

## Development evaluation and gates

Known-shower truth may be opened only after all P3 membership outputs above are immutable.

P3 inherits the **same substantive scientific gates as P2**, without relaxation:

- exact promoted-v8 226-family rank preserved;
- every promoted-v8 seed preserved;
- exact v8 baseline reproduced;
- exact D_SH source identity;
- cross-fit and final classifiers converged;
- cross-fit/reliability/final-model/membership payloads frozen before truth;
- expansion nonvacuous;
- qualified matches >= promoted-v8 95;
- recovery@100 >= promoted-v8 58;
- top-100 dominant precision >=0.65;
- macro F1 >= promoted-v8 macro F1 +0.08 absolute;
- on the exact v8-qualified large-shower subset already defined by P2, mean recall >=1.5× v8;
- large-shower mean precision >=0.85.

Additional integrity gates require exactly five deterministic folds, every family appearing in exactly one held-out fold, no held-out family row entering its fold model, exact seed-floor formula, exact 10% negative-tail ceiling, and zero proposals from unreliable directions.

Return exactly:

- `PASS_CROSSFIT_SEED_FLOOR_MEMBERSHIP_P3_DEVELOPMENT` if all integrity and scientific gates pass;
- `FAIL_CROSSFIT_SEED_FLOOR_MEMBERSHIP_P3_NO_GO` otherwise after a valid powered execution.

A scientific FAIL permanently rejects P3. No threshold, fold count, tail ceiling, seed-floor definition or P2 base rule may be retuned from the result.

## Downstream rule

Only a P3 development PASS may proceed to a separately pre-frozen matched Sugar/HDBSCAN comparison using the same broad/sparse superiority bars as P2. Literature superiority must then be followed by a genuinely unexposed cross-survey validation frozen before external values are opened. No development or literature result alone can authorize final target access.

## Firewall

Solar longitude 20°–55° remains removed before development geometry/orbit use. No OrbitTrace coordinate, target ID, canonical member, historical target rank/recovery, target-containing GMN event, withheld reference or reveal result may be accessed during P3 development.