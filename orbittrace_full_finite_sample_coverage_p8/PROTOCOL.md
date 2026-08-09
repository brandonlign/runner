# OrbitTrace P8 — full finite-sample coverage held-seed floor

## Status and precedence

This is the **sole primary successor** to the authoritative P7 no-go (`31295871142`). It is frozen only after that result. P7 failed solely because qualified known-shower matches remained 92 versus the immutable v8 baseline 95; every other substantive development gate passed. No target-region event, OrbitTrace target information, external panel, or matched-literature endpoint is available to P8 development.

P8 remains in the same v8→P2→P3→P4→P5→P6→P7 membership lineage. It is not a detector restart.

## Pretruth rationale

Before P7 truth evaluation, P6 pretruth diagnostics established that expansion burden was concentrated in high-support directions and strongly associated with the already-frozen P3 local-negative-tail statistic. P7 used only the second held-seed order statistic once `n>=19`, corresponding to exclusion probability `2/(n+1)<=0.10`. That rule affected 50/439 reliable directions but left most of the finite-sample exclusion budget unused for larger `n`.

The stronger rule below was derived before P7 truth from the same exchangeability argument. It introduces **no new fitted or searched constant**: the coverage level is exactly the inherited P3 negative-tail ceiling `alpha=0.10`.

Pretruth P6 support counts show why this is non-vacuous: 27 reliable directions have a permissible rank above 2, 11 have rank at least 5, and the largest permitted rank is 26. These counts use seed counts only, never known-shower labels.

## Sole P8 change

Everything in exact P7 is preserved except the candidate membership-floor order statistic.

For a P3-reliable family-direction with `n` held-out recurrent-seed probabilities sorted ascending `p_(1) <= ... <= p_(n)`, define

`k = max(1, floor(alpha * (n + 1)))`, with `alpha = P3_NEGATIVE_TAIL_MAX = 0.10`.

The P8 candidate membership floor is `p_(k)`.

Consequences:
- when no held-seed order statistic can attain a <=10% finite-sample exclusion bound (`n<9`), P8 retains the inherited minimum (`k=1`);
- when the bound is feasible, `k/(n+1) <= 0.10` and `k` is the **largest** integer rank satisfying that bound;
- P8 exactly reproduces P7 rank 2 for `19<=n<=28`, but uses rank 3, 4, ... as support increases instead of arbitrarily stopping at rank 2.

No quantile is estimated from truth, no multiplier/offset is fitted, no family-specific exception exists, and no alternate P8 configuration is eligible after execution begins.

## Inherited architecture — unchanged

P8 keeps, byte-for-byte except for the stated order-statistic logic and provenance/output labels:
- exact promoted v8 226 family cores and multiplicity ranking;
- P2 observation/orbit two-view representation;
- deterministic P3 five-fold family exclusion;
- held-fold model used both to score held-out seeds and candidates (P6 correction);
- P3 reliability rule: >=4 held-out target-year seeds, minimum seed probability >0.5, local-negative tail at the inherited minimum seed floor <=0.10, >=128 local negatives;
- P4 coordinate-wise held-seed envelope;
- P5 joint support by an actual held-out recurrent-seed vector;
- unit-background responsibility >0.5;
- no recursive growth; expanded members never seed new growth;
- v8 rank remains immutable.

## Frozen development gates

The exact substantive gates remain unchanged from P2–P7:
1. qualified known-shower matches >=95;
2. recovery@100 >=58;
3. top-100 dominant precision >=0.65;
4. macro F1 >= v8 macro F1 + 0.08;
5. large-shower mean recall >=1.5x v8;
6. large-shower mean precision >=0.85;
7. non-vacuous expansion plus all exact-source, pretruth-freeze, and target-firewall integrity gates.

No gate may be weakened after P8 truth is observed.

## Downstream firewall

A P8 development PASS alone does not permit target access.

Next, the exact frozen method must establish **sparse-stream superiority separately against both Sugar and catalogue HDBSCAN in both SonotaCo 2023 and SonotaCo 2025**, using the already-fixed matched-data protocol. Broad superiority is supplementary and cannot substitute for a sparse-stream failure.

Only after matched-literature PASS may the untouched MAARSY 2020/2021 external transport be opened, with no retuning. Only after that external PASS may the final target-containing GMN search be opened. The final ranked stable event-ID payload must freeze before the sealed exact-ID reveal.

Solar longitude 20°–55° remains inaccessible throughout P8 development, literature comparison, and external validation.