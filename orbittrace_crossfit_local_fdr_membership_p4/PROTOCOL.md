# OrbitTrace P4 — frozen cross-fitted reciprocal local-background-FDR membership

## Status and activation

P4 is a new target-free successor architecture frozen only after P3 produced an immutable target-excluded scientific no-go and before any P4 scientific execution.

P4 may execute only after the P3 immutable-result finalizer verifies that authoritative P3 run `31291214704` returned genuine `FAIL_CROSSFIT_SEED_FLOOR_MEMBERSHIP_P3_NO_GO` with every P3 integrity/firewall gate intact. A technical/integrity ambiguity in P3 does not authorize P4.

P3's pre-frozen literature, MAARSY and final-target routes remain dormant because P3 failed development. P4 receives no result from those unopened routes.

No OrbitTrace target coordinate, member, identity, prior target rank/recovery, target activity profile, withheld reference or event from solar longitude 20°–55° may influence P4.

## Motivation fixed from allowed target-excluded evidence

Promoted v8 preserves catalogue coverage and high precision but has incomplete membership. The membership successors established the following target-excluded facts:

- P1 raised macro F1 from `0.1736657194465356` to `0.351168136248689` but over-expanded enough to reduce qualified/recovery endpoints.
- P2 raised macro F1 to about `0.622` and large-shower recall strongly, but 247,123 non-seed assignments collapsed qualified matches and precision.
- P3 introduced family-level cross-fitting and reduced additions to 36,742, preserving recovery@100 at 58 and raising macro F1 to `0.471038167294719`, but qualified matches still fell 95→90 and large-shower precision was `0.8081618015600882`, below the frozen 0.85 gate.

The structural weakness is identifiable without known-shower labels: P3's reliability rule constrains a **fraction** of local negatives above the weakest held-out seed score, but each local non-seed window contains thousands of events. A small tail fraction can therefore correspond to many expected background proposals. P3 also compares a held-out seed floor produced by a family-excluded fold model to candidate probabilities produced by a different final all-family model.

P4 changes those two structural features rather than tuning P3's observed thresholds: every candidate is scored only by the family-excluded cross-fit model that also scores that family's held-out recurrent seeds, and acceptance is calibrated by a deterministic reciprocal local-background exceedance estimate that scales with the number of candidate/background events.

## Immutable core, rank and base representation

P4 preserves exactly:

- promoted-v8 recurrent primary cores and 226-family multiplicity order;
- original v8 seed IDs, which never move;
- P2 observation feature `d_obs`: opposite-year source-seed OAS Mahalanobis distance in the frozen four-dimensional residual geometry;
- P2 orbital feature `d_orb`: minimum exact Southworth–Hawkins D_SH to immutable opposite-year source seeds;
- exact ±5° target-year local non-seed window;
- exclusion of every original v8 seed from the non-seed background/candidate universe;
- >=128 local non-seed events per family-direction;
- family-direction training weights totaling 0.5 on positives and 0.5 on negatives;
- `StandardScaler` plus L2 `LogisticRegression(C=1.0, solver='lbfgs', max_iter=1000, tol=1e-10, fit_intercept=True, class_weight=None)`;
- no recursive growth, no refit from additions, no rank change.

Known-shower labels remain forbidden until the complete P4 membership payload is frozen.

## Deterministic family cross-fitting

Use the exact P3 fold rule unchanged:

`fold(family_id) = int.from_bytes(SHA256(family_id UTF-8)[:8], 'big') mod 5`.

For each held-out fold, fit exactly one P2-identical classifier using only directions whose family is in the other four folds. No training row from a held-out family may enter that fold model.

For every held-out family-direction, the same family-excluded fold model scores:

- all immutable target-year recurrent seeds of that family;
- every target-year local non-seed event in its exact ±5° window.

There is **no final all-family classifier** in P4. Thus seed calibration and candidate scoring are always on the same model/probability scale and held-out with respect to family identity.

## Deterministic reciprocal calibration/proposal split

For a held-out family-direction `fd`, order all local non-seed IDs by the ascending tuple

`(SHA256('P4-SPLIT|' + family_id + '|' + source_year + '|' + target_year + '|' + event_id), event_id)`.

Assign alternating ordered IDs to split 0 and split 1. Because every direction already requires >=128 local non-seeds, each split necessarily contains >=64 events. Feature values, model scores, labels and outcomes do not enter the split.

Each split acts once as proposal and once as calibration:

- side `0 <- 1`: split 0 is proposed; split 1 calibrates background exceedances;
- side `1 <- 0`: split 1 is proposed; split 0 calibrates background exceedances.

No event is proposed and calibrated in the same reciprocal side.

## Frozen local-background false-discovery estimate

Let `s(x)` be the family-excluded fold-model probability for event `x`. For a reciprocal side with proposal set `P`, calibration set `C`, and candidate score threshold `t`, define:

- `R(t) = #{x in P : s(x) >= t}`;
- `B(t) = #{x in C : s(x) >= t}`;
- `FDRhat(t) = ((1 + B(t)) / |C|) * |P| / max(1, R(t))`.

The `+1` is a frozen conservative pseudo-count. This is an empirical local-background/target-decoy style false-discovery estimate, not a claim that the local non-seed set is pure background or that exact frequentist FDR control holds under all dependence structures.

