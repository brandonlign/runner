# Fixed4 persistence rank-fusion prospective validation

## Status

Frozen before any 2019–2021 fixed4 score, quartet, component, family, or ranking is computed.

## Method

The fixed detector core and catalogue wrapper are inherited byte-for-byte from scanner source SHA-256
`fa18a19c08c6824c66606cbd92095dc3605cbcc30f17a468c9e525e7c6ff4a62`.

Only the final family ordering is extended. For a panel containing `N` preserved families:

- `r_p`: one-based persistence rank;
- `r_s`: one-based mean-year-strength rank;
- frozen weight `w = 0.020`;
- ascending fusion score:

`F = 0.98 * r_p / N + 0.02 * r_s / N`.

Ties are resolved by persistence rank, then mean-strength rank, then stable family identifier.

No detector distance, calibration, quartet-retention rule, component graph, family linkage, label-matching rule, eligibility rule, or persistence ranking changes.

## Prospective panel

- complete GMN months January 2019 through December 2021;
- solar longitude 20°–55° removed before label normalization;
- exact fixed4 scanner transport and quality filters;
- known-shower eligibility: at least eight labeled events in total and at least four in every panel year;
- OrbitTrace interval and members unavailable.

The exact source files, event counts, eligible labels, and hashes must be frozen in the preceding score-free input audit before scoring begins.

## Compared rankings

Exactly two rankings may be evaluated:

1. inherited `persistence`;
2. frozen `persistence_strength_fusion_w0020`.

No other candidate, alternative weight, sensitivity weight, strength statistic, tie-break, or fallback ranking may be computed.

## Primary endpoints

Using the inherited qualified known-shower family matches:

- recovered eligible labels at rank <=100;
- recovered eligible labels at rank <=500;
- mean reciprocal rank;
- dominant-label precision among top-100 families.

The qualified best-match family for each label must remain invariant across rankings; only family order may change.

## Prospective pass gates

`PASS_PERSISTENCE_RANK_FUSION_PROSPECTIVE_VALIDATION` requires all of:

1. fusion recall@100 is at least persistence recall@100;
2. fusion recall@500 is at least persistence recall@500;
3. fusion mean reciprocal rank is strictly greater than persistence mean reciprocal rank;
4. fusion top-100 dominant precision is no more than 0.05 below persistence;
5. at least one eligible label changes rank under fusion;
6. every scanner, blindness, input, component, family-universe, and match-invariance integrity gate passes.

Otherwise the verdict is
`FAIL_PERSISTENCE_RANK_FUSION_PROSPECTIVE_VALIDATION`.

## Decision boundary

A pass freezes the rank fusion as the revised generic catalogue ranking and authorizes only one separately frozen target-free OrbitTrace catalogue application using the same scanner and weight. It does not guarantee OrbitTrace recovery or rewrite the historical discovery chronology.

A failure rejects this rank fusion. No alternate weight, additional temporal panel, post-result tie-break change, relaxed gate, or OrbitTrace application is authorized for this formulation.
