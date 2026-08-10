# OrbitTrace multiscale-consensus multiplicity v15 — target-excluded development protocol

## Purpose

v15 is a new successor after v13 and v14 failed their preregistered low-cardinality ranking-robustness gates. It targets the remaining mechanism directly: multiplicity ordering can vary with episode cardinality even when the family universe, recovery count, precision, and score geometry remain valid.

v15 does not modify or rescue frozen #839/v8, v13, or v14. SonotaCo 2013/2014 is scientifically exposed and unavailable for successor development. MAARSY and OrbitTrace target information/region remain inaccessible.

## Single successor rule

For a nominal local episode cap `K`, define three deterministic nested cardinalities:

- `K1 = K`;
- `K2 = max(4, floor(3K/4))`;
- `K3 = max(4, floor(K/2))`.

At each nested cardinality, use the exact frozen v5 multiplicity family score and exact frozen multiplicity ordering rule. No window, family, proposal, Brown geometry, multi-anchor geometry, multiplicity formula, or event-distance rule changes.

For each recurrent family, let `r1`, `r2`, `r3` be its zero-based multiplicity ranks at `K1`, `K2`, `K3`. Define

`R15 = median(r1, r2, r3)`.

The v15 order is ascending by:

1. `R15`;
2. full-cap rank `r1`;
3. three-quarter-cap rank `r2`;
4. half-cap rank `r3`;
5. stable family ID.

No coefficient is fitted. No scale is selected after results. All three scales have equal ordinal weight by the median operation.

## Development stress grid

Nominal stress caps remain exactly the existing portability grid:

- 128;
- 96;
- 64;
- 32.

Therefore the complete required multiplicity-cap set is fixed before execution:

- nominal 128: `[128, 96, 64]`;
- nominal 96: `[96, 72, 48]`;
- nominal 64: `[64, 48, 32]`;
- nominal 32: `[32, 24, 16]`.

Unique required caps: `[16, 24, 32, 48, 64, 72, 96, 128]`.

The already-frozen valid v13 r3 artifacts from workflow run `31356056453` provide caps 32, 64, 96, and 128. Missing caps 16, 24, 48, and 72 must be generated with the same target-excluded GMN 2020/2021 scanner and the same adaptive episode construction used by v13, changing only the requested cap. Their multiplicity ranking must be frozen before labels are consulted, as in frozen v5/v13 timing.

No cap may be chosen as a model after results.

## Rank-before-label boundary

The v15 consensus ranker may read only:

- family IDs;
- multiplicity rankings for the eight frozen caps;
- family-score metadata needed to prove the exact episode cardinalities/universe;
- source/provenance summaries stating that labels entered only after each component ranking existed.

The ranker must freeze all four nominal v15 consensus orders before any known-shower evaluation payload is made available to the evaluator.

The evaluator may then reuse the frozen direct-v5 target-excluded known-shower matching payload solely to recompute ranks/metrics for the already-frozen v15 orders.

## Firewall

Forbidden throughout v15 development:

- SonotaCo 2013/2014 scientific rows, labels, families, scores, comparator outputs, or result-guided rules;
- MAARSY scientific data;
- OrbitTrace target identity, coordinates, region, or members;
- changing proposal generation or recurrent-family construction;
- changing the 10-degree local window;
- changing Brown or multi-anchor score definitions;
- altering multiplicity after a nested-cap ranking is generated;
- choosing nested fractions, weights, or gates after evaluation.

The source branch starts from pre-external commit `c9d6c44704013ba0c9430100e98a29a56b453304`.

## Integrity gates

All must pass:

1. all eight cap inputs contain exactly the same 92-family universe and exact family membership;
2. existing caps 32/64/96/128 exactly match the valid v13 r3 ranking identities;
3. newly generated caps 16/24/48/72 use the identical frozen v5 proposal/family universe and requested exact episode cardinality for every scored family/year;
4. Brown-equivalence difference is <= `1e-10` at every newly generated cap;
5. every nominal v15 order contains exactly the same 92 families once;
6. each v15 family consensus score equals the mathematical median of its three component ranks;
7. all four v15 orders are frozen before labels/evaluation are opened;
8. no SonotaCo 2013/2014, MAARSY, target-region, or OrbitTrace target access occurs.

## Full-cardinality preservation gate

Because v15 intentionally changes even the nominal-128 order, it must preserve the established full-cardinality method rather than gain robustness by sacrificing ordinary performance.

Relative to the exact direct-v5 cap-128 multiplicity reference:

1. v15-128 recovered@100 must be at least the direct-v5 recovered@100;
2. v15-128 MRR must be at least `0.95 * direct-v5 MRR`;
3. v15-128 top-100 dominant precision may fall by at most `0.05` absolute;
4. qualified-known-shower count must be unchanged.

No full-cardinality gate is tuned after execution.

## Low-cardinality robustness gates

Use the frozen v15 nominal-128 metrics as the v15 reference. For **each** nominal cap 96, 64, and 32:

1. recovered@100 >= `ceil(0.90 * v15-128 recovered@100)`;
2. MRR >= `0.90 * v15-128 MRR`;
3. top-100 dominant precision >= `0.50`;
4. top-100 dominant precision loss from v15-128 <= `0.05` absolute;
5. qualified-known-shower count equals v15-128.

These retain the same low-cardinality tolerance used for v13/v14; they are not relaxed after those failures.

## Decision rule

- all integrity gates, all full-cardinality preservation gates, and all three lower-cap robustness panels pass:
  `PASS_MULTISCALE_CONSENSUS_V15_TARGET_EXCLUDED_DEVELOPMENT`
- otherwise:
  `FAIL_MULTISCALE_CONSENSUS_V15_TARGET_EXCLUDED_DEVELOPMENT`

A pass freezes v15 only for later independent validation. It does not authorize SonotaCo reuse, MAARSY access, OrbitTrace target access, or a literature-superiority claim.
