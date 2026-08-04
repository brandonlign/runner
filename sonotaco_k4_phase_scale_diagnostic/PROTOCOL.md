# SonotaCo 2025 activity-phase scale diagnostic

Status: frozen before any revised score, p-value, recall, AUROC, or false-positive endpoint is computed.

## Scientific question

The failed bounded-neighbor diagnostic in PR #108 showed that search approximation was not limiting k=4 recovery. In 105 of 136 four-member windows, solar-longitude separation was the largest component of the true quartet diameter. Does the exact PR #38 complete-link statistic recover sparse streams more reliably when activity phase is down-weighted relative to radiant and geocentric-speed coherence?

## Development and blindness boundaries

SonotaCo 2025 remains the method-development survey. SonotaCo 2024 remains unopened and reserved for a separately preregistered one-shot confirmation only after a final method is frozen. The exact PR #69 parser removes solar longitude 20°–55° before labels, reservoirs, windows, scores, folds, or endpoints. No GhostStream radiant, orbit, members, score, or local region enters this study.

## Exact inherited components

The following remain unchanged:

- PR #69 SonotaCo parser and native-prefix mapping;
- 128-event windows and ±10° activity neighborhoods;
- Sun-centered ecliptic radiant longitude, ecliptic latitude, and geocentric-speed coordinates and their 2°/2°/2 km s⁻¹ scales;
- anchored nearest-three complete-link quartet statistic;
- globally anchored 10° Mondrian calibration bins;
- 128 calibration windows and 64 independent negative windows per supported bin;
- exact positive, calibration, and negative seeds;
- four positive replicates for k in {4,6,8,12};
- conservative rank p-values, alpha 0.05 and 0.01, five complex/parent folds, and all false-positive limits.

## Frozen candidate family

The only changed quantity is the divisor applied to pairwise relative solar longitude:

- 2° per distance unit: exact original control;
- 4° per distance unit;
- 6° per distance unit;
- 8° per distance unit.

For every scale, all calibration and test scores are recomputed independently with the same windows and seeds. No post-result scale, interpolation, cap, activity gate, alternate quartet search, or score combination may be added.

## Held-out selection

For each held-out complex/parent fold, select a scale using only positive windows from the other four folds. A scale is eligible only when its independently calibrated negative windows satisfy pooled FPR ≤0.060/0.020, worst 60°-sector FPR ≤0.120, training weak AUROC is within 0.01 of the original, and training k=6 and k=8 recall at alpha 0.05 are each within 0.02 of the original. Among eligible scales select lexicographically by training k=4 recall at 0.05, then k=4 recall at 0.01, then weak AUROC, then the smaller scale.

Continue only if:

- one scale is selected in at least four of five folds;
- cross-fitted k=4 recall reaches at least 0.15 at alpha 0.05 and 0.05 at alpha 0.01;
- the consensus scale passes all frozen FPR limits;
- consensus weak AUROC is no more than 0.01 below the original;
- consensus k=6 and k=8 recall at alpha 0.05 are each no more than 0.02 below the original;
- the 2° control exactly reproduces PR #69 k=4 recall and pooled FPR.

A complete pass authorizes only a separately frozen full revised SonotaCo-2025 development benchmark. It does not authorize SonotaCo 2024, a catalogue scan, or GhostStream application.

Frozen diagnostic source SHA-256: `e5cdb6eb8d07fdbcc5c29a4d02139fff86386e8aebde83717fdc7485acda265d`.
