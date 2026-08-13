# Predictability-normalized dynamical coherence: frozen Stage-0 benchmark

Status: protocol only. GhostStream is excluded from design, tuning, thresholds, and evaluation.

## Scientific question

Does short-horizon orbital evolution contain information about common stream origin after conditioning on present-day orbital compactness?

Ordinary backward integration, D-criterion evolution, clone integration, and chaos diagnostics are established. The narrow candidate contribution is a matched test of **incremental dynamical coherence**:

1. match chance groups to each real shower subgroup in present-day compactness, orbit regime, year composition, group size, and uncertainty quality;
2. propagate nominal orbits and uncertainty clones;
3. stop scoring each event when its own clones lose predictive coherence;
4. ask whether the real subgroup remains more coherent than its matched chance groups within that defensible horizon.

A result is not novel merely because it uses N-body integration.

## Data gate

The benchmark may run only if the checksum-verified GMN audit passes every frozen feasibility gate:

- at least four predefined control showers have at least 200 quality-screened events;
- at least four controls span at least four observing years;
- at least 2,000 quality-screened sporadic events exist;
- at least 95% of selected rows reconstruct a nominal state;
- at least 90% reconstruct element-level uncertainty clones;
- controls span substantially different dynamical regimes.

## Fixed controls

IAU shower numbers: 4, 6, 7, 10, and 13.

No control may be removed because it performs poorly. A control may be declared technically unusable only by a failure already defined in the data audit.

## Samples

For each usable control:

- form eight disjoint 20-event shower subgroups where data permit;
- stratify each subgroup over observing years;
- use the lowest-uncertainty quality-screened events within each year stratum without reference to dynamical outcomes;
- construct 24 matched sporadic groups per shower subgroup.

Each matched sporadic group must match, within frozen tolerances:

- group size exactly;
- year-count vector exactly when feasible, otherwise total-variation distance no greater than 0.10;
- median `(a, e, i, q, T_J)` standardized distance no greater than 0.50;
- median uncertainty-vector standardized distance no greater than 0.50;
- initial median pairwise `D_SH` within ±10%;
- initial 90th-percentile pairwise `D_SH` within ±15%.

If fewer than 12 matched groups can be formed for more than one control, the method is killed as unbenchmarkable rather than relaxing the matching after inspection.

## Propagation surrogate

Stage 0 is deliberately cheaper than a final integration:

- Sun plus giant planets from a fixed, documented ephemeris source;
- all meteors are massless test particles;
- nominal orbit plus eight independently sampled uncertainty clones per event;
- integrate backward to 0, 25, 50, 100, and 200 years;
- use the same integrator, time step/tolerance, and output epochs for real and matched groups;
- no non-gravitational forces in Stage 0.

The surrogate must record energy error and reject technically unstable integrations before group scoring under frozen rules.

## Predictability horizon

For each event and output epoch, compute the median clone-to-nominal orbital distance. The event horizon is the latest epoch before either:

- median clone-to-nominal `D_SH` exceeds 0.05; or
- at least 25% of clones become technically invalid or unbound when the nominal orbit is not.

The group scoring horizon is the 20th percentile of its event horizons. Real and matched groups are compared only at epochs no later than the shorter of their two group horizons.

This threshold is frozen before any integrations.

## Scores

Primary score: null-standardized area between the matched group and real group median pairwise-`D_SH` growth curves, integrated over valid output epochs. Positive values mean the real shower subgroup preserves more coherence than equally compact chance groups.

Secondary scores:

- time to double initial median pairwise `D_SH`;
- slope of median pairwise `D_SH` versus lookback time;
- fraction of event pairs remaining below their initial group 90th-percentile distance;
- score without clone-horizon normalization.

The unnormalized score is an ablation, not an alternative primary result.

## Baselines

- present-day median and 90th-percentile pairwise `D_SH`;
- present-day standardized orbital-feature compactness;
- the same dynamical score without matching initial compactness;
- the same score without clone-horizon normalization.

Because matched controls condition on present-day compactness, a valid dynamical contribution must outperform the present-day baselines rather than inherit their separation.

## Frozen continuation gates

All must pass:

1. At least four of five controls have a median primary score above the 90th percentile of their matched sporadic groups.
2. Shower-versus-matched-group AUROC is at least 0.75 using subgroup-level scores.
3. AUROC gain over the best present-day baseline is at least 0.15.
4. Matched sporadic false-positive rate at the frozen 90th-percentile threshold is at most 0.10, with an upper 95% bootstrap bound at most 0.15.
5. At least 70% of shower subgroups retain a scoring horizon of at least 50 years.
6. Removing clone-horizon normalization worsens either false-positive control or AUROC by at least 0.05; otherwise the claimed predictability normalization adds no value.
7. Results do not change by more than 0.10 AUROC when the clone-divergence threshold is varied once, prospectively, to 0.035 and 0.075.
8. No single control contributes more than half of the total AUROC gain.

## Kill rules

Kill the candidate if any continuation gate fails. Do not rescue it by:

- selecting only favorable showers;
- expanding matching tolerances after seeing results;
- changing the clone threshold repeatedly;
- extending the integration horizon until separation appears;
- replacing `D_SH` with whichever distance performs best afterward;
- applying the method to GhostStream before all gates pass.

A pass authorizes a larger shower-disjoint and ephemeris-verified benchmark. It does not establish novelty or authorize a GhostStream claim by itself.
