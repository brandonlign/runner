# Frozen OrbitTrace catalogue-v3 block-runtime equivalence result

Authoritative equivalence run: `31184676837`

Authoritative job: `92886142797`

Evaluated implementation commit: `1030da330f732a2738d8968294ed47f65fc20e86`

Verdict: **`PASS_BLOCK_EXACT_RESCORE_EQUIVALENCE`**

The block implementation preserves the frozen per-anchor wavelet path exactly and vectorizes only fixed4's repeated full-window nearest-three distance calculation.

Authoritative checks:

- frozen catalogue source audit: PASS;
- frozen fixed4 support source SHA guard: PASS;
- scalar/block wavelet score maximum absolute difference: **0.0**;
- scalar/block fixed4 score maximum absolute difference: **0.0**;
- scalar/block positive-lobe memberships: **identical**;
- scalar/vectorized fixed4 nearest-three indices: **identical**;
- vectorized wrap180 edge cases: **identical**;
- fixed4 distance maximum absolute difference on the equivalence panel: **0.0**.

Informative synthetic benchmark on the GitHub runner:

- frozen grouped runtime: **0.923585071 s**;
- block runtime: **0.159324694 s**;
- speedup: **5.79687334×**.

Speed is not a scientific gate. The equivalence checks are the authorization boundary.

This pass authorizes only a rerun of the already-frozen target-excluded SonotaCo/GMN catalogue-v3 development on **2022–2023** using the wrapper that replaces `exact_rescore_window`. It does not authorize any 2024–2026 catalogue, OrbitTrace target reveal, threshold change, candidate-definition change, or scientific-method change.
