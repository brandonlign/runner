# Multiplicity-calibrated multiscale confirmation

## Why this redesign is allowed

The fixed-radius surrogate showed useful cross-network gains but failed its prespecified scale-stability gate. Choosing the best observed radius is prohibited. This confirmation instead treats scale as part of the search and calibrates the maximum score over the complete scale grid under the null.

Multiscale scanning is a robustness mechanism, not the claimed methodological novelty. The candidate contribution remains shared physical support across heterogeneous networks with separate background evidence and leave-one-network-out protection against dominance by one survey.

## Frozen primary method

For each candidate center and each radius in `{0.70, 0.90, 1.10, 1.30}`:

1. compute a network-specific local Poisson excess score from an inner ball and outer shell;
2. retain positive evidence separately for CAMS, GMN, EDMOND, and SonotaCo;
3. sum evidence after removing the largest single-network contribution;
4. require positive evidence from at least two networks.

The scene score is the maximum primary score over all candidate centers and all four radii. Null calibration therefore includes both the candidate-location and scale searches.

## Independent confirmation data draws

- 72 calibration-null scenes;
- 72 independent test-null scenes;
- 96 injection scenes per signal condition;
- new random seeds disjoint from the fixed-radius pilot;
- 20-degree real solar-longitude windows outside M2026-A1;
- at most 600 real background events per network and scene.

## Signal conditions

For both balanced amplitudes `(4,4,4,4)` and heterogeneous amplitudes `(4,6,3,3)`, test three intrinsic dispersions:

- compact: `(0.60 deg, 0.60 deg, 0.40 km/s)`;
- nominal: `(0.90 deg, 0.90 deg, 0.60 km/s)`;
- diffuse: `(1.50 deg, 1.50 deg, 1.00 km/s)`.

Additional controls:

- GMN-only artifact `(0,10,0,0)` at nominal dispersion;
- strong shared signal `(8,8,8,8)` at nominal dispersion;
- balanced weak signal after removing GMN entirely.

## Baselines

Every baseline receives the identical multiscale search and its own null-calibrated maximum-score threshold:

- pooled-catalog scan;
- best single-network scan;
- second-best network score as a simple replication rule.

The unprotected sum of network scores remains an ablation and cannot rescue the frozen primary method.

## External positive control

After all thresholds are frozen, scan the M2026-A1 activity region. It is not used in calibration, radius selection, injection design, or tuning.

## Statistical reporting

- scene-level thresholds target 5% false positives;
- report independent test-null false-positive rates with Wilson 95% intervals;
- use paired injection scenes for all methods;
- report paired bootstrap 95% intervals for the primary recovery gain over the strongest eligible baseline.

## Frozen continuation gates

A full shared latent-stream model is permitted only if every gate passes:

1. primary test-null false-positive rate no greater than 0.10 and Wilson upper 95% bound no greater than 0.15;
2. mean primary recovery across the three balanced dispersions exceeds the strongest eligible baseline by at least 0.10, with paired-bootstrap lower 95% bound above zero;
3. mean primary recovery across the three heterogeneous dispersions exceeds the strongest eligible baseline by at least 0.10, with paired-bootstrap lower 95% bound above zero;
4. at each individual dispersion, primary recovery is not more than 0.10 below the strongest eligible baseline;
5. GMN-only artifact acceptance no greater than 0.10;
6. strong shared-signal recovery at least 0.90;
7. untouched M2026-A1 control is accepted near the published trajectory;
8. after excluding GMN, balanced weak-signal recovery is at least 0.50 and at least 0.05 above pooled search at matched false-positive rate.

Failure means the shared-network candidate remains unvalidated and no full model or GhostStream application is allowed.
