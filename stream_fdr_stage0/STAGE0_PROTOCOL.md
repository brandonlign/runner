# Shared-stream / separate-background Stage-0 protocol

## Purpose

Determine whether joint event-level modeling across independent meteor networks can recover weak shared streams more reliably than pooling catalogs or searching each catalog separately, without using GhostStream in model design, tuning, threshold selection, or continuation decisions.

## Candidate method

Each network receives its own flexible background density. Candidate stream components share a physical trajectory in solar longitude, Sun-centered geocentric radiant, and geocentric speed, while allowing network-specific amplitudes, reported measurement covariances, and small calibration offsets.

The method is not allowed to require a candidate to be individually significant in every network. Instead it must earn positive held-out predictive evidence across networks and must not be driven exclusively by the largest catalog.

## Stage 0A — data feasibility

Inputs are the four public shower-removed asteroidal subsets released with Shober (2026): CAMS, GMN, EDMOND, and SonotaCo.

Pass conditions:

1. At least three datasets expose compatible year/time, solar longitude, geocentric radiant, and geocentric speed fields.
2. At least three have at least 1,000 valid events after the same broad physical sanity bounds.
3. Network-specific uncertainty or quality fields exist for at least two datasets; otherwise the first pilot must use fixed network-level uncertainty and treat event-level uncertainty as unavailable.
4. The conservative M2026-A1-region mask appears in at least two networks, or another externally documented weak shared component can be selected before model fitting.

Failure of conditions 1 or 2 kills the candidate. Failure of condition 3 narrows the claim but does not kill it. Failure of condition 4 means the real-data positive benchmark must come from a separate labeled source before implementation.

## Stage 0B — benchmark construction

No GhostStream events are permitted.

### Positive controls

- one or more weak streams with documented presence in multiple networks;
- network labels may be used only to define an evaluation set, never as model inputs;
- at least one positive control is held out from all hyperparameter decisions.

### Negative controls

- null catalogs generated separately within network-year strata;
- removed or disputed showers with no consistent cross-network evidence;
- synthetic single-network artifacts that should not become shared components.

### Injections

Inject one shared physical component into independently resampled network backgrounds with different amplitudes, measurement noise, and coverage. Include cases where no single network clears its own detection threshold but the joint evidence should be sufficient.

## Baselines

1. pooled HDBSCAN/DBSCAN after global standardization;
2. per-network HDBSCAN/DBSCAN followed by union of detections;
3. per-network search followed by intersection/replication requirement;
4. fixed KDE-null pair-excess scan where computationally feasible;
5. cross-fitted candidate discovery and held-out testing.

All methods receive the same physical variables and the same evaluation scenes.

## Primary metrics

- catalog-level false discovery rate;
- weak-stream recovery rate;
- event recall and purity for recovered positive controls;
- leave-one-network-out predictive log-likelihood gain;
- recovery after excluding the largest network;
- calibration under doubled measurement noise and alternate background bandwidths;
- fraction of reported components supported by at least two networks.

## Frozen continuation gates

Continue only if all gates pass:

1. realized catalog-level FDR <= 0.10 and upper 95% confidence bound <= 0.15;
2. weak-stream recovery improves by >= 0.10 absolute over the best baseline at matched FDR;
3. at least half the gain survives exclusion of the largest network;
4. at least one untuned real weak stream is recovered;
5. at least one plausible false/removed stream is rejected;
6. recovery loss is <= 0.20 under doubled noise and alternate background smoothness;
7. no network contributes >90% of the held-out evidence for every recovered component;
8. all thresholds and hyperparameters are frozen before any GhostStream application.

## Kill interpretations

- If pooled clustering wins, the hierarchical model is unnecessary.
- If separate-network union wins, shared modeling adds complexity without evidence.
- If the method works only because GMN dominates, it is not a multi-network method.
- If flexible backgrounds absorb injected streams, identifiability is inadequate.
- If flexible stream components absorb null structure, error calibration is inadequate.
- If labels are required for component discovery, the method is supervised association rather than blind discovery.

## Claim boundary after a pass

A pass supports only the following provisional claim:

> A shared-component, network-specific-background approach can improve weak meteor-stream discovery across heterogeneous surveys at controlled catalog-level false discovery rate.

It would not establish that GhostStream is a distinct stream, identify a parent body, or justify a first-ever claim without a completed literature review and independent expert assessment.
