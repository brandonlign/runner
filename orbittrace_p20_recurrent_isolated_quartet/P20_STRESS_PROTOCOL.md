# OrbitTrace P20 preregistered development-stress protocol

## Status and purpose

This stress battery is frozen **before the first scientific P20 development execution is activated**. P20's protocol and exact scientific source were already frozen before the P19 result, and P19 has now returned the preregistered scientific no-go that activates P20. This stress file does not alter P20 and cannot rescue a P20 primary-development failure.

It is dormant unless exact frozen P20 first passes its original target-excluded GMN 2022/2023 development gate. Its purpose is to satisfy the fixed development-governance requirement for internal robustness before any method can be declared `FINAL_FOR_LITERATURE_TEST`.

## Immutable method identity

Every stress panel must execute the exact P20 scientific implementation already source-audited before P19 finished:

- `orbittrace_p20_recurrent_isolated_quartet/run_development.py` Git blob `6c5c8e02ac7a377ca8253f1e1fc0ad6e60e5e69f`;
- `orbittrace_p20_recurrent_isolated_quartet/P20_PROTOCOL.md` Git blob `94b732a303bd03d74317cf1101a0af5816bc06fd`.

No quartet eligibility rule, fixed4 proposal rule, component construction, component-overlap exclusion, radius, mutual-nearest rule, membership, deduplication, family order, score, threshold, or primary gate may be changed after the P20 result is known.

## Data boundary

Only the existing target-excluded GMN 2022/2023 development corpus may be used. The inherited parser removes every scientific event with solar longitude 20°–55° before thinning, labels, candidate generation, component construction, or evaluation.

No SonotaCo 2013/2014 scientific value, MAARSY scientific value, historical matched-result value, OrbitTrace target information, target-containing candidate output, or target-region scientific event may enter a stress panel.

## Fixed perturbation family

After exact inherited target exclusion and before any candidate/proposal-generation step, assign each surviving event the deterministic pseudo-uniform value

`u = uint64_be(SHA256(salt || "|" || event_id)[0:8]) / 2^64`.

Retain the event iff `u >= drop_fraction`.

Exactly four panels are frozen now:

1. salt `P20-STRESS-A`, drop fraction `0.10`;
2. salt `P20-STRESS-B`, drop fraction `0.10`;
3. salt `P20-STRESS-A`, drop fraction `0.20`;
4. salt `P20-STRESS-B`, drop fraction `0.20`.

No additional salt, fraction, resample, bootstrap seed, or thinning variant may be substituted after the primary P20 result.

Hidden known-shower labels do not enter the thinning function. The hidden-label map is restricted afterward to the retained stable event IDs solely for evaluation.

## Within-panel reconstruction

For every thinned panel, using exactly the same retained rows for both methods:

1. reconstruct the exact promoted-v8 label-free fixed4 retained quartets;
2. reconstruct exact v8 within-year components, hard recurrent families, pooled same-year centroids, multiplicity scores, and hard ranking;
3. identify P20-isolated retained quartets exactly as frozen: all four quartet event IDs must have zero overlap with all exact same-year v8 component events;
4. construct only mutual-nearest 2022/2023 isolated-quartet pairs within inherited centroid radius 1.5;
5. report exactly the eight quartet events for each P20 family, with no expansion or recursion;
6. preserve the within-panel exact v8 hard multiplicity order as the complete immutable prefix and append P20 families only afterward;
7. serialize and SHA-256 hash the full v8/P20 family payload and order before any hidden-label evaluation;
8. evaluate v8 and P20 on exactly the same retained-event universe.

The unthinned absolute v8 reference values of 226 hard families, 95 qualified matches, and recovery@100=58 are ancestry checks for primary P20 development only and are not required after intentional thinning.

## Required stress endpoints

For each panel report at minimum:

- retained event count by year and thinning-manifest SHA-256;
- v8 retained-quartet/component/hard-family counts by year;
- P20 isolated-quartet counts by year and reciprocal 4+4 family count;
- v8 and P20 qualified matches;
- v8 and P20 recovery@100;
- v8 and P20 macro F1;
- v8 and P20 top-100 dominant precision;
- annual mean F1 for 4–9, 10–24, 25–49, 50–99, and 100+ known-shower bins;
- annual combined 4–24 mean F1;
- all exact scientific-integrity and target-firewall diagnostics.

## Frozen stress PASS gate

P20 passes this robustness battery only if all of the following hold:

1. every integrity and target-firewall check passes in all four panels;
2. every panel has a nonempty v8 hard-family universe and a nonempty P20 reciprocal-isolated-quartet path;
3. P20 qualified matches are at least the within-panel v8 qualified matches in all four panels;
4. P20 recovery@100 is at least the within-panel v8 recovery@100 in all four panels;
5. because P20 appends all soft families after the complete v8 hard prefix, P20 top-100 dominant precision is equal to within-panel v8 to numerical tolerance `1e-12` in all four panels;
6. P20 macro F1 is strictly greater than within-panel v8 macro F1 in all four panels;
7. combined 4–24 mean F1 is strictly greater than within-panel v8 in **both 2022 and 2023 in all four panels**;
8. 4–9 mean F1 is strictly greater than within-panel v8 in both years in at least **three of four** panels, and no panel/year has a 4–9 mean-F1 decrement below `-0.02`.

This is a robustness/non-regression gate, not a second opportunity to adjust P20 or demand its exact primary +0.05 effect size under artificial missing-data perturbation.

The only PASS is `PASS_P20_PREREGISTERED_THINNING_STRESS`. Any power-eligible failure is `FAIL_P20_PREREGISTERED_THINNING_STRESS` and prevents P20 from being declared final under this development path. The stress result may not be used to alter P20 and rerun this same battery as fresh evidence.

## Power and interpretability

If thinning leaves a year with zero evaluable 4–9 known showers or no hard recurrent-family universe, that panel is structurally uninterpretable rather than favorable. Such a condition cannot be waived to produce a stress PASS.

## Downstream boundary

Even a P20 primary-development PASS plus stress PASS does not itself authorize the permanent SonotaCo 2013/2014 literature test. The project must first explicitly declare one exact method `FINAL_FOR_LITERATURE_TEST` and freeze its candidate-specific SonotaCo parser/transport, pairwise common-row construction, same-information Sugar/HDBSCAN interfaces, membership/ranking, bootstrap, provenance, verdict rules, and target firewall.

Only the already-frozen literature-superiority PASS may activate MAARSY 2020/2021 no-retuning external validation. Only the already-frozen external-generalization PASS may authorize the final blind target-containing search.
