# GhostStream methodology search: pressure-tested candidates

This file is a methodology incubator, not part of the validated GhostStream pipeline. Nothing here may be described as a GhostStream method unless it passes the frozen external benchmarks below.

## Problem definition

The useful methodological gap is not pairwise orbit similarity. The corrected Stage-0 common-origin benchmark showed that standard D-criteria already solve that subproblem better than the attempted learned score.

The remaining general problem is blind discovery of weak meteor streams in heterogeneous surveys while controlling false stream discoveries after an adaptive search over candidate locations, scales, algorithms, and hyperparameters.

## Candidate A — survey-preserving target-decoy discovery

Generate decoy catalogs by breaking stream coherence while attempting to preserve each survey's seasonal and geometric selection structure. Run the complete adaptive discovery pipeline on target and decoy catalogs, then estimate the false-stream fraction from high-scoring decoy clusters.

### Why it could matter

- calibrates the complete search rather than a fixed bin or one chosen cluster;
- can in principle use the full catalog rather than discarding a validation split;
- reports a catalog-level false discovery rate rather than only local membership contamination.

### Fatal weakness

The guarantee depends on null target clusters and decoy clusters being exchangeable. Meteor sporadic structure varies with solar longitude, radiant direction, network latitude, weather, and operational history. A permutation that destroys showers may also destroy real background structure, making decoys too easy and the estimated false discovery rate anti-conservative.

### Decision

**Secondary candidate only.** Continue only if a pre-GhostStream exchangeability benchmark shows that target-null and decoy top-cluster score distributions match across network-years. No tuning of the scramble is allowed after seeing GhostStream.

## Candidate B — cross-fitted adaptive stream significance

Use one independent subset of years or networks for unrestricted candidate generation and hyperparameter selection, then test the frozen candidate trajectory in held-out data against survey-matched analogues. Reverse the split and combine evidence with a finite-sample-valid multi-split procedure. Apply catalog-level multiple-testing control to held-out candidate tests.

### Why it could matter

- selection can be arbitrarily adaptive without contaminating the held-out test;
- directly addresses double-dipping in blind cluster discovery;
- permits a rigorous comparison between naive post-selection significance and honest significance.

### Fatal weakness

Weak streams may not survive data splitting. A method that controls errors but loses nearly all low-member streams is not useful.

### Decision

**Valid fallback and benchmark baseline.** Continue only if it detects an embedded real weak stream and materially outperforms a single 50/50 split at the same realized false discovery rate.

## Candidate C — shared latent-stream model with network-specific backgrounds

Fit multiple meteor networks jointly. A real stream is represented by one shared physical radiant/speed trajectory and intrinsic dispersion, while each network retains its own background intensity, measurement covariance, coverage, calibration offsets, and stream amplitude. Candidate discovery is driven by cross-network predictive evidence rather than pooling incompatible catalogs.

A minimal model is

`intensity_network(x) = background_network(x) + sum_k amplitude_network,k * shared_stream_k(x)`

with group sparsity on stream components and leave-one-network-out predictive testing.

### Why it could matter

- directly addresses the documented failure of thresholds calibrated on statistically dissimilar combined catalogs;
- turns independent-network replication into the discovery objective rather than an after-the-fact check;
- can recover a shared weak component that is individually sub-threshold in several networks;
- remains useful even when a specific astronomical candidate is rejected.

### Closest prior work found

- meteor databases have been pooled and clustered directly;
- individual networks have been searched separately and compared;
- recent work uses network-matched KDE nulls and cross-network confirmation;
- multi-observer count-rate models account for observer-specific backgrounds;
- no direct precedent was found for blind event-level meteor-stream discovery with a shared latent component, separate catalog backgrounds, and leave-one-network-out error calibration.

This is a provisional novelty boundary, not a first-ever claim.

### Fatal weaknesses

- network-specific selection functions may be too poorly documented to identify a shared component;
- one dominant network could determine the component while other networks add negligible evidence;
- a flexible background model could absorb real weak streams or a flexible stream model could absorb background structure;
- available labels may be circular because network shower codes are themselves produced by established association rules.

### Decision

**Primary candidate.** It earns a full pilot only if the data audit confirms compatible event-level coordinates in at least three networks and the benchmark can use held-out known streams or injected streams without relying solely on inherited shower labels.

## Ideas rejected before implementation

### Another learned orbit-distance metric

Rejected by the corrected parent-disjoint benchmark. It underperformed D_SH/D_D, recovered no weak streams, and transferred catastrophically.

### Uncertainty-aware DBSCAN/HDBSCAN

Too close to prior meteor clustering work that already propagates measurement uncertainty and evaluates cluster occurrence. At most an implementation improvement.

### Persistence across clustering scales

HDBSCAN already operationalizes density persistence. Rebranding hyperparameter stability as a new framework would not be substantial.

### Radiant-track matched filtering

Gridded radiant searches, wavelet transforms, radiant drift models, and fixed template searches already cover the core concept. A new implementation would need a separate statistical contribution.

### Generic Bayesian mixture model on one catalog

Mixture models are standard, and without the multi-network shared-physics constraint this is mainly a model substitution.

## Frozen primary Stage-0 gates

The shared-network candidate is killed unless all conditions hold on data and candidates unrelated to GhostStream:

1. At least three networks provide compatible solar longitude, geocentric radiant, speed, year/time, and uncertainty or quality fields.
2. Leave-one-network-out recovery of known weak streams improves by at least 10 percentage points over both pooled HDBSCAN and separate-network HDBSCAN union at matched false discovery rate.
3. At least half of the gain remains when the largest network is excluded.
4. Null catalogs produce a realized catalog-level false discovery rate no greater than 0.10 with an upper 95% confidence bound no greater than 0.15.
5. Recovery does not collapse by more than 20 percentage points under alternate background bandwidths, network offsets, or doubled measurement noise.
6. The model must recover at least one real weak stream not used for tuning and reject at least one plausible false/removed stream.
7. GhostStream remains completely excluded until all gates are frozen and passed.

## Current ranking

1. Shared latent-stream / separate-background model.
2. Cross-fitted adaptive significance.
3. Target-decoy catalog FDR, conditional on an unusually strong exchangeability result.
