# SonotaCo 2025 phase-normalized quartet development

Status: frozen before any candidate score is computed.

## Scientific rationale

PR #109 showed that removing activity phase from geometry improved overall discrimination and stronger sparse-stream recovery, but lost several four-member windows that the original phase-heavy score uniquely detected. The two scores therefore encode complementary structure: compact activity timing and tight radiant-speed coherence.

## Single candidate

Use one complete-link distance with distinct physical normalizations:

- relative solar longitude difference divided by **10°**, the inherited episode half-width;
- Sun-centered ecliptic radiant longitude divided by **2°** with the inherited cosine-latitude correction;
- ecliptic latitude divided by **2°**;
- geocentric speed divided by **2 km/s**.

For each anchor, enumerate all quartets formed from its fixed six nearest neighbors and retain the minimum complete-link diameter. There is no hard phase gate and no scale family. The 10° phase normalization is fixed by the pre-existing activity window, not selected from candidate outcomes.

## Unchanged design

Use the exact PR #69 parser, labels, blind interval, event filters, windows, seeds, 128 candidate-specific calibration negatives per supported 10° bin, 64 independent negatives per bin, conservative rank p-values, folds, alpha levels, fixed comparators, and scientific gates. Rerun the original PR #38 score on identical episodes and require exact reproduction of its frozen FPR and k=4 recall.

## Continuation gates

The candidate must pass every original SonotaCo transfer gate:

- pooled FPR <= 0.060 / 0.020 at alpha 0.05 / 0.01;
- worst 60° sector FPR <= 0.120;
- weak AUROC >= 0.75, within 0.03 of the strongest comparator, and no more than 0.01 below the original score;
- at least four folds with AUROC >= 0.70 and none below 0.65;
- recall at alpha 0.05 >= 0.15 / 0.30 / 0.45 for k=4/6/8;
- recall at alpha 0.01 >= 0.05 / 0.15 / 0.25 for k=4/6/8;
- monotonic recall through k=12 at both alpha levels.

Any failed gate kills this exact formulation. No result-dependent phase scale, threshold, candidate combination, or repair is authorized.

## Blindness

Remove every event at solar longitude 20°–55° inclusive before labels, reservoirs, windows, scores, folds, or endpoints. SonotaCo 2024 remains unopened. No GhostStream radiant, speed, orbit, member list, score, or local region is used.

A complete pass authorizes only a separately frozen robustness benchmark on the already-spent GMN methodology corpus before any SonotaCo 2024 confirmation.

Frozen candidate source SHA-256: `64e7ce227545b697da5c8568d687fca3490aafd548d9593a3e70c07cdcefe6c0`.
