# OrbitTrace P4 dual-view held-out seed-envelope membership protocol

## Status and scientific role

P4 is a narrowly targeted successor to the finalized P3 scientific no-go. It is **not** a new detector and does not restart methodology development. The exact promoted-v8 226-family universe/rank, exact P2 two-view representation and final logistic model, exact P3 deterministic five-fold family cross-fit, P3 held-out seed-floor reliability rule, immutable seeds, nonrecursive membership, and joint unit-background responsibility >0.5 remain unchanged.

Authoritative P3 finalization: PR #632 / workflow `31291999345`, verdict `FAIL_CROSSFIT_SEED_FLOOR_MEMBERSHIP_P3_NO_GO`.

The only new P4 scientific rule is a coordinate-wise held-out recurrent-seed envelope applied before a P3 proposal may enter the unchanged conflict/responsibility competition.

## Motivation fixed before P4 truth evaluation

P3 improved macro F1 and preserved recovery@100/top-100 precision, but failed qualified-match non-regression and large-shower precision. The P3 immutable pretruth artifact shows that the remaining problem is not primarily inter-family conflict: only 1,727 proposal events were conflicted, while 36,742 nonseed events were assigned. Further, 439/452 directions passed P3's coarse `negative_tail <= 0.10` reliability rule, and pretruth direction assignment burden is strongly concentrated in high-tail directions (Pearson correlation approximately 0.89 between held-out negative-tail fraction and direction assignment count).

That evidence motivates candidate-level two-view coherence control rather than a detector restart, a new classifier, or post-hoc threshold search.

## Immutable P4 change

For each held-out family-direction during the existing P3 cross-fit, let its recurrent target-year seed feature matrix be `X_seed`, with exact existing columns:

1. `d_obs`: opposite-year OAS Mahalanobis observation distance;
2. `d_orb`: minimum exact Southworth-Hawkins `D_SH` to an immutable source-year seed.

Freeze the coordinate-wise held-out seed ceiling

- `obs_ceiling = max(X_seed[:, d_obs])`
- `orb_ceiling = max(X_seed[:, d_orb])`

No quantile, multiplier, offset, shrinkage, search, or known-shower label is used.

A target-year nonseed event may become a proposal only if **all** exact P3 proposal requirements pass **and**:

- `candidate_d_obs <= obs_ceiling`; and
- `candidate_d_orb <= orb_ceiling`.

Thus a candidate cannot compensate for being less coherent than every held-out recurrent seed in one physical view by scoring extremely well in the other view. The use of the maximum seed distance is deliberately recall-preserving: it is the loosest coordinate-wise envelope that excludes no held-out seed in either view.

## Everything else remains exact P3

- years: 2022/2023 target-excluded development;
- inaccessible interval: solar longitude 20°-55°;
- 226 promoted-v8 recurrent families and exact multiplicity rank;
- exact v8 seeds always preserved;
- exact P2 two-view feature construction, OAS covariance, exact `D_SH`, ±5° local windows, >=128 negatives/direction, equal family/direction weighting;
- exact weighted StandardScaler + L2 logistic regression `C=1.0`;
- exact SHA-256 deterministic five-fold family cross-fitting;
- exact P3 reliability: >=4 target-year seeds, held-out seed floor >0.5, held-out negative tail at the seed floor <=0.10, finite/converged;
- exact P3 final-model probability >= frozen held-out seed floor;
- exact unit-background joint responsibility >0.5;
- no new member may seed growth; no refit after proposals; no rank change.

## One-shot development gates

P4 uses the same substantive frozen gates as P2/P3:

- exact v8 baseline reproduced;
- all 226 families/rank and every v8 seed preserved;
- qualified known-shower matches >=95;
- recovery@100 >=58;
- top-100 dominant precision >=0.65;
- macro F1 >=0.2536657194465356;
- large-shower mean recall >=1.5x exact-v8 baseline;
- large-shower mean precision >=0.85;
- expansion nonvacuous;
- all source/pretruth/truth-firewall/integrity gates pass.

The P4 envelope itself must also be frozen before truth, must exclude no held-out recurrent seed by construction, and every surviving P4 proposal must lie inside both frozen coordinate ceilings.

## Anti-tuning rule

There is exactly one primary P4 configuration: the coordinate-wise maximum held-out seed envelope above. No alternative quantiles, margins, tail cutoffs, responsibility thresholds, probability thresholds, feature weights, or family-specific tuning may be evaluated against known-shower truth in this lineage before the primary P4 verdict.

If P4 fails, that exact configuration is a no-go. Any successor must be justified structurally and frozen before another truth evaluation; P4 may not be threshold-retuned to chase the failed endpoint.

## Downstream firewall

P4 literature comparison, external validation, and final target-containing search remain closed unless P4 first passes this target-excluded development gate. No OrbitTrace target information, target coordinates, historical target rank/recovery, or event in solar longitude 20°-55° may be used in P4 development.
