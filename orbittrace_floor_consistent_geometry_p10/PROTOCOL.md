# OrbitTrace P10 — floor-consistent retained-seed joint geometry

## Status and precedence

P10 is the sole primary successor to the authoritative P9 no-go from workflow `31297949121`, successful job `93206769929`, artifact `9033947493`.

The complete P10 scientific rule was fixed **before P9 truth** in PR #659 comment `5230084892`, while the exact P9 recovery attempt was still inside target-excluded computation. P10 therefore was not chosen from P9 known-shower outcomes. The later historical comparator-firewall incident also occurred after this P10 rule was fixed, so comparator outcomes are ineligible to influence P10.

P10 remains in the exact v8→P2→P3→P4→P5→P6→P7→P8→P9 lineage. It is not a detector restart and introduces no numeric threshold.

## Pretruth rationale

The P8 finite-sample order-statistic floor and inherited P5 joint geometry were internally inconsistent in a measurable target-free way:

- 50 P3-reliable directions had P8 membership-floor rank >1;
- those directions contained 125 inherited P5 componentwise-maximal joint-support vectors;
- 71/125 of those frontier vectors scored below their own exact P8 membership floor under the same held-fold P6 model;
- every one of the 50 affected reliable directions had at least one such below-floor frontier vector;
- the probability deficits were substantive rather than floating roundoff (approximately: minimum 7.22e-6, median 5.88e-3, 90th percentile 2.87e-2, maximum 0.1375).

Those diagnostics used only frozen pretruth model/geometry state and no known-shower label values. Structurally, P8 says the low-scoring held-out seeds below its finite-sample floor should not define the candidate acceptance floor on the probability axis, yet inherited P5 still permits those same discounted seeds to enlarge the accepted `[d_obs,D_SH]` joint-support region. P10 makes the scalar and geometric support sets coherent.

P9 is inherited in full. P9 improved qualified matches from 92 to 93 but remained below the immutable v8 requirement 95, with every other substantive gate passing. That outcome activates this already-fixed P10 contingency but does not change its rule.

## Sole P10 scientific change

For each cross-year family-direction, exact P9 already has:

- held-out recurrent-seed two-view rows `xp = [d_obs,D_SH]`;
- those same held-out seeds' probabilities `pp`, scored by the exact held-fold model used by P6/P8;
- exact P8 `membership_floor` and `membership_floor_rank`.

P10 changes only the P5 **joint-support geometry** construction:

1. retain a held-out recurrent seed as a geometry-support seed iff its exact same-fold probability satisfies `pp >= membership_floor`;
2. recompute the componentwise-maximal P5 frontier from exactly those retained seed rows;
3. require each candidate to be componentwise `<=` at least one retained frontier vector in `[d_obs,D_SH]`, exactly as P5 required relative to its frontier.

The P4 coordinate-wise envelope remains exactly inherited and is still computed from the full held-out recurrent-seed set. P10 changes only the P5 joint-support set.

For P8 rank-one directions, `membership_floor` is the minimum held-out seed probability, so every held-out seed must be retained and the P5 frontier must reproduce exactly. No tolerance, epsilon, or approximate comparison is introduced; the exact stored/predict_proba float values are compared with `>=`.

## Exact P9 science inherited unchanged

P10 preserves:

- promoted v8 226 recurrent families, immutable seed members and multiplicity rank;
- P2 two-view `[d_obs,D_SH]` representation;
- ±5° local-negative windows and >=128 negatives/direction;
- deterministic P3 five-fold family exclusion;
- P3 per-direction reliability: >=4 held-out recurrent seeds, minimum seed score strictly >0.5, local-negative tail <=0.10;
- P4 coordinate-wise held-seed envelope from the full held-out seed set;
- P6 same-held-fold model for seed floor, candidate score and proposal odds;
- P8 finite-sample floor `k=max(1,floor(0.10*(n+1)))` at the inherited P3 0.10 scale;
- P9 family-level prerequisite that both reciprocal P3 reliability booleans are true before either direction may add a nonseed member;
- unit-background responsibility >0.5;
- no recursive growth, refit, recentering or reranking;
- all original v8 seeds preserved.

No alternate P10 geometry, alpha, quantile, multiplier, offset, tolerance, support-count cutoff, family-specific exception, rescue, or parameter search is eligible after activation.

## Frozen development gates

All substantive gates remain unchanged from P2–P9:

1. qualified known-shower matches >=95;
2. recovery@100 >=58;
3. top-100 dominant precision >=0.65;
4. macro F1 >= v8 macro F1 +0.08;
5. large-shower mean recall >=1.5× v8;
6. large-shower mean precision >=0.85;
7. non-vacuous expansion and every exact-source / pretruth-freeze / target-firewall gate passes.

P10 additionally requires, before truth interpretation:

- exact P9 reciprocal-reliability pattern 218 bidirectional / 3 one-sided / 5 zero-sided families;
- every retained geometry-support seed has exact same-fold probability >= its P8 membership floor;
- every P8 rank-one direction retains every held-out seed and reproduces its inherited P5 joint frontier byte-for-byte;
- exactly the 50 pretruth reliable rank>1 directions have a non-vacuous retained-seed geometry change;
- every surviving nonseed proposal is jointly supported by at least one retained held-out seed frontier vector;
- no proposal comes from a family lacking reciprocal P9 reliability;
- v8 seed IDs, family identities and rank are unchanged.

## Downstream hierarchy

A P10 development PASS does not authorize target access.

The exact frozen P10 method must next establish sparse-stream superiority independently against **both Sugar and catalogue HDBSCAN in both SonotaCo 2023 and SonotaCo 2025** under the already-precommitted strict pairwise exact-row transport protocol. Historical comparator outcomes accidentally exposed after P10 preregistration may not be used to tune, rescue or select P10; the actual P10 benchmark must be executed only after P10 development is frozen.

Only after all four required sparse comparator/year passes may the untouched no-retuning MAARSY 2020/2021 external transport be opened with its already-frozen power/effect bars. Only after a powered external PASS may the final method-agnostic target-containing search/reveal hierarchy be opened.

Solar longitude 20°–55° and all OrbitTrace target information remain inaccessible throughout P10 development, literature comparison and external validation.