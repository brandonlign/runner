# GhostStream versus NOP solution 004: frozen Track-1 protocol

## Question

Does the best public evidence support the claim that GhostStream is merely the same population represented by IAU MDC shower 149/NOP solution 004, or does it require a separate concentration?

This protocol distinguishes three conclusions:

1. literal identity with the NOP-004 population;
2. a related branch or substructure in the broader Ophiuchid/antihelion complex;
3. a fully distinct stream.

The last conclusion is not authorized from incomplete public NOP member orbits alone.

## Frozen inputs

The workflow verifies and uses these preserved runner artifacts:

- canonical GhostStream package: artifact `8814798136`, ZIP SHA-256 `716b70313465d5df4bfb092a85a81680e6f618606b71e25470c63c480b6449f5`;
- official NOP-004 provenance audit: artifact `8874517049`, ZIP SHA-256 `2707a7be1152967960703245e62049e74f4eb778c84098f27c2486385acd512c`;
- exact multi-source NOP orbit recovery: artifact `8875235491`, ZIP SHA-256 `978e59f2e6b9c63644b0640d21662ab56307633da25d298bbb4d870dfb897ab7`.

Expected immutable counts are 95 significant-year GhostStream members, 567 official NOP-004 observations and 118 exact public source-matched NOP orbits.

## Analyses

No detector, candidate membership, NOP membership, threshold or shower label is changed.

1. **Activity separation**: compare the observed solar-longitude ranges and measure any empty interval.
2. **Observed radiant/speed trend**: fit one Theil-Sen linear trend to the official NOP sun-centered ecliptic longitude, latitude and geocentric speed as functions of solar longitude. Evaluate NOP and GhostStream residuals against that same trend. Estimate the probability of a 95-member NOP sample having a median radiant residual at least as large as GhostStream using 100,000 fixed-seed bootstrap samples.
3. **Direct orbital population comparison**: compute Southworth-Hawkins-style orbital distances between the 95 GhostStream orbits and 118 exact recovered NOP orbits. Report within-NOP nearest neighbors, Ghost-to-NOP nearest neighbors and cross-links at fixed descriptive thresholds 0.05, 0.10, 0.15 and 0.20.
4. **Orbital-trend extrapolation**: fit Theil-Sen trends for NOP eccentricity, perihelion distance, inclination and argument of perihelion against solar longitude, with node fixed to the encounter solar longitude. Compare NOP members to their fitted trend and GhostStream to the extrapolated trend.
5. **Current GMN population check**: independently download May and June GMN trajectory catalogues for 2018–2026, retain quality-controlled trajectories labelled NOP, deduplicate exact events, and repeat the orbital comparison. This population is label-dependent corroboration and does not replace the original NOP-004 membership.

## Decision boundary

Literal NOP-004 identity is rejected only when all of the following hold:

- the observed activity intervals do not overlap;
- the GhostStream median radiant residual exceeds every official NOP residual under the frozen robust trend;
- the median Ghost-to-NOP nearest-neighbor orbital distance exceeds the 99th percentile of within-NOP nearest-neighbor distances;
- the median GhostStream residual from the extrapolated NOP orbital trend exceeds the 95th percentile of NOP residuals from its own trend.

A related branch remains plausible when at least one cross-population link exists at `D_SH <= 0.15`.

A fully distinct-stream classification is not issued without the complete original 567 NOP member orbits, uncertainty information, or authoritative expert assessment.

## Prohibited follow-up

The result may not be repaired by changing the candidate membership, selecting a more favorable NOP subset, altering thresholds, fitting nonlinear models after inspecting the result, or inventing another classifier. Negative and ambiguous results remain final for this protocol.
