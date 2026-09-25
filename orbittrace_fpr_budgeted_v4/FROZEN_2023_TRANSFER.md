# OrbitTrace v4 — frozen SonotaCo 2023 transfer

Workflow: `31147442432`

Job: `92769748730`

Artifact: `8982023596`

Artifact digest: `sha256:7e89ebbe8d1cbec9e8150a6d48211ee2805a6144dfa90a3fa6b5b274509c988e`

Scientific source commit: `5184a49e448b5adee3a1f9b80b2348d451cfd2a1`

Adapted 2023 v3 runner digest: `sha256:b479b5fced4e446969ab63604660c51741be95f204012758d2bfc6bf1f707e52`

Verdict: **`FAIL_V4_SONOTACO_2023_TRANSFER`**

## Frozen architecture

No 2023-specific threshold selection occurred. The transferred rule was exactly:

`(p_v3 <= 3/129) OR (p_fixed4 <= 4/129)`

where v3 is the unchanged multi-anchor wavelet-energy ranking and fixed4 is the unchanged sparse channel.

## Transfer result

The continuous v3 ranking transferred successfully:

- v3 weak AUROC: **0.836263**;
- Brown-family wavelet: **0.831972**;
- fixed4: **0.811631**.

The frozen v4 reporting decision produced:

- pooled FPR: **0.055871** vs cap `0.055`;
- worst-sector FPR: **0.072917** vs cap `0.08`;
- k=4 recall: **0.201220** vs fixed4 `0.189024`;
- k=6 recall: **0.536585** vs Brown `0.542683`;
- k=8 recall: **0.762195** vs Brown `0.798780`;
- k=12 recall: **0.926829** vs Brown `0.920732`.

All provenance, parser, benchmark, count, calibration-grid, source-integrity, AUROC, sector-FPR, k=4, k=6, and k=12 gates passed. Two preregistered gates failed:

- `combined_fpr_at_most_0055` — `0.055871 > 0.055`;
- `k8_within_003_of_wavelet` — the v4 deficit to Brown was `0.036585`, exceeding the allowed `0.03` by `0.006585`.

## Interpretation

This is a real transfer failure of the **v4 binary OR decision**, not a failure of the v3 continuous ranking. The ranking independently remained above Brown-family AUROC in both 2025 development and 2023 transfer.

The `(3/129, 4/129)` v4 thresholds remain frozen. They may not be altered using the 2023 result. Any successor must be separately named and must address the decision geometry rather than silently retuning v4.
