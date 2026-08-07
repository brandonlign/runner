# OrbitTrace rank-consensus v10 — frozen target-excluded development protocol

## Purpose

The promoted method remains **v8 pooled-year-centroid label-free sparse-support multiplicity**. Its exact target-excluded GMN 2022/2023 development result is 226 recurrent families, multiplicity recovery@100 58/95 qualified known showers, persistence recovery@100 59/95, multiplicity top-100 dominant precision 0.6884631112636006, and multiplicity/persistence Spearman correlation about 0.51 with only 62/100 top-100 family overlap.

Subsequent recurrence-topology successors did not improve the method: one-to-one v7, reciprocal-nearest recurrence, and support-overlap v9 are preserved no-gos. Earlier support-normalized structural rerankers also failed. Therefore v10 changes **no proposal, component, family, centroid, episode, or physical score**. It asks one narrower question: can the two surviving, complementary, already-frozen label-free rankings be combined without a fitted weight and improve held-out known-shower ranking?

## Immutable scientific architecture

Everything below is inherited exactly from passed v8:

- development data: GMN 2022 and 2023 only;
- solar longitude 20°–55° removed by the frozen parser before label use;
- label-free fixed4 proposal generation;
- 4° angular / 10% speed geometry;
- first shortlist 64 and exact audit shortlist 128;
- anchor multiplicity >=2;
- at most 512 retained quartets per 10° bin;
- within-year component minimum 4 events and 2 quartets;
- v6 connected cross-year family semantics with fixed centroid-link radius 1.5;
- exact v8 pooled same-year centroid repair: union unique same-year family events, circular mean for solar longitude and Sun-centered longitude, median ecliptic latitude and speed;
- exact 128-event local episodes;
- multi-anchor v3 and Brown implementations unchanged;
- multiplicity `M=(v3/Brown)^2` unchanged;
- v8 multiplicity ranking unchanged;
- label-free persistence ranking unchanged;
- no source label, OrbitTrace information, orbital element, or target-region event may enter proposals, components, families, pooled centroids, episode construction, multiplicity, persistence, or any rank fusion.

The exact v8 family universe, multiplicity order, persistence order, and v8 metrics must be reproduced before v10 can be evaluated.

## Exactly two preregistered fusion candidates

Let `r_M(f)` be the 1-based rank of family `f` under v8 multiplicity and `r_P(f)` the 1-based rank under v8 label-free persistence.

Only these two candidates exist:

1. **rank_product**
   - sort ascending by `r_M * r_P`;
   - tie-break ascending by `r_M + r_P`, then `r_M`, then `r_P`, then stable family id.

2. **rank_sum**
   - sort ascending by `r_M + r_P`;
   - tie-break ascending by `r_M * r_P`, then `r_M`, then `r_P`, then stable family id.

Both are equal-weight, scale-free rank consensus rules. No coefficient, exponent, reciprocal-rank constant, threshold, percentile, top-k, or other parameter is fitted. No third candidate may be introduced after execution begins.

Before any known-shower label evaluation, the workflow freezes the full v8 multiplicity ranking, v8 persistence ranking, both candidate rankings, and SHA-256 digests of those ranking payloads.

## Deterministic shower-label development/validation split

After all rankings are frozen, known-shower labels may first be used only to define eligibility exactly as in the frozen multiplicity evaluator and assign eligible shower codes to one of two panels.

For each eligible shower code `s`, compute `SHA256("orbittrace-v10-label-split|" + s)` and interpret the first byte as an unsigned integer:

- even -> **development-label panel**;
- odd -> **validation-label panel**.

The split rule is fixed here before execution. Family construction and rankings do not depend on the split.

When evaluating one panel, every shower label belonging to the other panel is masked to `SPORADIC` before the frozen evaluator is called. Thus candidate selection sees only development-panel shower outcomes.

## Candidate selection using development labels only

Evaluate v8 multiplicity, v8 persistence, rank_product, and rank_sum on the development-label panel.

The development winner among the two fusion candidates is selected lexicographically by:

1. recovered qualified showers at rank 100, descending;
2. mean reciprocal rank, descending;
3. median rank, ascending;
4. fixed candidate priority: rank_product before rank_sum.

The validation-label panel remains unevaluated unless the selected candidate first satisfies both development authorization gates:

- development recovery@100 >= `max(v8 multiplicity, v8 persistence) + 1`;
- development MRR >= `max(v8 multiplicity, v8 persistence)`.

If either authorization gate fails, v10 immediately returns a scientific no-go and the validation-label panel is not evaluated.

## Validation and full-result promotion gates

If development authorization passes, evaluate only the selected candidate plus the two v8 baselines on the previously untouched validation-label panel. Then, and only then, evaluate full eligible-label metrics for reporting.

All of the following are required to promote v10:

1. validation recovery@100 >= `max(v8 multiplicity, v8 persistence) + 1`;
2. validation MRR >= `max(v8 multiplicity, v8 persistence)`;
3. full recovered@100 >= 60, strictly exceeding the passed-v8 multiplicity value 58 and persistence value 59;
4. full top-100 dominant precision >= 0.68;
5. full MRR >= 0.045531138942766655, the exact passed-v8 multiplicity MRR;
6. exact 226-family v8 universe and exact v8 baseline metrics are reproduced;
7. every inherited v8 integrity gate remains satisfied.

`PASS_RANK_CONSENSUS_V10_DEVELOPMENT` requires every integrity, development-authorization, validation, and full-result gate to pass.

Any failure yields `FAIL_RANK_CONSENSUS_V10_DEVELOPMENT`. The candidate set may not be expanded or reweighted after seeing the result.

## Claim boundary

This is development on already-exposed **target-excluded** GMN 2022/2023 only. A pass would promote a ranking successor for later independent validation; it would not authorize OrbitTrace reveal or a target-containing discovery scan. A failure leaves v8 as the promoted method.
