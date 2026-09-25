# OrbitTrace P21 preregistered development-stress protocol

## Status

This stress battery is frozen while P20's one-shot development run is still in progress and before any P21 scientific execution is authorized. It is dormant unless P20 fails scientifically and exact frozen P21 then passes its own primary target-excluded GMN 2022/2023 development gate.

It cannot rescue or modify a P21 primary failure. The exact P21 method identity is already frozen:

- scientific source Git blob `a1a89caf4641320b24ae14043bf2d47b87a2455d`;
- protocol Git blob `3714675d87bbc9d3fc964d667f91fe9edca17a3c`.

## Data and target boundary

Only target-excluded GMN 2022/2023 development events may enter. The inherited parser removes solar longitude 20°–55° before thinning, singleton proposal generation, labels, components, recurrence, or evaluation.

No SonotaCo 2013/2014 scientific value, MAARSY scientific value, OrbitTrace target information, target-containing candidate output, or target-region scientific event may enter.

## Fixed deterministic thinning panels

After inherited target exclusion and before any fixed4 proposal generation, compute

`u = uint64_be(SHA256(salt || "|" || event_id)[0:8]) / 2^64`.

Retain an event iff `u >= drop_fraction`.

Exactly four panels are frozen:

1. `P21-STRESS-A`, drop fraction `0.10`;
2. `P21-STRESS-B`, drop fraction `0.10`;
3. `P21-STRESS-A`, drop fraction `0.20`;
4. `P21-STRESS-B`, drop fraction `0.20`.

No later salt, fraction, bootstrap sample, or substitute perturbation is permitted.

## Exact within-panel reconstruction

For each panel, both v8 and P21 receive exactly the same retained stable event IDs. Recompute from scratch:

1. exact v6 fixed4 anchor/shortlist/audit proposal generation;
2. exact normal retained `anchor_count>=2` v8 quartets, 512/bin cap, components, hard recurrent families, pooled centroids, multiplicity scores, and hard order;
3. exact P21 pre-retention `anchor_count==1` singleton proposals;
4. exact zero-overlap exclusion against all normally retained quartet events in that thinned year;
5. exact inherited 512/bin singleton cap;
6. exact mutual cross-year nearest-singleton pairing at inherited centroid radius 1.5;
7. exact two-year hard-family novelty veto;
8. exact 4+4 P21 membership and frozen soft ranking by cross-year distance, minimum quartet score, stable ID;
9. exact v8 hard multiplicity order as the complete immutable P21 prefix;
10. SHA-256 freeze of full structural payload and order before hidden-label evaluation.

No parameter, radius, cap, ranking, novelty criterion, or gate may change on a stress panel.

## Required endpoints

For each panel report:

- retained event counts by year and thinning-manifest SHA-256;
- v8 retained-quartet/component/hard-family counts;
- P21 singleton counts before/after overlap veto and cap;
- mutual singleton-pair count, hard-family novelty rejections, surviving P21 family count;
- v8 and P21 qualified matches, recovery@100, macro F1, top-100 dominant precision;
- annual 4–9, 10–24, 25–49, 50–99, 100+ mean F1;
- annual combined 4–24 mean F1;
- all source/integrity/target-firewall diagnostics.

## Frozen stress PASS gate

`PASS_P21_PREREGISTERED_THINNING_STRESS` requires all of:

1. every integrity and target-firewall check passes in all four panels;
2. every panel has a nonempty v8 hard-family universe and a nonempty P21 singleton-recurrence path after the hard-family novelty veto;
3. P21 qualified matches >= within-panel v8 in all four;
4. P21 recovery@100 >= within-panel v8 in all four;
5. P21 top-100 dominant precision equals within-panel v8 to `1e-12` in all four because the exact hard order is an immutable prefix;
6. P21 macro F1 > within-panel v8 in all four;
7. combined 4–24 mean F1 > within-panel v8 in both years in all four panels;
8. 4–9 mean F1 > within-panel v8 in both years in at least three of four panels, with no panel/year 4–9 decrement below `-0.02`.

A power-eligible failure is `FAIL_P21_PREREGISTERED_THINNING_STRESS` and prevents P21 from final-candidate declaration under this path. Stress outcomes may not alter P21 and then be rerun as fresh evidence.

## Interpretability

If thinning leaves a panel with zero evaluable 4–9 known showers, no hard-family universe, or no surviving P21 recurrence path, the panel is not favorable and cannot contribute to a stress PASS.

## Downstream boundary

Even primary P21 PASS plus stress PASS only permits explicit final-candidate freezing. The permanent SonotaCo 2013/2014 literature test remains sealed until one exact method is declared `FINAL_FOR_LITERATURE_TEST` with candidate-specific transport and already-frozen same-information Sugar/HDBSCAN comparisons. MAARSY 2020/2021 and the blind OrbitTrace search remain downstream of their already-frozen gates.
