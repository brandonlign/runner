# M2 full-URC integration protocol — v1

## Status

This protocol was frozen before any admissible #846 scientific result was known.

It defines the **only** allowed full-catalogue integration of the M2 event-level P12 membership challenger admitted by final GMN method-selection freeze #848. It does not authorize any new GMN architecture search.

The two earlier #846 executions `31343806656` and `31344761936` were invalidated pre-result by strict-group source issues and are permanently inadmissible regardless of outcome. The only admissible #846 scientific source is final corrected commit `e5733a57488b7b8dff26c15ff76f679810efac9c`, executed as run `31344902186`.

The final corrected wrapper changes fold grouping only: qualified cores group by their unchanged #846 target identity; nonqualified near-misses group by best eligible shower association solely to prevent cross-fold same-shower leakage; unassociated fragments retain family-specific background groups. Event targets, features, models, weights, thresholds, caps, P12 assignments, hard cores, feasibility gates, and the 20°–55° firewall are unchanged.

## Preconditions

The integration is scientifically authorized only if all of the following are true:

1. final corrected #846 run `31344902186` returns `PASS_EVENT_LEVEL_P12_MEMBERSHIP_CALIBRATION_FEASIBILITY` under its already-frozen selector and at least three grid variants pass its feasibility gates;
2. the exact single model / probability threshold / additions-per-core cap selected by that run passes the already-frozen five-salt fixed-policy whole-shower stress in #850, with all five panels passing under the final corrected grouping source;
3. the exact #839 candidate universe and rank reproduce unchanged.

If either #846 or #850 fails, this integration remains dormant permanently and M2 cannot be rescued.

## Immutable discovery catalogue

The integration may not change candidate existence or ordering.

The catalogue remains exactly:

- 226 hard-v8 families;
- 1,075 frozen P19-soft families;
- 3,203 frozen P20-soft families;
- 4,504 total candidate families.

P21 and every weaker later proposal layer remain excluded.

The catalogue rank remains exactly the #839 strict-group ExtraTrees quality-regression + diversity order:

- ExtraTrees depth 4;
- minimum leaf 5;
- diversity lambda 0.8;
- diversity scale 1.0;
- selected-order SHA-256 `ffc97f7bc4fbc8f13170ffe8a71260e1596190e39e9324c24e8ba7719f427449`.

No candidate may be inserted, deleted, suppressed, merged, rescored, or reordered by this integration.

## M2 membership reconstruction

For GMN 2022/2023 scientific evaluation, M2 uses the exact **out-of-fold predictions** from final corrected #846's selected policy, reconstructed from the frozen final corrected source and folds.

This is required because the GMN integration is still a development-performance estimate. A model fitted on all GMN labels may not be used to score the same GMN events for the promotion decision.

Only membership of the 226 hard families can change:

- the immutable hard core is never removed;
- the only eligible additions are the exact 17,238 already-frozen P12 assignments;
- the model family, threshold, and cap are exactly those selected by final corrected #846;
- no new feature, probability calibration, threshold, cap, ranking term, or family-specific exception is allowed;
- P19-soft and P20-soft memberships remain exactly as frozen.

## Required reproduction checks

Before M2 is judged, the integration must reproduce:

- the exact final corrected #846 selected hard-family historical macro F1;
- the exact final corrected #846 selected corrected qualified count;
- the exact final corrected #846 selected corrected recovery@100;
- the exact final corrected #846 selected corrected top-100 dominant precision;
- all #839/M0 reference endpoints under the exact 4,504-family order.

Any reproduction failure invalidates the integration rather than allowing a compatibility patch after scientific values are inspected.

## Final #848 promotion gate

The integrated M2 catalogue can replace M0 only if **all** of the following hold under the exact #839 order:

- recovery@25 >= 22;
- recovery@50 >= 40;
- recovery@100 >= 75;
- recovery@500 >= 159;
- qualified known streams >= 256;
- MRR >= 0.019037817654898162;
- top-100 dominant precision >= 0.740000;
- best-membership macro F1 >= 0.19953659309876195;
- annual all-shower mean F1 delta versus M0 >= 0 in both 2022 and 2023;
- annual 4–9-member mean F1 delta versus M0 >= -0.002 in each year and >= 0 on average;
- at least one of the 25–49, 50–99, or 100+ strata improves in both years and has mean two-year gain >= +0.015;
- candidate IDs, candidate count, order, and target firewall remain unchanged.

The result is exactly one of:

- `PASS_M2_FULL_URC_PROMOTION_GATE`;
- `FAIL_M2_FULL_URC_PROMOTION_GATE`.

A failure is permanent for M2. No parameter or membership rule may be changed from the result.

## Application/deployment rule if M2 is promoted

This GMN integration uses OOF predictions only for unbiased development evaluation. If M2 passes and becomes the final method, its deployable membership classifier is then frozen as follows **without further model selection**:

1. use the exact model class/hyperparameters selected by final corrected #846;
2. reconstruct the exact 17,238 GMN training rows/features from the final corrected frozen #846 pipeline;
3. fit one model on **all** eligible GMN development rows using the same group-balanced/class-balanced sample-weight function already frozen in #846;
4. preserve the exact #846 probability threshold and additions-per-core cap;
5. preserve every P12 feature definition and hard-core rule;
6. serialize/fingerprint the fitted model and source before any SonotaCo 2013/2014 scientific access.

This full-GMN fit is training for downstream application, not an additional GMN performance estimate. Its GMN in-sample score may not be used for promotion or reported as validation.

If the frozen M2 feature interface cannot be reproduced on SonotaCo or MAARSY from their permitted observables, that is an architecture-compatibility failure; no post-result proxy feature is allowed.

## Downstream consequence

If M2 passes this integration, M2 becomes the final GMN membership architecture because M1/#845 already failed scientifically. If M2 fails or never becomes authorized, M0/#839 original memberships remain final.

Once that choice resolves, GMN methodology development stops. The selected method must be frozen as one deployable executable before the single SonotaCo 2013/2014 literature test against Sugar and catalogue HDBSCAN.

The authoritative integration source may unwrap the final corrected #846 module but may not substitute either invalid earlier #846 implementation.

No SonotaCo 2013/2014 scientific value, MAARSY scientific value, target-region event, OrbitTrace coordinate/member/identity information, or prior OrbitTrace recovery result may be accessed by this integration stage.
