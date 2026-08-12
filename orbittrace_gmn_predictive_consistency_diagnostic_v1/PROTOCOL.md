# OrbitTrace GMN predictive-consistency diagnostic v1

## Scientific role

This is a **target-excluded GMN mechanism diagnostic only**. It does not modify v31, does not use SonotaCo, and is not a SonotaCo successor. Its sole question is whether candidate-internal held-out physical predictability contains ranking information that is useful beyond the existing hard-family GMN order.

A PASS may authorize one separately frozen transferable successor. A FAIL permanently closes this exact predictive score and exact equal-rank fusion. No post-result rescue, threshold search, weighting search, feature subset search, split search, or alternate regression is authorized.

## Data firewall

- GMN years: 2022 and 2023 development catalogue already used by the project.
- Protected solar longitude **20 deg to 55 deg inclusive remains excluded before candidate feature construction**.
- OrbitTrace target information and target-region events are inaccessible.
- SonotaCo 2013/2014 is inaccessible during this diagnostic.
- MAARSY and DMS are inaccessible.
- Candidate generation and membership are immutable.

The exact hard-family universe is the 226 candidates in frozen P19 prelabel payload SHA-256 `276129ef8f9f31a1f8e7b1570c15f5e67ed1a7274f293f5da65bab60f86e32b8`. The frozen v8 result SHA-256 is `fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b`.

## Label-free candidate-internal feature

For every candidate and each year separately:

1. Normalize each member to accessible observables: solar longitude, solar-centered radiant longitude, ecliptic latitude, and positive geocentric speed.
2. When annual membership has at least four events, perform deterministic leave-one-out prediction. For each held-out event, fit ordinary least squares on the remaining annual members with design `[1, signed_delta_solar_longitude / 10 deg]` and response `[radiant unit-vector x,y,z, log(vg)]`.
3. Normalize the predicted radiant vector to unit length and evaluate the held-out event with one fixed physical residual: `hypot(radiant_angle / 3 deg, abs(delta_log_vg) / log(1.08))`.
4. If an annual candidate has fewer than four events, use its static annual centroid residual as the predictive residual for that year and mark the learned fraction accordingly. No family is deleted.
5. Summarize each family by the worst annual predictive q90, worst annual predictive median, worst event residual, static q90, predictive gain (`static_q90 - predictive_q90`), and learned-member fraction.

The complete feature vector is written to a prelabel artifact before truth-derived metrics or orders are evaluated.

## Frozen ranking rule

There is one predictive order only:

`(lower worst-year predictive q90, lower worst-year predictive median, higher q90 gain, family_id)`.

There is one fusion only. Convert the immutable hard order and predictive order to 1-based ranks, sum them equally, and sort by:

`(hard_rank + predictive_rank, hard_rank, family_id)`.

No coefficient, threshold, budget-specific rule, source quota, diversity parameter, or candidate deletion is permitted.

## Binding GMN signal gate

The first technically valid result is binding. PASS requires **all**:

- fused recovered@100 strictly greater than the immutable hard baseline;
- fused recovered@50 not lower than baseline;
- fused top-100 dominant precision not lower than baseline;
- fused MRR not lower than baseline.

Otherwise verdict is FAIL and this exact mechanism is closed.

## Claim boundary

Even a PASS is only GMN development evidence for the candidate-internal predictability mechanism. It does not beat HDBSCAN on SonotaCo and does not authorize looking at SonotaCo yet. A separate successor must be frozen before any new SonotaCo benchmark view, consistent with the v60 development closure.
