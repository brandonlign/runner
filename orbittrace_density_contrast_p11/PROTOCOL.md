# OrbitTrace P11 pretruth contingency reservation

Status: **INELIGIBLE unless authoritative exact P10 is a genuine scientific development no-go.** This branch is source/protocol-only. It must never execute while P10 is unresolved or if P10 passes.

## Provenance

This reservation was created while authoritative unchanged P10 recovery workflow `31300225235` was still inside its target-excluded scientific execution step and before any P10 result was inspected.

The architecture derives from the pre-exposure source-only note in PR #659 comment `5230139141`: inherited P2/P3/P6 logistic `predict_proba` values are scores learned under an artificial balanced 0.5-positive/0.5-local-unlabeled weighting and must not be interpreted as literal posterior probabilities. The complete P11 rule was preregistered before P10 truth in PR #665 comments `5230285375`, `5230292345`, `5230298947`, and `5230302320`.

No Sugar/HDBSCAN outcome value, external scientific value, target-region event, OrbitTrace target information, or P10 truth may be used to alter this reservation. Solar longitude 20°–55° remains inaccessible.

## Exact scientific rule if P11 becomes eligible

P11 is **cross-fit local density-contrast order-statistic membership**. It is a single additional candidate veto on exact P10, not a new detector and not a formal full-conformal predictor.

1. Inherit exact P10 completely: immutable v8 family cores/seeds/order/rank; P2 `[d_obs,D_SH]` representation; deterministic five family folds; P3 reciprocal-direction reliability and `P3_NEGATIVE_TAIL_MAX=0.10`; P4 full-seed coordinate envelope; P8 finite-sample membership floor; P9 bidirectional family reliability; P10 floor-consistent retained-seed joint frontier; responsibility >0.5; no recursion/refit/recentering/reranking; every substantive development gate.
2. For each P9-bidirectionally-reliable family-direction, use the exact already-fitted P6 held-fold `StandardScaler` to transform that direction's existing two columns `[d_obs,D_SH]`. No new feature, metric weight, or learned transform.
3. Let `Z+` be the direction's exact held-out recurrent target-year seeds and `Zu` the exact local target-year globally-v8-seed-excluded unlabeled rows already used by P3. Canonical P2 source constructs this reference from `valid_nonseed_by_year` before the ±5° family-direction window.
4. In held-fold standardized 2-D space use exact Euclidean squared distance. For seed `i`, `A_i = d2(seed_i, nearest other Z+) / d2(seed_i, nearest Zu)`. A seed denominator exactly zero gives `A_i=+inf`.
5. For each local unlabeled candidate `x`, `A(x) = d2(x, nearest Z+) / d2(x, nearest other Zu)`, excluding the candidate's own event row. A candidate nearest-other-unlabeled denominator exactly zero is rejected directly; no epsilon/tolerance is allowed.
6. Reuse the exact inherited finite-sample exclusion rank with no new alpha. For `n=len(Z+)`, `k=max(1,floor(P3_NEGATIVE_TAIL_MAX*(n+1)))`. Sort seed nonconformities ascending and set `T=sorted_A[n-k]`, the kth-largest seed nonconformity. A positive-denominator P10-surviving candidate remains only if `A(x) <= T`.
7. The density veto may only remove P10 proposals. It cannot relax P10 probability floor, P4/P10 geometry, P9 bidirectional reliability, responsibility, seed preservation, or ranking. New members never seed growth.
8. No alternate nearest-neighbor `k`, distance norm, feature subset, alpha, bandwidth, prior, pseudo-count, family exception, rescue, score combination, threshold search, or parameter sweep is eligible. `1-NN`, exact held-fold standardization, the existing two features, and inherited `0.10` are the sole configuration.

## Deterministic implementation freeze

- Sort each direction's local unlabeled rows by stable event ID before neighbor indexing.
- Use `scipy.spatial.cKDTree`, exact query `p=2`, `eps=0`, `workers=1`; square returned Euclidean distances.
- Seed nearest-positive: 2-neighbor self-query, excluding own row. Seed nearest-unlabeled: 1-neighbor query.
- Candidate nearest-positive: 1-neighbor query. Candidate nearest-other-unlabeled: 2-neighbor self-query, excluding own index. Exact duplicate other events legitimately yield zero nearest-other distance and are rejected.
- Exact distance ties have the same scientific distance; stable event-ID ordering is provenance only.
- Seed zero-denominator `+inf` values participate in the order statistic. If `T=+inf`, the veto is nonrestrictive for positive-denominator candidates in that direction; zero-denominator candidates still reject directly.
- Hash raw float64 seed/candidate nonconformity arrays (IEEE `+inf` allowed in binary hashes). JSON records infinity counts/flags rather than nonstandard numeric infinity values.

Pretruth P9 feasibility counts, using only `p3_crossfit_pretruth.json`: 218 bidirectionally reliable families / 436 eligible directions; 5,018 held-out recurrent-seed rows; 3,961,356 local unlabeled rows; seed count 4–236 (median 7); unlabeled count 2,197–40,849 (median 7,894). Among eligible directions, inherited P8 rank is 1 for 389 and >1 for 47.

## Statistical interpretation

Do not claim a formal conformal p-value or theorem. The test candidate is drawn from the local unlabeled pool, not an exchangeable augmented sample with the recurrent seeds. The frozen order statistic directly limits exclusion of the observed held-out recurrent evidence under the inherited finite-sample rank; prospective generalization must be established by the later no-retuning held-out/external stage.

The squared 1-NN radius ratio is monotone with inverse local 1-NN density contrast up to direction-constant sample-size factors, which cancel when the threshold is calibrated within the same direction. Genuine stream contamination in `Zu` can shrink the denominator and therefore makes the veto more conservative in stream-dense regions.

## Required pretruth integrity before any P11 truth

Before any known-shower label value is indexed, a future P11 implementation must freeze and hash:
- exact P10 source and inputs;
- held-fold scaler identities;
- exact `Z+` and sorted `Zu` event identities per eligible direction;
- seed nonconformities, infinity flags, `k`, and thresholds;
- candidate nonconformities, zero-denominator flags, and density decisions;
- complete proposal/conflict/assignment state and final memberships.

It must prove: 20°–55° exclusion; `Zu` contains no global v8 seed; every candidate excludes its own unlabeled row; every surviving proposal satisfies exact P10 and P11; all P9 family-reliability constraints remain; v8 seeds/families/rank are identity-unchanged; no result/comparator/external/target information enters any pretruth step.

## Development gates

Unchanged from the current lineage:
- qualified known-shower matches >=95;
- recovery@100 >=58;
- top-100 dominant precision >=0.65;
- macro-F1 >= v8 + 0.08;
- large-shower mean recall >=1.5x v8;
- large-shower mean precision >=0.85;
- nonvacuous, integrity, and truth-firewall gates all pass.

No gate may be weakened after P10. If P11 passes development, matched sparse-stream superiority against **both Sugar and catalogue HDBSCAN in both SonotaCo 2023 and 2025** remains mandatory before external validation. No final target search is authorized by this reservation.
