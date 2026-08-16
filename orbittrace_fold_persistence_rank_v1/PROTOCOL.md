# OrbitTrace perturbation-persistence rank v1 — frozen protocol

## Goal
Test whether **resampling stability itself** can identify the families most likely to generalize. The exact full-data density-synchronous recurrent-EOM candidate universe is held fixed; the sole change is its order.

A GMN PASS requires total recovered@100 >= **184** (+5 over the frozen 179 winner), with no annual regression in recovered@50, recovered@100, top-100 dominant precision, MRR, or median top-500 fragmentation. A GMN PASS is only the first step and must be frozen before any SonotaCo transfer test.

## Why this is distinct
The preregistered GMN train-robustness experiment (run `31859724335`) already produced ten deterministic ~10% deletion folds and froze complete density-synchronous candidate memberships before truth. It showed the full-data +1 recovery advantage was sample-sensitive, but robustness was used only as an **audit of aggregate metrics**. It did not use cross-fold membership persistence to rank the full-data candidates.

A pre-run repository search found no prior OrbitTrace candidate ranking by Jaccard membership persistence, fold survival, or cross-perturbation membership overlap.

## Frozen evidence only
Full-data candidate universe:
- winner run `31852836840`;
- winner artifact `9238142199`;
- exact candidate count `2094`;
- winner prelabel SHA256 `efce0617a738a0372ec5b007fb87b46912accd8419f0f768829c4c0cb7d62993`;
- winner result SHA256 `ca6aeed2b82739003ea5d39b59e869df876de2962164344a938fe4935ea38711`;
- ordered-membership SHA256 `e8f374ad03e7072463118ee6440a54d96d11e3aab17202cfe336f866530224f2`;
- baseline recovered@100 = `89 + 90 = 179`.

Perturbation evidence:
- exact CV run `31859724335`;
- ten artifacts named `orbittrace-density-sync-gmn-train-cv-v1-fold-{0..9}`;
- fold assignment exactly `uint64_be(SHA256(UTF8(event_id))[0:8]) mod 10`;
- in fold `f`, that bucket was removed from both years before clustering;
- each fold artifact contains the complete pretruth density-synchronous `successor_candidates` order/memberships.

No fold is rerun. No fold definition, weight, deletion fraction, HDBSCAN setting, representation, or candidate-generation rule changes.

## Sole scientific score
For each full-data candidate `C` and fold `f`:

1. Form its surviving membership `C_f = {event in C : bucket(event_id) != f}`.
2. For every density-synchronous candidate `F` in the already-frozen fold-f prelabel, define standard Jaccard overlap:

`J(C_f,F) = |C_f ∩ F| / |C_f ∪ F|`.

3. Define `J_f(C) = max_F J(C_f,F)`. If `C_f` is empty or intersects no fold candidate, `J_f(C)=0`.
4. Exact ties in best Jaccard use lexicographically smallest immutable fold `family_id` for audit only; the score is unchanged.
5. Define one parameter-free perturbation-persistence score:

`P(C) = mean_{f=0..9} J_f(C)`.

The arithmetic mean gives every preregistered perturbation exactly equal weight. There is no overlap threshold, fold threshold, learned coefficient, fitted model, truth access, or score blending.

## Sole new order
Order the exact 2094 full-data candidates by:
1. descending `P(C)`;
2. descending original density-synchronous stability;
3. descending original ordinary HDBSCAN stability;
4. descending member count;
5. ascending immutable family ID.

The first key is the sole scientific change. No candidate may be added, removed, split, merged, filtered, or have membership changed.

## Pretruth freeze
Before any known-shower label is indexed, persist:
- exact winner/fold artifact identities and self-consistency hashes;
- exact 2094-candidate membership multiset identity to the winner;
- all ten `J_f(C)` values, matched fold family IDs, and `P(C)` for every full-data candidate;
- complete new order and ordered-membership SHA256;
- mechanism-active flag requiring the order differ from the 179 winner;
- firewall state.

## Structural gates
Require all:
1. exactly 2094 full-data candidates;
2. candidate membership/content multiset unchanged from the winner;
3. all ten fold prelabels are present, uniquely numbered 0..9, and each result verifies its prelabel SHA256;
4. every fold has `scientific_role=PRELABEL_DENSITY_SYNC_GMN_TRAIN_CV_V1`, no protected/external access, and density-sync successor candidates present;
5. every persistence score is finite and within [0,1];
6. the new order differs from the winner;
7. no catalogue/truth is loaded until the new order is durably written.

## Binding GMN success gate
PASS iff all are true:
1. total recovered@100 >= **184**;
2. 2022 recovered@50 not below winner and recovered@100 >=89;
3. 2023 recovered@50 not below winner and recovered@100 >=90;
4. top-100 dominant precision not lower in either year;
5. MRR not lower in either year;
6. median top-500 fragmentation not higher in either year;
7. every structural/source/firewall gate passes.

Anything else is FAIL.

## Transfer/generalization rule
A GMN PASS does not prove generalization. If and only if it passes, freeze the exact persistence rule before one exposed SonotaCo transfer benchmark. True external generalization still requires a genuinely untouched survey afterward.

## No rescue
If v1 fails, permanently close this exact fold-persistence rank. Do not retry after outcome with median/min/max overlap, Dice/containment instead of Jaccard, overlap thresholds, fold omission/weighting, top-k fold voting, rank blending, persistence exponents, raw-stability blends, candidate filtering, alternate perturbation fractions, new random folds, or target-guided exceptions. Any later successor must have a distinct independently motivated mechanism.
