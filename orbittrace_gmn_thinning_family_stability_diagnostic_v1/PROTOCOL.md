# OrbitTrace GMN thinning family-stability diagnostic v1

## Purpose

Test whether **label-free candidate persistence under already-preregistered deterministic event thinning** is informative about family quality on the target-excluded GMN 2022/2023 development corpus.

This is diagnostic only. It does not define or evaluate a SonotaCo successor.

## Immutable inputs

- exact #839 4,504-family union: 226 hard + 1,075 P19 + 3,203 P20;
- exact #842 candidate-generation stress panels A10, B10, C20, D20;
- exact #839 family-truth semantics, used only after stability has been computed;
- exact #843 two-year family distance semantics;
- exact #843/v19 selected agreement radius **1.0**.

The four thinning panels are already frozen:

- A10: 10% removal, `URC-GENERATOR-STRESS-A`;
- B10: 10% removal, `URC-GENERATOR-STRESS-B`;
- C20: 20% removal, `URC-GENERATOR-STRESS-C`;
- D20: 20% removal, `URC-GENERATOR-STRESS-D`.

## Label-free stability score

For every original family and every thinning panel:

1. restrict potential counterparts to the **same generator source** (`hard`, `p19`, or `p20`);
2. use the exact #843 family distance: maximum of the exact inherited centroid distance in 2022 and 2023;
3. panel persistence is 1 iff at least one counterpart has distance <= **1.0**;
4. family stability is the sum of the four persistence indicators, an integer from 0 to 4.

No event-label, target, family-quality value, new radius, learned model, or tuned threshold enters stability construction.

## Diagnostic evaluation

Only after all family stability values are fixed, reconstruct the exact #839 target vector. For each source and each exact stability value 0,1,2,3,4 report:

- family count;
- positive-family count;
- mean target F1;
- q90 target F1;
- maximum target F1;
- count of families with target F1 > 0.5.

Also report, without names, the stability-count histogram of all P20 families with target F1 > 0.5.

F1 > 0.5 is the pre-existing catalogue recovery criterion, not a newly selected threshold.

## Firewall and interpretation

No SonotaCo 2013/2014, matched Sugar/HDBSCAN route, MAARSY, DMS, OrbitTrace target information, or target-region event may be accessed. P20/P21 remain standalone scientific no-gos.

A future successor is justified only if this diagnostic shows that high-quality families, especially the rare P20 high-quality mode, are materially distinguished by thinning persistence. No stability cutoff or fusion rule is selected in this diagnostic.