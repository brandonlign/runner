# Sequential predictive evidence v1 — geometric-null no-go

Authoritative corrected runner workflow: `30844481682`

Artifact: `predictive-eprocess-stage0-corrected` (`8868120353`)

Artifact digest: `sha256:751fd9d6dfe4d37de9e690d0740238efae3347a19306bed580e25dbe93d91cee`

## Verdict

**KILL_OR_REDESIGN_PREDICTIVE_EPROCESS**

The candidate search used only earlier years and each evidence increment used an unseen year, but the year-level likelihood ratio assumed a locally uniform three-dimensional background with `p0=(1/2.5)^3`. GhostStream was excluded.

## Null behavior

| Method | Acceptance | Wilson 95% |
|---|---:|---|
| multi-order adaptive | 0.336 | [0.260, 0.421] |
| chronological adaptive | 0.242 | [0.176, 0.323] |
| fixed candidate | 0.078 | [0.043, 0.138] |
| single split | 0.102 | [0.060, 0.166] |
| naive same-data | 0.977 | [0.933, 0.992] |

Individual prespecified year-order null acceptance ranged from 0.195 to 0.250. The theoretical `E >= 10` error bound therefore failed badly on real meteor backgrounds.

## Power and controls

- recurring, intermittent, late-onset, diffuse, and strong injections all reached 1.000 primary recovery;
- one-year-artifact primary acceptance was 0.260, although only 0.021 localized on the injected artifact;
- M2026-A1 was accepted with `E=18.044` and localized 0.638 standardized units from the reference.

The injection design saturated, so it could not establish an advantage over the chronological adaptive baseline, which also recovered all recurring-weak scenes.

## Interpretation

The failure is not evidence against predictive testing itself. It demonstrates that a geometric volume ratio is not a valid conditional null for the persistent, anisotropic meteor background. Adaptive candidate updates repeatedly select recurring background structure, causing nominal e-values to grow under real null scenes.

The protocol permits one principled redesign: replace the geometric null with prespecified, held-out-year matched analogue ranks. Further radius tuning, mixture-weight tuning, or threshold calibration is prohibited.
