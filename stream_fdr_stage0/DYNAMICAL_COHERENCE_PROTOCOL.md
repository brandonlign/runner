# Predictability-normalized dynamical coherence: feasibility protocol

## Purpose

Determine whether short-horizon dynamical evolution contains stream-membership information beyond present-epoch orbital similarity.

This is a runner-only methodology gate. GhostStream is excluded from data selection, thresholds, model design, and continuation decisions.

## Narrow candidate contribution

For a candidate meteor group, integrate nominal or uncertainty-clone orbits over a finite horizon and compare the evolution of group dispersion with static-matched chance groups. The integration horizon is normalized by each orbit's own predictability limit, estimated from clone divergence or close encounters.

The proposed evidence is not simply that a group stays close. Nearby osculating orbits stay close initially by continuity. The intended statistic is a **dynamical coherence surplus** after conditioning the null groups on:

- the same present-day orbital compactness;
- the same local orbit region;
- the same number of meteors;
- similar measurement quality;
- similar observation epochs.

A useful method must distinguish real stream groups from chance groups that are equally compact at the observation epoch.

## Prior-art boundary

Established work already includes:

- D-criteria and near-invariant geocentric variables for stream identification;
- grouping meteoroids by broadly similar orbital evolution;
- backward/forward integrations for stream-parent associations;
- tracking D-criteria through time;
- clone integrations and chaos indicators such as OFLI;
- physical stream integrations and stream-age estimation.

Therefore none of the following is novel by itself:

- integrating meteor orbits;
- measuring whether D remains small;
- computing clone divergence;
- applying a chaos indicator;
- adding dynamical variables to a clustering vector.

The only provisional novelty residue is a calibrated cluster-level test of **incremental finite-time dynamical information beyond present-day compactness**, with a predictability-normalized horizon and matched real false groups. No first-ever claim is permitted without a complete literature review.

## Stage 0A — public-data feasibility audit

Use the public Global Meteor Network trajectory database, which provides shower labels, observation epochs, osculating orbital elements, anomaly, and quality/error fields.

Audit established-shower controls with IAU numbers:

- 4;
- 6;
- 7;
- 10;
- 13.

The audit must obtain the IAU codes from the data rather than assuming shower names. It must also obtain sporadic events (`IAU No = -1`).

### Required fields

- unique event identifier;
- observation UTC or Julian date;
- IAU shower number and code;
- solar longitude;
- semimajor axis, eccentricity, inclination;
- argument of perihelion and ascending node;
- true anomaly or mean anomaly;
- perihelion distance;
- convergence angle and trajectory-fit error;
- uncertainty fields if exposed by the downloadable trajectory summaries.

### Initial quality screen

- finite physically interpretable osculating elements;
- `0 < q < 1.3 AU`;
- `0 <= e < 1.2`;
- `0 < a < 100 AU` for the nominal bound-orbit pilot;
- convergence angle `Qc >= 10 deg` when available;
- median fit error `<= 300 arcsec` when available;
- at least two observing years per positive control.

### Pass conditions

1. At least four of the five established controls have at least 200 quality-screened events.
2. At least 2,000 quality-screened sporadic events are available for matched null construction.
3. Observation epoch and full six-element state reconstruction are possible for at least 95% of selected events.
4. At least one event-level uncertainty representation can be reconstructed from released one-sigma fields or a documented observational Monte Carlo product.
5. Selected controls span more than one dynamical regime rather than all being nearly identical high-activity streams.

Failure of conditions 1–3 kills the candidate immediately. Failure of condition 4 permits only a nominal-orbit surrogate and prohibits any predictability-normalized claim.

## Stage 0B — nominal-orbit incremental-information surrogate

This stage is not authorized until Stage 0A passes.

### Positive groups

For each established control:

- create event groups of sizes 6, 10, and 20;
- keep complete groups separate by year when possible;
- reserve at least one shower and one year from all score construction and matching decisions.

### Static-matched null groups

Construct sporadic pseudo-groups matched to each positive group on:

- median orbit or local orbit neighborhood;
- group size;
- observation-epoch span;
- median quality;
- present-day median and upper-quantile D-criterion dispersion.

Null groups must be as compact at the observation epoch as the positive groups. A loose random sporadic baseline is prohibited.

### Dynamics

- reconstruct heliocentric states at the observation epoch;
- propagate every event to a common reference epoch;
- include the Sun and major planets;
- evaluate both forward and backward evolution over a short prespecified maximum horizon;
- record close encounters and numerical failures;
- calculate dispersion curves in at least one established D-criterion and one observational/geocentric invariant representation.

### Predictability normalization

For each event, create prespecified perturbation clones from released uncertainty fields. Define the event's predictability horizon before the benchmark as the earliest of:

- clone-cloud dispersion exceeding a frozen physical threshold;
- a frozen close-encounter threshold;
- a frozen maximum integration time.

Group time is expressed as normalized time `tau = t / T_predictability`. Candidate and null groups are compared only over their common supported normalized interval.

If uncertainty fields are unavailable, Stage 0B may measure nominal dynamical surplus only and cannot claim predictability normalization.

### Primary statistic

The primary score is the area under the **coherence-surplus curve**:

`matched-null expected dispersion(tau) - observed group dispersion(tau)`,

after normalizing both by their present-epoch dispersion. The matched-null expectation is calculated without using the held-out positive group.

## Baselines

- present-day D_SH or D_N compactness alone;
- present-day geocentric compactness alone;
- unnormalized finite-time average D;
- minimum historical D;
- simple requirement that D stay below a threshold for a fixed time;
- optional OFLI or clone-divergence summary alone.

## Frozen continuation gates

A full dynamical benchmark is permitted only if all applicable gates pass on groups unrelated to GhostStream:

1. held-out positive-vs-null AUROC improves by at least 0.05 over the strongest static baseline;
2. partial AUROC at false-positive rate <= 0.10 improves by at least 0.05;
3. at a matched 10% false-positive rate, recovery improves by at least 10 percentage points;
4. at least three established controls show positive gain, including the completely held-out control;
5. gain remains positive after exact matching on present-day D dispersion;
6. no more than 10% of quality-screened groups fail state reconstruction or integration;
7. performance does not collapse when the integration maximum is halved;
8. if clones are available, gain remains after conditioning on predictability horizon and measurement quality;
9. the method rejects static-compact pseudo-groups that diverge dynamically rather than merely ranking all compact groups highly.

## Kill interpretations

- If positive and static-matched null groups have indistinguishable normalized dispersion curves, dynamics adds no useful information.
- If gain disappears after matching present-day compactness more tightly, the method is only rediscovering the D-criterion.
- If only one young or resonant shower benefits, the method is not a general stream-discovery contribution.
- If uncertainties erase nominal separation, the result is not observationally usable.
- If long integration is required beyond the predictability horizon, the score is physically uninterpretable.
- If the method only validates known parent associations, it does not solve blind stream discovery.

## Claim boundary after a pass

A pass would support only the provisional claim that predictability-normalized finite-time dynamics can add discriminative information beyond present-epoch orbital similarity for meteor-stream candidate validation.

It would not yet authorize GhostStream application, prove a common parent, establish stream age, or justify a first-ever claim.
