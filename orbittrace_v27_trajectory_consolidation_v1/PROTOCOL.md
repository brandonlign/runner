# OrbitTrace v27 — trajectory completion + sibling membership consolidation

## Motivation

The exposed SonotaCo successor line established three facts before v27:

1. the broad hard/P19/P20 candidate universe contains enough fixed-membership headroom to beat catalogue HDBSCAN at the exact 11/9 budgets;
2. strict whole-shower ranking successors through the authoritative two-head v24 still miss HDBSCAN, especially 2014;
3. post-result inspection of the frozen v24 top-9 shows some selected families are extremely pure but under-recalled, while large parts of the same physical shower are fragmented into geometrically adjacent sibling candidates.

v27 therefore changes **membership completion/consolidation only** around the already-frozen authoritative v24 two-head OOF order. It does not search a new ranker, detector, radius, alpha, residual threshold, activity width, comparator budget, or panel-specific rule.

## Frozen ancestry

v27 inherits exactly from the authoritative annual two-head v24 branch / PR #953:

- exact v22/v23 pretruth hard+P19+P20 candidate universe;
- exact v19 joint-conformal expanded memberships as high-purity seed memberships;
- exact 71-dimensional pretruth feature matrix and centroid geometry;
- exact strict same-shower five-fold annual two-head OOF ranking;
- exact final order `two_head_min_oof_v19_rank_sum`;
- exact #854-compatible equal-budget one-to-one F1 evaluator.

The v24 control must reproduce the authoritative four-panel metrics and fused-order identities before any v27 scientific verdict is accepted.

## Stage 1 — one-pass trajectory completion

Starting from the exact frozen v19/joint-conformal memberships, run one additional completion pass using the **exact pre-SonotaCo v4 trajectory mechanism** frozen in PR #458:

- affine trajectory order: 1;
- conformal alpha: 0.05;
- source activity-arc padding: +/-6 degrees solar longitude;
- trajectory residual ceiling: 1.5;
- residual formula: `sqrt((dlon*cos(mean_lat)/2)^2 + (dlat/2)^2 + (dvg/2)^2)`;
- source leave-one-out conformal reference;
- target event accepted only when residual <=1.5 and conformal p >0.05;
- source support comes only from the opposite year's **original joint-conformal seed membership**;
- newly added target members never become support in the same pass;
- no recursive growth;
- no alpha/model/activity/residual/threshold search.

The cascade-specific seed rule is fixed before execution:

- every event already owned by any v19/joint-conformal family in the target year is protected and cannot be reassigned during trajectory completion;
- only currently unowned target-year events are eligible for new assignment;
- when an unowned event is accepted by multiple families, assign it uniquely by highest conformal p-value, then smallest trajectory residual, then current frozen v19 rank, then stable family ID.

This differs from standalone v4 only in its **starting seed set**: v27 deliberately uses the later frozen joint-conformal high-purity memberships rather than the original sparse v8 seed skeleton. All v4 trajectory constants and fitting/calibration formulas remain unchanged.

## Stage 2 — direct sibling membership consolidation

After the exact v24 two-head OOF fused order is reconstructed, use the already-frozen #843/v20 direct family geometry at radius **1.0**.

Scan families once in the frozen v24 fused order:

1. if the current family has no direct radius-1.0 conflict with an already accepted family, accept it as a representative;
2. otherwise defer it and assign it to the **earliest/highest-ranked accepted family** with which it has a direct radius-1.0 conflict;
3. union the deferred family's trajectory-completed event membership into that accepted representative;
4. after the scan, append every deferred family in its original v24 order with its own membership unchanged.

Thus:

- no family is deleted;
- the complete candidate universe is preserved;
- only representative memberships receive deterministic sibling unions;
- the geometric radius is exactly 1.0 and is not searched;
- consolidation has no comparator-budget input;
- no transitive connected-component closure is used; only direct conflicts to already accepted representatives are merged;
- no post-result merge rule, radius, order or membership parameter may be changed.

## Truth boundary and evaluation

For each matched Sugar and HDBSCAN row route:

1. regenerate exact v22/v24 pretruth features, centroids and joint-conformal seed memberships from label-free rows;
2. run and hash-freeze v27 trajectory completion before truth;
3. hash-freeze both route payloads;
4. only then load the immutable already-exposed SonotaCo truth/comparator artifact;
5. reconstruct exact strict-group v24 two-head OOF order and verify the authoritative v24 control;
6. perform the frozen direct sibling membership consolidation;
7. evaluate once under exact #854-compatible equal-budget one-to-one F1 semantics.

v27 has exactly one successor output. PASS requires in all four comparator/year panels:

- candidate macro-F1 strictly greater than the frozen literature comparator; and
- recovered F1>0.5 count greater than or equal to the comparator.

No second search or rescue variant is allowed after the result.

## Candidate freeze after a PASS

Only an all-four exposed-development PASS permits fitting the already-defined v24 two annual heads once on all exposed SonotaCo development families and fingerprinting them together with the frozen v27 membership-cascade source. No full-fit in-sample SonotaCo score may be used for promotion.

Any later protected external validation must have its own candidate-specific preregistered protocol and firewall. A v27 SonotaCo PASS alone does not authorize opening MAARSY, DMS, OrbitTrace target information, target-region events, or protected solar-longitude 20°–55° content.

## Claim boundary

SonotaCo 2013/2014 is exposed development only. Even an all-four PASS is a matched-literature development superiority result, not pristine cross-survey validation and not a change to the original historical blind-HDBSCAN OrbitTrace discovery provenance.