The P4 target is fixed at `q = 0.05` and is not searched.

For each held-out family-direction, also compute

`seed_median_fd = median{s(seed) : immutable target-year recurrent seed}`.

For each reciprocal side independently, consider only thresholds equal to an observed proposal score. Among thresholds satisfying both

1. `FDRhat(t) <= 0.05`, and
2. `t <= seed_median_fd`,

select the **lowest** threshold, i.e. the most permissive threshold that still satisfies the frozen local-background bound while retaining at least half of the held-out recurrent seeds on the same score scale.

A family-direction is P4-reliable only if **both reciprocal sides** have a valid threshold. If either side has no valid threshold, that entire family-direction contributes no non-seed proposal.

No interpolation, alternate q, alternate pseudo-count, alternate seed quantile or one-sided rescue is allowed after execution.

## Candidate acceptance and conflicts

For a reliable family-direction:

- an event in split 0 survives only if its fold-model probability is >= the frozen `0 <- 1` threshold;
- an event in split 1 survives only if its fold-model probability is >= the frozen `1 <- 0` threshold.

The complete per-direction split IDs, seed scores, calibration/proposal score-vector SHA-256 digests, selected thresholds, `R`, `B`, `FDRhat`, and reliability decision must be frozen before truth evaluation.

P4 deliberately removes P2/P3's cross-family odds-responsibility assignment. If a non-seed event survives for exactly one family, assign it to that family. If it survives for two or more families, leave it unassigned. There is no probability tie-break, rank tie-break or family preference. This conservative abstention rule is fixed before P4 execution.

Original v8 seeds are never contested and never move. Added events never alter any model, seed set, window, threshold, core or ranking.

## Pretruth freeze and firewall

Before any known-shower label value is indexed, P4 must durably serialize and SHA-256 freeze:

- exact promoted-v8 family IDs, seed memberships and multiplicity order;
- deterministic five-fold family assignment;
- every cross-fit model;
- for every family-direction, immutable seed-score digest and exact non-seed split IDs;
- every reciprocal calibration/proposal score-vector digest;
- every selected reciprocal threshold with `R`, `B`, `FDRhat`, seed median and reliability status;
- every surviving event/family proposal;
- every contested-event abstention;
- complete final P4 memberships and exact unchanged v8 order.

The geometry/orbit parser must remain target-excluded and label-value-free until this freeze. The later truth pass must reproduce exactly the pretruth event universe.

## One-shot target-excluded development evaluation

Development remains GMN 2022/2023 with solar longitude 20°–55° removed before labels, orbit values or candidate construction as in the existing firewall.

Use the exact promoted-v8 `evaluate_order` implementation and exact multiplicity order for both baseline and P4.

The exact large-shower subset remains the P2/P3 definition: v8-qualified target-excluded known showers with >=100 labelled events in the frozen development panel. It may not be reselected.

### Integrity gates

All must pass:

- exact v8 226-family universe/order and exact baseline metrics reproduced;
- original v8 seeds unchanged;
- exact P2 `d_obs`/`d_orb` implementation identities reproduced;
- exact five deterministic family folds and zero held-out-family leakage into its fold model;
- every direction has >=128 non-seeds and each deterministic reciprocal split has >=64;
- only the family-excluded model scores its held-out seeds and candidates;
- no final all-family model exists;
- exact q=0.05 and `+1` pseudo-count formula used;
- both reciprocal sides required for direction reliability;
- every accepted proposal meets its side's frozen threshold and has `FDRhat<=0.05` at that threshold;
- every multi-family surviving event is abstained/unassigned;
- all P4 decisions/memberships/rank frozen before truth;
- no known-shower label enters any feature, fit, calibration, threshold, proposal, conflict or membership decision;
- no parameter/feature/window/q/seed-quantile/model/threshold/variant search;
- no OrbitTrace target information or target-region event access.

### Scientific gates

P4 deliberately keeps the same substantive promotion standard used for P2/P3:

- expansion is non-vacuous;
- qualified known-shower matches >=95;
- recovery@100 >=58;
- top-100 dominant-label precision >=0.65;
- macro F1 >= `0.2536657194465356` (exact v8 +0.08);
- exact frozen large-shower mean recall >=1.5 × exact v8 large-shower mean recall;
- exact frozen large-shower mean precision >=0.85.

A pass is `PASS_CROSSFIT_LOCAL_FDR_MEMBERSHIP_P4_DEVELOPMENT`.

A scientific failure is `FAIL_CROSSFIT_LOCAL_FDR_MEMBERSHIP_P4_NO_GO` and permanently rejects this exact P4 architecture. No q, pseudo-count, split, seed-median requirement, abstention rule or other P4 setting may be changed from that outcome.

## Downstream rule

A P4 development pass still does not establish literature superiority or generalization. Before any target access it must:

1. pass a separately frozen exact-row SonotaCo Sugar/HDBSCAN benchmark under the project's pre-existing superiority standards, with all P4 pretruth decisions frozen before comparator/truth access;
2. pass a separately frozen no-retuning cross-survey/external validation on a scientifically unexposed panel;
3. then and only then enter a separately frozen final Stage-A deployment feeding the existing exact-ID-only Stage-B reveal firewall.

No failed P1/P2/P3 literature/external route may be reused as if it were a P4 validation result.