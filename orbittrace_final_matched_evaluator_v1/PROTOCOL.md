# OrbitTrace final matched evaluator v1 — preaccess freeze

## Scope

This protocol freezes the **truth-opening evaluation mathematics only** for the permanent SonotaCo 2013/2014 matched literature test. It contains no SonotaCo transport, archive path, event value, known-shower value, comparator output, final-candidate output, MAARSY value, target-region event, or OrbitTrace target information.

It implements the already-frozen requirements in `orbittrace_governance/FINAL_LITERATURE_TEST_POLICY_V1.md`: pairwise common-row universes, candidate-budget parity, one primary member set, one-to-one candidate↔known-shower scoring, broad/sparse effect-size routes, and a 10,000-replicate cross-year bootstrap.

## Evaluation-unit floor

For one comparator × year pair, after the exact common-row manifest is frozen and both method outputs are frozen, the known-shower evaluation universe consists of every non-sporadic known-shower label having **at least 4 rows** in that exact pairwise common-row universe.

Labels with 1–3 surviving rows are preserved in provenance but are below the minimum scientifically scoreable shower unit and do not enter superiority metrics. This floor is fixed before final truth access and is identical for OrbitTrace and the comparator.

Size strata use the exact surviving row count on that pairwise common universe:

- `4-9`
- `10-24`
- `25-49`
- `50-99`
- `100+`

Combined sparse `4-24` is the ordinary mean over all eligible 4–24 shower units, not an unweighted mean of the two stratum means.

## Candidate-budget parity

For each comparator/year:

1. Let `B` be the number of frozen comparator families with at least one exact common-row member in that year.
2. Comparator scoring uses all `B` such families.
3. Filter the frozen OrbitTrace global order to families having at least one exact common-row member in that year and take the first `B`.
4. If OrbitTrace has fewer than `B`, use every available OrbitTrace family; no padding is allowed.

Family members outside the exact pairwise common-row manifest are ignored for that pairwise evaluation and may not contribute to overlap, precision, or recall.

## One-to-one assignment

OrbitTrace and the comparator are assigned to known showers **separately** by maximum-total-membership-F1 bipartite matching.

For one method:

- left nodes: every eligible known shower;
- right nodes: every budget-eligible frozen family plus one dummy unmatched node per known shower;
- real edge weight: ordinary event-membership F1 between that frozen family member set and that known shower on the exact common-row universe;
- dummy weight: zero;
- each family can match at most one shower;
- each shower can match at most one family;
- a real assignment with exact F1=0 is reported as unmatched;
- unmatched showers receive precision=recall=F1=0.

The solver is `scipy.optimize.linear_sum_assignment` on the negative augmented weights. Exact positive-F1 ties receive a deterministic solver-only perturbation `<1e-12` favoring, in order, earlier frozen family rank and then lexically earlier known-shower label. **Reported F1/precision/recall use the unperturbed values.** The perturbation can resolve an exact numerical tie but cannot create a positive score or change a non-tied scientific score.

This rule prevents one broad family from counting as multiple shower recoveries and prevents multiple fragments of one shower from counting as multiple scientific recoveries.

## Point metrics

For each method/year, compute from the one-to-one per-shower records:

- macro F1 across all eligible shower units, including unmatched zeros;
- mean F1 for each nonempty size stratum;
- mean F1 for combined 4–24;
- number of shower units with assigned F1 > 0.5.

The broad and sparse point gates are then evaluated exactly as frozen in `FINAL_LITERATURE_TEST_POLICY_V1.md`.

A sparse route cannot pass a year if either its 4–9 or 4–24 truth subset is empty. A broad route requires at least two nonempty size strata because the route requires two strata with >=0.10 improvement.

## Bootstrap

The one-to-one assignments are **held fixed** during uncertainty resampling. The bootstrap estimates uncertainty over the population of known-shower/year evaluation units; it does not rerun clustering, family matching, or method selection.

For each comparator independently:

- root seed: integer `20260809`;
- deterministic comparator-specific seed: first 8 bytes of SHA-256 of `"20260809|<comparator_id>|FINAL_MATCHED_BOOTSTRAP_V1"`, interpreted unsigned big-endian and reduced modulo `2**32`;
- replicates: exactly 10,000;
- resampling strata: **test year × frozen shower-size stratum**;
- within every nonempty stratum, sample with replacement exactly the original number of shower units in that stratum;
- concatenate all sampled units from both years;
- broad statistic: ordinary pooled mean of `(OrbitTrace F1 - comparator F1)` over all sampled shower/year units;
- sparse 4–9 statistic: ordinary pooled mean delta over sampled 4–9 units;
- sparse 4–24 statistic: ordinary pooled mean delta over sampled 4–9 and 10–24 units;
- lower bound: NumPy linear 2.5th percentile of the 10,000 replicate statistics.

Because sampling preserves every nonempty year×size stratum count, a nonempty sparse stratum cannot disappear by chance in a replicate.

Broad uncertainty passes iff pooled macro-F1 advantage lower bound >0. Sparse uncertainty passes iff both pooled 4–9 and pooled 4–24 advantage lower bounds >0.

## Final route logic

For one comparator, `broad` survives only if its broad point gates pass in **both 2013 and 2014** and its broad bootstrap lower bound is >0.

`sparse` survives only if its sparse point gates pass in **both 2013 and 2014** and both sparse bootstrap lower bounds are >0.

The final project literature verdict requires the **same route** to survive against both frozen comparators:

- broad against Sugar and HDBSCAN → `PASS_FINAL_BROAD_CATALOGUE_SUPERIORITY`;
- sparse against Sugar and HDBSCAN → `PASS_FINAL_SPARSE_STREAM_SUPERIORITY`;
- otherwise → `FAIL_FINAL_LITERATURE_SUPERIORITY`.

Integrity failure at any earlier pairwise stage returns `INVALID_FINAL_LITERATURE_TEST_INTEGRITY` and performance is not interpreted.

## Freeze boundary

The source accompanying this protocol may be tested only on synthetic fixtures before final access. Candidate/comparator adapters may serialize their already-frozen outputs into this evaluator's schema after `FINAL_FOR_LITERATURE_TEST`, but they may not change any rule in this protocol.
