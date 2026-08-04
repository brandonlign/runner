# SonotaCo 2025 phase-gated 3D quartet development

Status: frozen before any candidate score is computed.

## Scientific rationale

The exact PR #38 four-clique score treated relative solar longitude as one coordinate of complete-link geometry. The preregistered failure anatomy in PR #108 showed that this term, not the nearest-neighbor approximation, dominates the true four-member diameter in 105 of 136 SonotaCo windows. Meteor-shower activity phase and radiant-speed coherence therefore need distinct roles.

## Candidate

Retain the exact 128-event, ±10° episode construction. Search for a four-event clique using:

- 3D complete-link distance in Sun-centered ecliptic radiant longitude, ecliptic latitude, and geocentric speed;
- the exact inherited scales 2°, 2°, and 2 km/s;
- solar longitude only as a hard activity-phase gate requiring the quartet span to be at most 10°;
- a fixed six-neighbor anchor pool, enumerating every choice of three neighbors.

The 10° phase gate is inherited from the existing episode half-width and was frozen before this score was evaluated. No phase-span family, coordinate scale, soft penalty, or threshold sweep is permitted.

## Unchanged design

The exact PR #69 SonotaCo parser, native-label mapping, quality rules, blind interval, positive windows, seeds, 128 calibration negatives per supported 10° bin, 64 independent negatives per bin, conservative rank p-values, folds, alpha levels, comparators, and scientific gates remain unchanged. The original PR #38 score is rerun on the identical episodes and must exactly reproduce its frozen k=4 recall and pooled FPR.

## Continuation gates

The candidate must pass every original SonotaCo transfer gate:

- pooled FPR <= 0.060 / 0.020 at alpha 0.05 / 0.01;
- worst 60° sector FPR <= 0.120;
- weak AUROC >= 0.75, within 0.03 of the strongest comparator, and no more than 0.01 below the original score;
- at least four folds with AUROC >= 0.70 and none below 0.65;
- recall at alpha 0.05 >= 0.15 / 0.30 / 0.45 for k=4/6/8;
- recall at alpha 0.01 >= 0.05 / 0.15 / 0.25 for k=4/6/8;
- monotonic recall through k=12 at both alpha levels.

Any failed gate kills this exact candidate. No result-dependent repair is authorized.

## Blindness

Remove every event at solar longitude 20°–55° inclusive before labels, reservoirs, windows, scores, folds, or endpoints. SonotaCo 2024 remains unopened. No GhostStream radiant, speed, orbit, member list, score, or local region is used.

A complete pass authorizes only a separately frozen robustness benchmark before SonotaCo 2024 confirmation. It does not authorize a catalogue scan or GhostStream application.

Frozen candidate source SHA-256: `fb93ab74edf4c79b00bca6f5c1e6c1a4be33904204bbd2aed296cf2b01dd10b2`.
