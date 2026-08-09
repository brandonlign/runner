# OrbitTrace P19 preregistered development-stress protocol

## Status and purpose

This stress battery is frozen while the exact P19 one-shot GMN 2022/2023 development run is still in progress and before its scientific PASS/FAIL is known. It does not alter P19 and cannot rescue a P19 development failure. It is dormant unless exact frozen P19 first passes its original development gates.

The purpose is to satisfy the permanent development-governance requirement that a candidate survive fixed internal perturbations before it can be considered `FINAL_FOR_LITERATURE_TEST`.

## Immutable scientific method

Every stress panel uses the exact frozen P19 scientific rule and exact v8 comparator rule already committed before the primary P19 result. No triplet size, radius, recurrence rule, component threshold, score, ranking, membership, event-count threshold, gate, or target boundary may change.

The exact P19 scientific blobs remain:

- `run_development.py` Git blob `f230fc775b38df1e9d447bba33419abd5f6f6ef1`;
- `P19_PROTOCOL.md` Git blob `3be02f4fb288d784cabd7901e928db14eed6593d`.

## Data boundary

Only the existing target-excluded GMN 2022/2023 development corpus is used. The inherited parser must remove solar longitude 20°–55° before the stress transform, label normalization, candidate generation, family construction, scoring, or evaluation.

No SonotaCo 2013/2014 scientific value, MAARSY event value, exposed historical comparator result, OrbitTrace target information, or target-region event is permitted.

## Fixed perturbation family: deterministic event thinning

After the exact inherited target exclusion and before any proposal/candidate-generation step, each surviving event is independently assigned a deterministic pseudo-uniform value

`u = uint64_be(SHA256(salt || "|" || event_id)[0:8]) / 2^64`.

The event is retained iff `u >= drop_fraction`.

Exactly four stress panels are defined now:

1. salt `P19-STRESS-A`, drop fraction `0.10`;
2. salt `P19-STRESS-B`, drop fraction `0.10`;
3. salt `P19-STRESS-A`, drop fraction `0.20`;
4. salt `P19-STRESS-B`, drop fraction `0.20`.

No other salt, fraction, bootstrap seed, resample, or thinning variant may be substituted after the primary P19 result is known.

Labels do not enter the thinning function. The hidden-label map is merely restricted afterward to retained event IDs for evaluation.

## Within-panel comparison

For each of the four thinned panels:

1. reconstruct the exact label-free v8 detector, within-year components, hard recurrent families, pooled same-year centroids, multiplicity scores, and hard ranking from the retained events;
2. construct P19 soft reciprocal recurrence on those same retained events using the exact frozen P19 rule;
3. preserve the within-panel v8 hard multiplicity order as P19's immutable prefix and append only P19 soft families;
4. hash the complete pre-label v8/P19 family payload and order before any hidden-label evaluation;
5. evaluate v8 and P19 on exactly the same retained event universe.

The original absolute v8 counts of 226 families / 95 qualified matches / 58 recovery@100 are **not** required on a thinned panel because thinning intentionally changes the event universe. They remain ancestry checks on the unthinned primary run only.

## Fixed stress endpoints

For each panel, report at minimum:

- retained event counts by year;
- v8 hard-family count and P19 soft-family count;
- qualified matches for v8 and P19;
- recovery@100 for v8 and P19;
- macro F1 for v8 and P19;
- top-100 dominant precision for v8 and P19;
- annual mean F1 for the 4–9, 10–24, 25–49, 50–99, and 100+ known-shower size bins;
- combined 4–24 mean F1 by year;
- complete integrity and target-firewall diagnostics.

## Frozen stress PASS gate

P19 passes this robustness battery only if all of the following hold:

1. every integrity/target-firewall check passes in all four panels;
2. each panel has a nonempty v8 hard-family universe and a nonempty P19 soft-recurrence path;
3. P19 qualified matches are at least the within-panel v8 qualified matches in all four panels;
4. P19 recovery@100 is at least the within-panel v8 recovery@100 in all four panels;
5. because P19 appends soft families after the complete v8 hard prefix, P19 top-100 dominant precision is exactly equal to the within-panel v8 top-100 dominant precision in all four panels, up to numerical tolerance `1e-12`;
6. P19 macro F1 is strictly greater than within-panel v8 macro F1 in all four panels;
7. combined 4–24 mean F1 is strictly greater than within-panel v8 in **both 2022 and 2023 in all four panels**;
8. 4–9 mean F1 is strictly greater than within-panel v8 in both years in at least **three of four** panels, and no panel/year has a 4–9 mean-F1 decrement below `-0.02`.

This is deliberately a robustness/non-regression gate, not another opportunity to demand the exact +0.05 primary-effect size under missing-data perturbation.

The only stress PASS is `PASS_P19_PREREGISTERED_THINNING_STRESS`. Any power-eligible failure is `FAIL_P19_PREREGISTERED_THINNING_STRESS` and prevents P19 from being declared final for the literature test under this governance path. The stress result cannot be used to alter P19 and rerun the same battery as fresh evidence.

## Power / interpretability boundary

If deterministic thinning makes a year contain zero evaluable 4–9 known showers or no hard recurrent family universe, the panel is structurally uninterpretable rather than favorable. Such a condition does not waive the corresponding gate and therefore cannot produce a stress PASS.

## Downstream boundary

Even a P19 primary-development PASS plus stress PASS does not automatically open SonotaCo 2013/2014. Before the permanent one-shot literature test, the project must still explicitly freeze and declare one `FINAL_FOR_LITERATURE_TEST` candidate, including exact candidate generation, family construction, membership, ranking, matched-universe construction, Sugar and catalogue-HDBSCAN interfaces, pairwise superiority gates, provenance, and target firewall.

Only a one-shot SonotaCo 2013/2014 literature-superiority PASS may activate MAARSY 2020/2021 no-retuning external validation. Only satisfaction of the external-generalization requirement may authorize the final blind OrbitTrace search.
