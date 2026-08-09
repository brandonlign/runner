# OrbitTrace P11 cross-fit local density-contrast order-statistic membership

## Status and precedence

P11 is the sole post-P10 development successor fixed **before P10 truth** in PR #665 comments `5230285375`, `5230292345`, `5230298947`, and `5230302320`. P10 subsequently failed development in authoritative workflow `31300225235` / artifact `9034442543` without any target access. No alternative P11 configuration is eligible.

The motivating architectural defect predates P9/P10 truth and the later comparator-firewall incident: the inherited P2/P3/P6 logistic output is trained with 0.5 total positive and 0.5 total local-nonseed weight per family-direction, so its `predict_proba` is a balanced discriminative score rather than a literal posterior under the actual local stream/background incidence. P11 does **not** tune that score or the responsibility constant; it adds one target-free local density-contrast veto in the already-frozen two-view space.

## Immutable inherited method

P11 inherits exact P10 in full:

- immutable promoted-v8 family cores, event seeds, family order and multiplicity rank;
- GMN 2022/2023 development only;
- solar longitude **20°–55° inaccessible before every pretruth freeze**;
- P2 two-view features only: cross-year source-seed OAS Mahalanobis observation distance `d_obs` and minimum exact Southworth-Hawkins `D_SH` to source-year immutable seeds;
- ±5° local target-year nonseed window and >=128 local nonseed rows/direction;
- deterministic five family folds;
- P3 reliability with `seed_floor > 0.5` and local negative-tail <= `0.10`;
- P6 candidate scoring with the identical family-excluded held-fold scaler/logistic model used for that direction's seed scores;
- P8 finite-sample membership floor rank `k=max(1,floor(0.10*(n+1)))`;
- P9 requirement that both reciprocal cross-year directions are P3-reliable before either may grow;
- P4 full-seed coordinate envelope;
- P10 floor-retained held-seed P5 joint-support frontier;
- unit-background responsibility >0.5, no recursive growth, no refit/recentering/reranking.

P11 is a **candidate veto only**. It cannot add a candidate rejected by P10 and cannot change any immutable seed.

## P11 density-contrast rule

For each direction, use the exact already-fitted P6 held-fold `StandardScaler` and only the existing two columns `[d_obs,D_SH]`.

Let `Z+` be the exact held-out recurrent target-year seed feature rows for that family-direction. Let `Zu` be the exact local target-year nonseed/unlabelled rows already used by P3. `Zu` is constructed upstream only after removing the union of **all** immutable v8 seed IDs, so a recurrent calibration seed cannot appear in the unlabelled reference.

All neighbor queries use exact 1-nearest-neighbor Euclidean distance in the standardized 2-D space (`scipy.spatial.cKDTree`, `p=2`, `eps=0`, `workers=1`); the returned distance is squared before the ratio. Squaring is a monotone implementation choice and introduces no scale/bandwidth.

For held-out recurrent seed `i`:

`A_i = d2(seed_i, nearest other Z+) / d2(seed_i, nearest Zu)`.

The numerator uses a `k=2` self-query to exclude the seed's own row. If the denominator is exactly zero, set `A_i=+inf`.

Let `n=len(Z+)` and reuse **exactly** the inherited P3/P8 exclusion budget:

`k=max(1,floor(P3_NEGATIVE_TAIL_MAX*(n+1)))` with `P3_NEGATIVE_TAIL_MAX=0.10`.

Sort `A_i` ascending and set the direction threshold to the kth-largest seed nonconformity:

`T = sorted_A[n-k]`.

For local nonseed candidate `x`:

`A(x) = d2(x, nearest Z+) / d2(x, nearest other Zu)`.

The local unlabelled rows are sorted by stable event ID before neighbor indexing. Because the candidate itself is in `Zu`, the denominator uses the second distance from an exact `k=2` self-query. If a distinct duplicate event is at exactly the same standardized coordinates, the nearest-other denominator is correctly zero. A candidate with exact zero denominator is **rejected directly**, even if `T=+inf`. Otherwise it passes P11 iff `A(x) <= T`.

Final proposal inclusion is therefore:

`exact P10 allowed AND P11 density contrast allowed`.

No candidate passing P11 may bypass any probability, reciprocal reliability, P4 envelope, P10 joint support, or responsibility rule.

## Statistical claim

P11 is called a **local density-contrast order-statistic** method, not a formal full-conformal predictor. Held-out recurrent seeds calibrate the observable retained-seed exclusion budget, but candidates come from the local unlabeled pool rather than an exchangeable augmented sample. Generalization must therefore be established later by the frozen no-retuning external/held-out stage, not asserted from conformal theory.

The 1-NN squared-radius ratio is a local nonparametric density-contrast statistic in the existing standardized 2-D representation. Contamination of the unlabeled reference by genuine stream-like events shrinks the denominator and therefore makes this veto more conservative in stream-dense regions.

## No tuning / prohibited alternatives

P11 introduces **no new numeric threshold**. The following are fixed and may not be searched or changed after truth:

- nearest-neighbor order = 1;
- two inherited features only;
- exact inherited held-fold scaler;
- squared Euclidean distance;
- alpha/rank source = inherited `P3_NEGATIVE_TAIL_MAX=0.10`;
- no alternate norm, feature weighting/subset, bandwidth, epsilon, density estimator, prior, pseudo-count, family exception, rescue rule, score combination, responsibility change, geometry change, cap, or parameter sweep.

## Pretruth integrity requirements

Before any known-shower label value is indexed, P11 must durably freeze and hash:

1. exact P10 scientific source identity;
2. every direction's positive and local-unlabelled identity sets;
3. held-fold scaler identity/provenance;
4. every held-seed density-ratio vector by raw little-endian float64 SHA-256 (IEEE `+inf` allowed in the binary hash);
5. every direction's order-statistic rank and finite/infinite threshold flag;
6. every eligible direction's complete candidate density-ratio vector by raw float64 SHA-256 and candidate-ID hash;
7. the density accept/reject decision summary;
8. complete final memberships and normal P3/P10 proposal/assignment decisions.

JSON must never serialize nonstandard numeric infinity: thresholds use `null` plus an explicit infinity flag. Every geometry/catalogue pass must retain the 20°–55° blind exclusion and truth labels remain unread until all P11 pretruth hashes and memberships exist.

## Immutable development gates

P11 passes development only if **all** inherited gates and P11 integrity gates pass, including:

- qualified known-shower matches >= **95**;
- recovery@100 >= **58**;
- top-100 dominant precision >= **0.65**;
- macro-F1 >= exact-v8 macro-F1 + **0.08**;
- large-shower mean recall >= **1.5×** exact-v8;
- large-shower mean precision >= **0.85**;
- expansion and P11 veto nonvacuous;
- exact 226-family order and immutable seed preservation;
- target/truth firewall clean.

No gate may be weakened after execution.

## Downstream promotion rule

If P11 passes development, freeze P11 and run the already-required matched literature benchmark. Promotion beyond development requires sparse/weak-stream superiority against **both Sugar and catalogue HDBSCAN in both SonotaCo 2023 and 2025** under matched data, with no material overall-performance sacrifice. Only then may the frozen no-retuning external/held-out validation proceed. OrbitTrace remains inaccessible until those prerequisites pass.