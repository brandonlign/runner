# Shared-support scan surrogate pilot

## Purpose

Before building a full hierarchical point-process model, test the core hypothesis cheaply: network-specific background evidence combined around one shared physical component should recover weak cross-network signals better than pooled or single-network searches while rejecting a strong artifact confined to one catalog.

This is a surrogate kill test, not the proposed final method.

## Data

Use the four shower-removed asteroidal subsets released with Shober (2026): CAMS, GMN, EDMOND, and SonotaCo. GhostStream is excluded.

Each event is represented by:

- solar longitude for scene selection;
- Sun-centered geocentric ecliptic longitude;
- geocentric ecliptic latitude;
- geocentric speed.

The four networks retain separate event samples and separate background estimates.

## Scene construction

- draw 20-degree solar-longitude windows outside the M2026-A1 activity region;
- sample at most 600 background events per network per scene;
- preserve each network's real local background rather than pooling catalogs;
- use independent fixed random seeds for calibration-null, test-null, and injection scenes.

## Candidate search

Search candidate centers among the observed events in the scene. For every candidate and network:

1. count events inside an inner metric radius;
2. estimate expected inner occupancy from an outer shell;
3. compute a one-sided Poisson log-likelihood-ratio excess score.

The frozen primary score is the sum of positive network scores after removing the single largest network contribution. At least two networks must provide positive local evidence. This leave-one-network-out score is intended to prevent a large catalog from defining a supposedly shared component by itself.

## Baselines

- pooled-catalog Poisson scan;
- best single-network scan;
- second-best network evidence (simple replication rule);
- unprotected sum of network-specific scores as an ablation, not a baseline eligible to rescue the frozen primary method.

## Calibration

Calibrate a separate scene-level threshold for each method from 36 real null scenes. Evaluate realized false positives on 36 independent null scenes. Thresholds target a 5% scene-level false-positive rate.

## Injection tests

Use 32 independent scenes for each frozen pattern:

- balanced weak shared signal: 4 injected events in every network;
- heterogeneous weak shared signal: CAMS 4, GMN 6, EDMOND 3, SonotaCo 3;
- three-network weak signal: CAMS 4, GMN 5, EDMOND 0, SonotaCo 4;
- GMN-only artifact: CAMS 0, GMN 10, EDMOND 0, SonotaCo 0;
- stronger shared signal: 8 injected events in every network.

Injected events share one physical center but receive network-specific subscale offsets and measurement scatter. Candidate centers are not supplied to the detector.

## External positive control

After all thresholds are frozen, scan the M2026-A1 solar-longitude region and test whether the primary score's top accepted component lies near the published stream trajectory. This control is not used for tuning.

## Sensitivity

Repeat the complete calibration and evaluation at inner radii 0.8, 1.0, and 1.2 in the frozen standardized metric; the outer-shell radius is 2.5 times the inner radius.

## Frozen continuation gates

The full hierarchical model is permitted only if the primary leave-one-network-out score passes all gates at radius 1.0:

1. independent-null false-positive rate no greater than 0.15;
2. recovery of the balanced weak signal at least 0.10 above the best eligible baseline at its separately calibrated threshold;
3. recovery of the heterogeneous weak signal at least 0.10 above the best eligible baseline;
4. acceptance of the GMN-only artifact no greater than 0.10;
5. recovery of the stronger shared signal at least 0.80;
6. external M2026-A1 control accepted near its published trajectory;
7. balanced and heterogeneous recovery do not fall by more than 0.20 at either alternate radius.

Failure means kill or redesign the shared-network formulation before any full model or GhostStream application. Passing means only that a full benchmark is worth constructing.
