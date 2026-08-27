# OrbitTrace P9 — bidirectional recurrent-reliability membership

## Status and precedence

P9 is the sole primary successor to the authoritative P8 no-go from workflow `31296889081` / artifact `9033444168`.

The P9 contingency was recorded **before the P8 scientific result** in PR #653 comment `5230013045`, while the authoritative P8 workflow was still inside its target-excluded scientific computation. The design therefore did not use P8 known-shower outcomes, comparator values, external values, target-region events, or OrbitTrace target information.

P9 remains in the exact v8→P2→P3→P4→P5→P6→P7→P8 lineage. It is not a detector restart and introduces no new numeric threshold.

## Pretruth rationale

Immutable P6 pretruth cross-fit/membership state showed:

- 226 recurrent v8 families / 452 cross-year directions;
- 218 families have both reciprocal directions satisfying the inherited P3 reliability boolean;
- 5 families have neither direction reliable and therefore already contribute no membership growth;
- only 3 families have exactly one reliable direction;
- those 3 one-sided families nevertheless contributed 3,320 / 24,945 = 13.309...% of P6 nonseed assignments (1,272, 1,185, and 863 additions), all into the target year of the sole reliable direction;
- the failed reciprocal directions had local-negative-tail rates 0.19413, 0.14317, and 0.14199, while the accepted directions had 0.05766, 0.09858, and 0.07949 under the already-frozen P3 `<=0.10` reliability criterion.

No known-shower label was used in those counts. Structurally, a method whose defining evidence is recurrence across years should not allow a large one-year membership halo for a recurrent family when the reciprocal core-to-year generalization fails the method's own already-frozen reliability test.

## Sole P9 scientific change

Exact P8 is preserved except for one family-level prerequisite on **nonseed membership growth**.

For family `F` with the two existing P3 reliability records `2022→2023` and `2023→2022`:

- if **both** direction records have `reliable == True`, run exact P8 proposal scoring in both directions unchanged;
- otherwise, neither direction of `F` may contribute a new nonseed proposal.

Immutable v8 seed members are never removed. The family remains in the exact same v8 family universe and exact multiplicity rank regardless of the P9 growth veto.

P9 does **not** require equal numbers of additions in the two years and does not impose a symmetry ratio, cap, minimum growth, or any new score threshold. Bidirectional reliability is only a prerequisite for allowing the existing P8 halo-growth machinery to operate.

## Inherited science — unchanged

P9 preserves exactly:

- promoted v8 226 recurrent family cores, seed members, and multiplicity ranking;
- P2 two-view `[d_obs, D_SH]` representation;
- ±5° local-negative windows and >=128 negatives per direction;
- deterministic P3 five-fold family exclusion;
- P3 per-direction reliability: >=4 held-out recurrent seeds, minimum seed probability strictly >0.5, and local-negative tail at that inherited minimum seed floor <=0.10;
- P4 coordinate-wise held-out-seed envelope;
- P5 joint support by one actual held-out recurrent-seed vector;
- P6 use of the same held-fold model to set the direction floor and score its candidates / produce odds;
- P8 candidate floor `k=max(1,floor(0.10*(n+1)))` using the inherited P3 0.10 scale;
- unit-background responsibility >0.5;
- no recursive growth, refit, recentering, or reranking;
- all original v8 seeds preserved.

No parameter sweep, family-specific exception, rescue rule, truth-conditioned choice, or alternate P9 configuration is eligible after activation.

## Frozen development gates

All substantive gates remain unchanged:

1. qualified known-shower matches >=95;
2. recovery@100 >=58;
3. top-100 dominant precision >=0.65;
4. macro F1 >= v8 macro F1 +0.08;
5. large-shower mean recall >=1.5× v8;
6. large-shower mean precision >=0.85;
7. expansion non-vacuous and every exact-source / pretruth-freeze / target-firewall integrity gate passes.

Additional P9 integrity-only requirements are frozen before truth:

- the pretruth family-reliability pattern reproduces exactly 218 bidirectionally reliable, 3 one-sided, and 5 zero-sided families;
- every surviving nonseed proposal belongs to a family whose two reciprocal P3 reliability records are both true;
- no v8 seed, family identity, or ranking changes.

## Downstream hierarchy

A P9 development PASS does not authorize target access.

The exact frozen P9 method must next establish sparse-stream superiority independently against **both Sugar and catalogue HDBSCAN in both SonotaCo 2023 and SonotaCo 2025** under the already-precommitted exact-row pairwise transport protocol. Broad superiority is supplementary only.

Only after all four required sparse comparisons pass may the untouched no-retuning MAARSY 2020/2021 external transport be opened, retaining its previously frozen power/effect gates. Only after a powered external PASS may the final method-agnostic target-containing search be opened.

Solar longitude 20°–55° and all OrbitTrace target information remain inaccessible throughout P9 development, matched literature comparison, and external validation.