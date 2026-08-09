# OrbitTrace P7 per-year immutable-seed evidence-budget protocol

## Status

Preregistered after authoritative P6 development returned `FAIL_BIDIRECTIONAL_RELIABILITY_MEMBERSHIP_P6_NO_GO` in workflow `31294731265`.

P7 is not a new detector. It is an artifact-only conservative subset of exact frozen P6 membership. It does not refit, rescore, regenerate geometry, rerank families, change any probability/reliability threshold, or add an event that P6 did not already assign.

## Immutable input

P7 requires the exact canonical P6 artifact from workflow `31294731265`:

- artifact id `9032590228`;
- artifact ZIP digest `sha256:3b55fa59d3a92802f2ee7802101e6ca67eac8b6f4a026d4d3aedf1f1a68ebffa`;
- P6 membership SHA `40b0b720ef37427bc2d89aeb71c145683cbc69eff9b56ac5516e87fc34348ff6`;
- P6 decisions SHA `5e76bbf2fd75acdf1d1bc770dc3c60de338a6388524c956544afe4c1aabc8490`;
- exact promoted-v8 226-family order/rank.

No OrbitTrace target identity, coordinate, member, historical target result, comparator result, external-validation result, or event in solar longitude 20°–55° may be accessed.

## Pretruth structural diagnosis

After P4/P5/P6, every substantive development gate except qualified-match non-regression passes, while qualified matches remain fixed at 92/95 despite reducing additions from 25,706 (P4) to 24,946 (P5) to 21,626 (P6).

The exact P6 pretruth membership remains expansion-dominated:

- median P6 additions / immutable-v8 seeds per family is about 1.91;
- 162/226 families have more additions than immutable seeds in total;
- 21,133 of the 21,626 retained P6 additions lie in those 162 families;
- some families have more than ten additions per immutable seed.

This indicates that the next defensible refinement is not another geometric threshold. It is an evidence-budget constraint preventing unlabeled pseudo-members from numerically overwhelming the recurrent seed evidence that established the family.

## Sole P7 rule: per-target-year immutable-seed evidence budget

For each P6 family `f` and each target year `y` in {2022, 2023}:

1. Reconstruct the exact immutable-v8 seeds as P6 `event_ids` minus P6 `p2_added_event_ids`.
2. Let `K(f,y)` be the number of immutable-v8 seeds whose event ID belongs to year `y`.
3. Consider only the exact frozen P6 assignments to family `f` with `target_year = y`.
4. Retain at most `K(f,y)` additions.
5. If more than `K(f,y)` P6 assignments exist, retain the strongest already-frozen assignments by the deterministic order:
   - higher frozen responsibility first;
   - then higher frozen probability;
   - then lexicographically smaller event ID.
6. Dropped events are not reassigned. Family rank/order, immutable seeds, P6 eligibility, P3/P4/P5 gates, and every detector/model quantity remain unchanged.

The budget ratio is exactly one because P7 encodes the structural rule **unlabeled expansion may not outvote the immutable recurrent evidence within the same survey year**. It is not a fitted scalar and is not chosen from known-shower outcomes.

A total-family cap is not an eligible alternate P7 configuration because it can still allow one target year's pseudo-members to overwhelm that same year's immutable seed evidence. The per-year rule is the sole primary P7 configuration.

No multiplier, quantile, offset, relaxed cap, alternate sort, family exception, reassignment, or threshold search is eligible after P7 truth is observed.

## Exact frozen pretruth output

Applying the sole P7 transform to the exact P6 artifact must produce exactly:

- P6 input additions: 21,626;
- P7 retained additions: 4,463;
- dropped P6 assignments: 17,163;
- families still gaining members: 214;
- budget-binding family-year cells: 283;
- families with at least one binding year: 174;
- P7 membership canonical SHA-256: `c68dcf21761cdad3048508902a7382039ea543df5b58a6b95a094c7c17f2db7a`;
- P7 decisions canonical SHA-256: `4ffb9a4a4735788322825aaa24a1adee50ac7f5d13d0aba61c579d4b7b206ba5`.

These values are derived only from the immutable P6 pretruth artifact and must be regenerated and verified before known-shower truth is reopened.

## Truth firewall

P7 membership/decisions are frozen and hashed before any known-shower label value is read. Truth evaluation uses only the unchanged target-excluded GMN 2022/2023 evaluator. Solar longitude 20°–55° remains excluded.

## Immutable development gates

P7 passes only if all integrity gates pass and all substantive gates inherited unchanged from P2–P6 pass:

- exact promoted-v8 baseline reproduced;
- exact 226-family order and every immutable v8 seed preserved;
- P7 membership and decisions equal the preregistered hashes above;
- every retained family-year addition count is <= that family-year's immutable-v8 seed count;
- deterministic responsibility/probability/event-ID selection reproduced exactly;
- qualified known-shower matches >=95;
- recovery@100 >=58;
- top-100 dominant precision >=0.65;
- macro F1 >=0.2536657194465356;
- large-shower mean recall >=1.5 × exact-v8 large-shower mean recall;
- large-shower mean precision >=0.85;
- expansion is nonvacuous.

PASS token: `PASS_YEAR_SEED_BUDGET_MEMBERSHIP_P7_DEVELOPMENT`.

FAIL token: `FAIL_YEAR_SEED_BUDGET_MEMBERSHIP_P7_NO_GO`.

A genuine FAIL closes this exact configuration. Later parallel/exploratory branches are not second-chance promotion routes.

## Downstream hierarchy

Only a genuine P7 development PASS may proceed to a separately frozen matched Sugar/HDBSCAN benchmark. Promotion still requires `SPARSE_STREAM_SUPERIORITY` against both Sugar and HDBSCAN in both matched SonotaCo 2023 and 2025 panels, followed by pristine no-retuning external validation, before any target-containing final search.
