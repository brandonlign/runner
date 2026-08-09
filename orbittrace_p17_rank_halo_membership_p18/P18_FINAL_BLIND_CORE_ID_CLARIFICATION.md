# P18 final blind exact-ID clarification — primary core IDs only

## Status

Frozen before any P18 matched result, MAARSY result, Stage-A run, Stage-B reveal, target-region access, or withheld-reference access.

This clarification removes one possible ambiguity in `P18_FINAL_BLIND_AUTHORIZATION_ADDENDUM.md` without changing its thresholds, years, ranking, or authorization prerequisites.

## Exact recovery membership object

For Stage-B recovery classification, the event-ID set associated with a ranked primary family is **only that family's immutable P17/P14 recurrent-core event-ID set frozen in Stage A**.

The P18/P15/P12 halo event-ID set is secondary characterization only. Halo-only event IDs:

- do not count toward the requirement of at least 4 exact withheld reference IDs in 2022;
- do not count toward the requirement of at least 4 exact withheld reference IDs in 2023;
- do not count toward the requirement of at least 8 exact withheld reference IDs total;
- cannot turn `NO_BLIND_RECOVERY` into `PARTIAL_BLIND_RECOVERY`;
- cannot turn `PARTIAL_BLIND_RECOVERY` into `FULL_BLIND_RECOVERY`;
- cannot change the primary family rank used for the rank <=25 / rank <=100 thresholds.

Thus Stage B tests exact withheld-ID overlap against the frozen **primary core membership** only. The halo may be reported after the primary recovery verdict is frozen, but it cannot contribute evidence to that verdict.

## Rationale and claim boundary

P18 deliberately uses halo membership for fair catalogue-membership evaluation because membership F1 is an output-quality question. The final blind goal is stricter: whether the target-free discovery engine itself independently produced and ranked a recurrent family containing the preregistered minimum exact withheld membership. Using core IDs only for Stage-B qualification keeps that discovery claim tied to the primary discovery object rather than to a secondary membership-expansion layer.

All other final-firewall requirements remain unchanged: full GMN 2022/2023 Stage A, target reference absent during Stage A, exact-ID-only Stage B, >=4 exact IDs in each year and >=8 total, FULL rank <=25, PARTIAL rank <=100, no coordinate/distance/clustering/reranking after reveal, and no target access before all authorization prerequisites pass.

This clarification must not be changed in response to any later result.
