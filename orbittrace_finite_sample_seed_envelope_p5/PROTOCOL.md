# OrbitTrace P5 finite-sample-valid dual-view seed-envelope protocol

## Scientific role

P5 is a **minimal successor to P4, not a detector restart**. It preserves the entire P3/P4 architecture: the exact promoted-v8 226-family universe and multiplicity order, immutable v8 seeds, P2 OAS-Mahalanobis + exact Southworth-Hawkins D_SH features, the exact P3 deterministic five-fold family cross-fit and seed-floor reliability rule, the exact final weighted StandardScaler + L2 logistic model, nonrecursive membership, and unit-background responsibility >0.5.

Authoritative predecessor results:

- P3: `FAIL_CROSSFIT_SEED_FLOOR_MEMBERSHIP_P3_NO_GO`, finalized in workflow `31291999345`.
- P4: `FAIL_DUAL_VIEW_SEED_ENVELOPE_MEMBERSHIP_P4_NO_GO`, workflow `31292258243`; P4 passed every substantive gate except qualified-match non-regression (92 vs required 95), while large-shower precision improved to 0.8819815897427599 and recovery@100 remained 58.

No P3/P4 threshold is retuned in P5.

## The one P5 change

P4 applied a coordinate-wise held-out-seed maximum envelope in every reliable family-direction:

- candidate `d_obs <= max(held-out recurrent-seed d_obs)`; and
- candidate `d_orb <= max(held-out recurrent-seed d_orb)`.

P5 keeps this exact P4 envelope **only when its finite-sample resolution is adequate**. Let `n` be the number of held-out recurrent seeds in that family-direction.

- if `n >= 19`: apply the exact P4 two-view maximum envelope;
- if `n < 19`: do not use the coordinate-wise envelope and fall back to the exact P3 seed-floor proposal rule for that direction.

All other P3/P4 gates and competition rules are unchanged.

## Why the threshold is 19 — frozen before P5 truth

Under exchangeability of a future true member with `n` held-out recurrent seeds, the probability that the future member exceeds the sample maximum in one continuous coordinate is `1/(n+1)`. P4 rejects a candidate if it exceeds the sample maximum in **either of two** pre-existing views. Without assuming dependence between those views, the union bound gives a true-member rejection probability no larger than `2/(n+1)` from the two maximum tests alone.

P3 already fixes `0.10` as the maximum acceptable held-out local-background tail at the weakest recurrent seed. P5 requires the sampling uncertainty introduced by the two-view maximum envelope not to exceed that same fixed 10% scale:

`2/(n+1) <= 0.10`, hence `n >= 19`.

This is a finite-sample adequacy calculation, not a threshold search against known-shower truth. No alternative seed-count cutoffs may be evaluated in the primary P5 lineage.

## Pretruth motivation, not parameter tuning

The immutable P4 pretruth artifact shows why a finite-sample correction is structurally relevant: 389/439 reliable directions have fewer than 19 held-out seeds, and 8,961/12,691 P4 envelope rejections above the P3 seed floor occurred in those under-resolved directions. This diagnostic uses proposal geometry and seed counts only; it does not choose the cutoff or use known-shower labels.

## Exact inherited architecture

P5 keeps unchanged:

- development years: 2022 and 2023;
- inaccessible solar-longitude interval: 20°–55°;
- exact 226 promoted-v8 recurrent families, v8 seeds, and multiplicity rank;
- P2 two-view representation and ±5° local negative windows;
- >=128 negatives per family-direction;
- equal family/direction class weighting;
- weighted StandardScaler;
- L2 logistic regression with C=1.0, lbfgs, max_iter=1000, tol=1e-10;
- SHA-256 deterministic five-fold family cross-fit;
- P3 reliability: >=4 target-year seeds, held-out seed floor >0.5, negative tail at the seed floor <=0.10, finite/converged;
- final probability >= immutable held-out seed floor;
- joint odds with unit background and winning responsibility >0.5;
- no recursive growth, no refit from added members, no reranking.

## One-shot development gates

The same substantive frozen P2/P3/P4 gates apply:

- exact v8 baseline reproduced;
- all 226 families/rank and every v8 seed preserved;
- qualified known-shower matches >=95;
- recovery@100 >=58;
- top-100 dominant precision >=0.65;
- macro F1 >=0.2536657194465356;
- large-shower mean recall >=1.5x the exact-v8 baseline;
- large-shower mean precision >=0.85;
- expansion nonvacuous;
- all source/pretruth/truth-firewall/integrity gates pass.

Additional P5 integrity gates require:

- `P5_ENVELOPE_MIN_SEEDS == 19`;
- every proposal from a direction with `n >= 19` was subjected to the exact P4 two-view envelope and lies inside it;
- every proposal from a direction with `n < 19` is governed only by the exact P3 seed-floor rule, not the coordinate envelope;
- the finite-sample rule and all decisions are frozen before known-shower truth is evaluated.

## Anti-tuning rule

There is exactly one primary P5 configuration: envelope iff `n >= 19`. No 18/20/other cutoff, quantile, multiplier, margin, altered negative-tail threshold, altered seed-floor threshold, altered responsibility threshold, altered feature weighting, or family-specific exception may be tested against known-shower truth before the primary P5 verdict.

If exact P5 fails, it is a no-go. Any successor must be justified structurally and frozen before another truth evaluation; P5 may not be loosened or tightened to chase a failed metric.

## Downstream firewall

Literature comparison, external validation, and target-containing final search remain closed unless P5 first passes target-excluded development. No OrbitTrace target information, target coordinates, historical target rank/recovery, target activity profile, or event in solar longitude 20°–55° may be used during P5 development.
