# OrbitTrace recurrent flow tube v2 — soft-evidence flow

## Scientific role

RFT v2 is a **new target-excluded GMN 2022 development successor** motivated by the binding RFT v1 failure and its preregistered ablations. It does not rescue or reinterpret RFT v1. RFT v1 remains permanently `FAIL_RFT_V1_GMN2022_DEVELOPMENT_VIABILITY` and GMN 2023 remains inaccessible under the v1 protocol.

RFT v1 failed with 35 retained candidates, 20 qualified matches, recovered@100 = 20, top-100 dominant precision = 0.4856598221583339, fragmentation median = 1.0, and top-100 persistence>=0.75 share = 0.22857142857142856. The preregistered `no_perturbation_persistence` ablation increased qualified matches to 133 while retaining top-100 dominant precision 0.670272900136203, showing that hard perturbation survival was a severe coverage choke point. The preregistered `no_path_ownership` ablation raised top-100 dominant precision to 0.7530672586627197 and recovered@100 to 29, showing that exclusive atom ownership also discarded plausible hypotheses. The `no_trajectory_trim` ablation was effectively neutral, so v2 retains the original trim unchanged rather than spending another degree of freedom on it.

The v2 design therefore changes the **epistemic role** of ownership and perturbation recurrence: they no longer delete hypotheses. Local flow geometry still generates the hypotheses; perturbation recurrence becomes continuous evidence used for ordering.

## Data firewall

- Development dataset: GMN 2022 only.
- Protected solar longitude 20°–55° is excluded before v2 sees events.
- GMN 2023 is inaccessible unless v2 first passes the exact development gate below and a separate held-out protocol is frozen.
- SonotaCo 2013/2014 is not accessed by v2.
- OrbitTrace target information and target-region events are inaccessible.
- MAARSY and DMS are scientifically inaccessible.
- Labels never enter atom construction, tube construction, persistence computation, trimming, deduplication, or ranking.

## Frozen inherited geometry

The following RFT v1 scientific constants and functions are inherited unchanged from frozen source blob `a5d5371f0c30a9c57ee4d8756ea41f454cd86301`:

- solar-centered radiant longitude, ecliptic latitude, geocentric speed state;
- 2° solar-longitude atom strata;
- reciprocal KNN with `KNN=4` and `MIN_ATOM=4`;
- exact pair metric and transition geometry;
- `MIN_STRATA=3`, `MIN_SPAN=6°`, `MIN_EVENTS=10`;
- 16 deterministic perturbation replicas;
- perturbation radiant sigma 0.35° and speed sigma 1%;
- persistence Jaccard match threshold 0.50;
- trajectory trim threshold 2.5;
- exact label-free trajectory fit and residual definitions.

The already-computed 17-replica UV-parallel shard artifacts from RFT v1 may be used strictly as an engineering cache. They contain both owned and unowned tube lists for replica 0 and perturbation replicas 1–16, were generated without truth, passed exact UV/parallel equivalence probes, and have all protected-data flags false. Reusing those tubes does not alter v2 science.

## v2 hypothesis universe

For every replica, use the frozen RFT v1 **unowned** tube construction: every eligible atom seeds its deterministic cheapest-successor path and downstream atom reuse is allowed. This is not an ablation after the v2 outcome; it is the sole frozen v2 hypothesis generator.

For each nominal replica-0 unowned tube:

1. Calculate perturbation persistence exactly as in v1: in each of replicas 1–16, find the maximum member-set Jaccard overlap against any unowned tube; count the replica as a survival when maximum Jaccard >= 0.50; persistence is surviving replicas / 16.
2. **Do not apply a persistence cutoff.** Persistence of 0 is a valid measured evidence value, not a deletion rule.
3. Apply the unchanged v1 trajectory trim to the nominal tube and require at least 10 retained members.
4. Calculate the unchanged geometric coherence score without multiplying by persistence:

   `coherence = log1p(n_members) * log1p(strata) / (1 + median_transition_cost + median_trajectory_residual)`.

5. Exact-member duplicates created after trimming are collapsed. For an identical trimmed member set, retain the representative with lowest `(median_transition_cost + median_trajectory_residual, tube_id)`. Its measured persistence is retained with that representative. This rule is fixed before labels.

Candidate IDs are SHA-256 prefixes of `RFT2|<sorted member IDs>`.

## Sole v2 ranking

Create two independent 1-based ranks over the deduplicated candidate universe:

- **coherence rank:** descending coherence, ties by family ID;
- **persistence rank:** descending measured persistence, ties by family ID.

The sole v2 order is equal rank-sum:

`(coherence_rank + persistence_rank, coherence_rank, family_id)`.

No fusion weight, persistence threshold, ownership quota, rank product, score exponent, candidate budget, post-hoc diversity pass, source quota, or parameter search is authorized.

## Preregistered explanatory ablations

These are descriptive only and cannot rescue a failed v2 result:

1. `coherence_only`: same v2 unowned candidate universe ordered by coherence rank alone.
2. `owned_soft_evidence`: identical soft-evidence procedure using the frozen **owned** tube lists instead of unowned lists.
3. `persistence_only`: same v2 unowned candidate universe ordered by persistence rank alone.

No ablation may replace the sole v2 order after the outcome.

## Binding GMN 2022 viability gate

The first technically valid v2 outcome is binding. PASS requires all of:

- qualified matches >= 120;
- recovered@100 >= 55;
- top-100 dominant precision >= 0.60;
- fragmentation median among recovered top-500 labels <= 3.0.

These are the same four core retrieval/precision/fragmentation gates used by RFT v1; v2 receives no relaxed performance target. Persistence is no longer a binary validity property, so v1's separate `top100 persistence>=0.75 share >=0.75` gate is not applicable to v2 and is reported descriptively instead.

If any binding gate fails, v2 terminates and GMN 2023 remains inaccessible. No alternate rank fusion, cutoff, ownership rule, perturbation treatment, or threshold may be tried as a rescue under the v2 name.

If all gates pass, v2 is frozen unchanged and only then may a separately frozen GMN 2023 held-out evaluator be authorized.
