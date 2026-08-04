# SonotaCo 2025 fixed two-scale joint-conformal scan

Status: frozen before any candidate score, p-value, recall, AUROC, or false-positive endpoint is computed.

## Scientific motivation

PR #113 established that the exact 2° and 4° activity-phase scales recover complementary sparse shower windows. The fixed 4° score passed both original k=4 recall gates, but complex-held-out selection of one global scale was unstable. This experiment therefore does not choose a scale. It scans the fixed pair {2°,4°} and applies one finite-sample empirical conformal correction to the scale search.

## Exact candidate

For each 128-event episode, preserve the PR #113 anchored nearest-three complete-link quartet score at exactly two solar-longitude divisors:

- 2° per distance unit — exact PR #38 / PR #69 control;
- 4° per distance unit — the independently motivated broader activity-phase scale from PR #113.

Within the episode's globally anchored 10° Mondrian bin, append the episode to the exact 128 calibration episodes. For all 129 exchangeable episodes:

1. compute the conservative upper-tail rank of the 2° score among all 129 scores;
2. compute the conservative upper-tail rank of the 4° score among all 129 scores;
3. define the scan extremeness as the negative minimum of those two component ranks;
4. define the final candidate p-value as the conservative rank of that scan extremeness among all 129 exchangeable scan extremeness values.

This symmetric transductive construction corrects the fixed two-scale search directly under exchangeability. No Bonferroni approximation, alpha adjustment, scale selection, interpolation, scale weight, extra calibration stream, or result-dependent choice is permitted.

## Inherited components

Preserve unchanged:

- the exact PR #69 SonotaCo parser and native-prefix mapping;
- removal of solar longitude 20°–55° inclusive before labels, reservoirs, windows, scores, folds, or endpoints;
- SonotaCo 2025 as the development survey;
- 128-event windows, ±10° activity neighborhoods, and exact positive/calibration/negative seeds;
- anchored nearest-three quartet search and radiant/latitude/speed scales;
- globally anchored 10° Mondrian bins;
- 128 calibration windows and 64 independent test-negative windows per supported bin;
- four positive replicates at k in {4,6,8,12};
- five complex/parent folds, alpha 0.05 and 0.01, fixed split/density/DBSCAN comparators, and reporting sectors.

The exact original 2° score and fixed 4° score remain controls.

## Frozen continuation gates

The original 2° control must exactly reproduce PR #69 recall, FPR, and weak AUROC. The joint candidate must satisfy all of the following:

- pooled FPR ≤0.060 / 0.020 at alpha 0.05 / 0.01;
- worst 60° reporting-sector FPR at alpha 0.05 ≤0.120;
- weak AUROC ≥0.75, no more than 0.01 below the original, and within 0.03 of the strongest fixed comparator;
- at least four fold AUROCs ≥0.70 and none below 0.65;
- k=4 recall ≥0.15 / 0.05 at alpha 0.05 / 0.01 and strictly above the original at both levels;
- k=6 recall ≥0.30 / 0.15 and k=8 recall ≥0.45 / 0.25 at alpha 0.05 / 0.01;
- k=6 and k=8 recall at each alpha no more than 0.02 below the original;
- monotonic recall through k=12 at both alpha levels.

Any failed gate kills this exact candidate. No scale addition, calibration-size change, fusion repair, threshold adjustment, or post-result retuning is authorized.

A complete pass authorizes only a separately frozen full SonotaCo-2025 revised-development benchmark. It does not authorize SonotaCo 2024, a catalogue scan, or GhostStream application.

## Blindness

SonotaCo 2024 remains unopened. No GhostStream radiant, speed, orbit, members, score, solar-longitude region, or local information is used.

Frozen candidate source SHA-256: `766a1180df767f065b76f335a30f374516f6dc8c6c668d5aa8132789faf66e0d`.
