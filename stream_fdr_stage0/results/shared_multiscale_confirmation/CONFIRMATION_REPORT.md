# Multiplicity-calibrated multiscale confirmation

Authoritative runner workflow: `30842450469`

Artifact: `shared-network-multiscale-confirmation` (`8867403198`)

Artifact digest: `sha256:f84df015075780a86169554e23dc209783d77ff5653a0060e9129e04d98fc023`

## Verdict

**KILL_OR_REDESIGN_SHARED_NETWORK_FORMULATION**

The frozen primary method maximized a leave-one-network-out local excess score over candidate locations and radii `{0.70, 0.90, 1.10, 1.30}`. The complete multiscale search was calibrated under independent null scenes. GhostStream was excluded.

## Main results

- independent-null FPR: **0.028**; Wilson 95% interval **[0.008, 0.096]**;
- balanced mean recovery: **0.444** versus pooled **0.413**; gain **0.031**, paired-bootstrap 95% **[0.000, 0.066]**;
- heterogeneous mean recovery: **0.340** versus pooled **0.410**; gain **-0.069**, paired-bootstrap 95% **[-0.108, -0.031]**;
- GMN-only artifact recovery: **0.000**;
- strong shared recovery: **1.000**;
- no-GMN balanced recovery: **0.594** versus pooled **0.229**;
- M2026-A1 external control accepted near the published trajectory, distance **0.269**.

## Recovery by dispersion

| Condition | leave-one-out | pooled |
|---|---:|---:|
| balanced compact | 0.688 | 0.635 |
| balanced nominal | 0.521 | 0.500 |
| balanced diffuse | 0.125 | 0.104 |
| heterogeneous compact | 0.552 | 0.646 |
| heterogeneous nominal | 0.406 | 0.490 |
| heterogeneous diffuse | 0.062 | 0.094 |

## Interpretation

The cross-network premise is not disproven: the primary method controlled errors, rejected a single-network artifact, survived removal of GMN, and found the external control. The failed element is the hard dominance protection. Removing the largest contribution throws away legitimate evidence whenever survey sensitivities or stream amplitudes differ.

The only justified redesign is a shared latent-flux likelihood in which each network retains its own background while network counts are linked by one nonnegative stream-strength parameter, with optional exposure terms. This must be tested on new independent scenes and must continue to reject a one-network artifact. The failed leave-one-out score cannot be presented as a successful method.
