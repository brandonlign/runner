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

## Fixed controls and source

Control showers are frozen as IAU 4/GEM, 6/LYR, 7/PER, 10/QUA, and 13/LEO. Event data come only from official GMN trajectory-summary products. The de-showered Shober 2026 subset may be used as an uncertainty/background cross-check but not as a labeled benchmark.

The frozen observing years are 2019, 2021, 2023, and 2025. Only the control activity months are downloaded: January, April, August, November, and December.

## Data gate

The benchmark may run only if:

- at least four predefined controls have at least 200 quality-screened events;
- at least four controls have at least 20 quality events in every frozen year;
- at least 2,000 quality-screened sporadic events exist in the matched year-month strata;
- at least 95% of selected rows reconstruct a nominal state;
- at least 90% reconstruct element-level uncertainty clones;
- controls span substantially different dynamical regimes.

No control may be removed because it performs poorly.

## Samples

For each usable control:

- form eight disjoint 20-event shower subgroups;
- use five events from each frozen year;
- rank quality within each year using uncertainty magnitude, `Qc`, fit error, and station count without reference to dynamical outcomes;
- construct at least 12 and preferably 24 matched sporadic groups per shower subgroup.

Each matched sporadic group must match:

- group size and year-count vector exactly;
- median `(a, e, i, q, T_J)` standardized distance no greater than 0.50;
- median uncertainty-vector standardized distance no greater than 0.50;
- initial median pairwise `D_SH` within ±10%;
- initial 90th-percentile pairwise `D_SH` within ±15%.

If fewer than 12 matched groups can be formed for more than one control, the candidate is killed as unbenchmarkable rather than relaxing tolerances afterward.

## Propagation surrogate

Stage 0 uses a cheaper but real gravitational propagation:

- Sun plus giant planets from one fixed, documented ephemeris source;
- all meteors are massless test particles;
- nominal orbit plus eight independently sampled element-error clones per event;
- integrate backward to 0, 25, 50, 100, and 200 years;
- identical integration settings for shower and matched groups;
- no non-gravitational forces.

Energy and integration errors are recorded. Technically unstable particles are rejected under frozen rules before group scoring.

## Predictability horizon

The event horizon is the latest epoch before either:

- median clone-to-nominal `D_SH` exceeds 0.05; or
- at least 25% of clones become technically invalid or unbound when the nominal orbit is not.

The group scoring horizon is the 20th percentile of its event horizons. A shower and matched group are compared only through the shorter group horizon.

## Scores

Primary score: null-standardized area between matched-group and shower-group median pairwise-`D_SH` growth curves over valid epochs. Positive values mean the real subgroup preserves more coherence than an equally compact chance group.

Baselines:

- present-day median and 90th-percentile pairwise `D_SH`;
- present-day standardized orbital compactness;
- the same dynamical score without initial-compactness matching;
- the same score without clone-horizon normalization.

## Frozen continuation gates

All must pass:

1. At least four of five controls have median primary score above the 90th percentile of matched sporadic groups.
2. Shower-versus-matched-group subgroup AUROC is at least 0.75.
3. AUROC gain over the best present-day baseline is at least 0.15.
4. Matched-sporadic false-positive rate is at most 0.10, with upper 95% bootstrap bound at most 0.15.
5. At least 70% of shower subgroups retain a scoring horizon of at least 50 years.
6. Removing clone-horizon normalization worsens AUROC or false-positive control by at least 0.05.
7. AUROC changes by no more than 0.10 at prospectively fixed clone thresholds 0.035 and 0.075.
8. No single control contributes more than half of total AUROC gain.

## Kill rules

Kill the candidate if any gate fails. Do not rescue it by selecting favorable showers, relaxing matching, repeatedly changing clone thresholds, extending the horizon until separation appears, choosing another orbital distance afterward, or applying it to GhostStream before every gate passes.
