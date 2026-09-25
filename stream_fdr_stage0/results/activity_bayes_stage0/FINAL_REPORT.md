# Activity-marginalized Bayes scan — final no-go

Authoritative runner workflow: `30846705722`

Artifact: `activity-bayes-stage0` (`8868979979`)

Artifact digest: `sha256:27532f26357674d7ca011b1ffb51d7736d79410ea2fd947ee5d334f4777f26ee`

## Verdict

**KILL_ACTIVITY_MARGINALIZED_BAYES_DIRECTION**

The primary integrated over all 99 activity subsets spanning at least three of seven years and four fixed active-year concentration levels. The complete candidate-center and radius search was calibrated on independent real GMN null scenes. GhostStream was excluded.

## What worked

- primary FPR: **0.055**, Wilson 95% **[0.027, 0.109]**;
- M2026-A1 accepted and localized **0.330** standardized units from the published reference;
- log Bayes factor **14.875** versus threshold **11.813**;
- broad-ridge acceptance **0.073**;
- late-onset recovery **0.135**, higher than pooled (**0.073**) and recurrent-deviance (**0.052**) baselines.

## Fatal failures

- recurring-sparse recovery **0.094** versus pooled **0.146**;
- sparse paired gain **-0.052**, bootstrap 95% **[-0.104, -0.010]**;
- recurring-moderate recovery **0.292**;
- intermittent recovery **0.083**;
- diffuse recovery **0.010**;
- drifting recovery **0.000**;
- strong recovery **0.729**, below the frozen 0.90 gate;
- one-year-artifact acceptance **0.156**, above the frozen 0.10 ceiling.

## Interpretation

Marginalizing activity patterns solves part of the late-onset problem and can identify the untouched real control, but it does not improve sparse recurring recovery over simple local scans and remains vulnerable to sufficiently strong one-year spikes. Adjusting the activity prior, minimum active years, alternative concentration levels, or artifact penalty after observing these results would be result-driven tuning.

The activity-marginalized Bayes direction is therefore closed for GhostStream. No prior tuning or M2026-driven redesign is authorized.
