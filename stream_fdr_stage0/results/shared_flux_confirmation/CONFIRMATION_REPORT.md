# Shared latent-flux confirmation

Authoritative runner workflow: `30843045613`

Artifact: `shared-latent-flux-confirmation` (`8867682902`)

Artifact digest: `sha256:9fefa4ec1524f3d0297fb1a94343d39830c70ffab4a69d9c2fb075be6e90c899`

## Verdict

**KILL_OR_REDESIGN_SHARED_FLUX_METHOD**

The primary method used a joint Poisson profile likelihood with one nonnegative latent stream rate and separate network backgrounds. The full candidate-location and multiscale search was calibrated under independent null scenes. GhostStream was excluded.

## Results

- independent-null FPR: **0.073**, Wilson 95% **[0.036, 0.143]**;
- combined weak recovery: **0.553** versus pooled **0.533**;
- gain: **0.021**, paired-bootstrap 95% **[0.003, 0.039]**;
- dominant shared recovery `(2,8,2,2)`: **0.211** versus pooled **0.359**;
- three-network recovery: **0.227**;
- GMN-only artifact recovery: **0.016** versus pooled **0.141**;
- strong shared recovery: **1.000**;
- no-GMN recovery: **0.453** versus pooled **0.523**;
- external M2026-A1 control accepted near the published trajectory, distance **0.348**.

## Interpretation

The shared-flux likelihood is well calibrated and suppresses single-network artifacts, but its power gain over pooled search is too small and it loses substantial power when a real stream is strongly survey-dominant or absent from one network. The common-amplitude constraint is therefore too restrictive, while relaxing it would approach an unprotected sum or require difficult survey-selection modeling.

This result kills the current shared-network methodology direction. It may remain a future specialized replication test, but it is not strong enough to serve as GhostStream's major methodological contribution. No further dominance penalties, random-effects tuning, or GhostStream application are authorized from this branch of work.
