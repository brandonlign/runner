# Binding result — matched-capacity GMN literature fairness v1

Binding execution: GitHub Actions run `32156065072` (execution-only PR #1330), exact frozen science commit `a6068835f7af005699919dfc57d45688b9ea6787`.

Artifact: `9331799095`, `orbittrace-recurrent-eom-gmn-literature-fairness-v1-binding`, artifact digest `sha256:aacd6cc6e99d4509f0beb0431cd4e699f27e92cbf859c69d4183cae793658217`.

Binding result JSON SHA-256: `6c3c7fe927b80f5913088d3698609d07cca0174a95650b6cd6ec69712e31a0ff`.

Verdict: `PASS_RECURRENT_EOM_GMN_MATCHED_CAPACITY_LITERATURE_4_OF_4`.

## Exact matched-capacity panels

- Sugar deterministic core 2022, K=525: recurrent-EOM macro-F1 `0.41018804867300057`, recovered F1>0.5 `159`; Sugar `0.15607673680944167`, `51` — PASS.
- Sugar deterministic core 2023, K=751: recurrent-EOM `0.4331949968930268`, `168`; Sugar `0.18674791207442026`, `59` — PASS.
- Catalogue-HDBSCAN 2022, K=74: recurrent-EOM `0.16040268706433455`, `69`; HDBSCAN `0.11783144148783989`, `43` — PASS.
- Catalogue-HDBSCAN 2023, K=88: recurrent-EOM `0.18634099000659957`, `79`; HDBSCAN `0.13235618973750005`, `57` — PASS.

The fairness audit therefore confirms that the direct-GMN advantage is not solely a consequence of recurrent-EOM exposing 2,097 candidates. The HDBSCAN margin shrinks substantially under equal capacity, as expected, but remains a clean two-year win in both macro-F1 and recovered-shower count.

## Claim boundary

This supports direct GMN superiority to the tested comparator implementations at equal catalogue capacity. The GMN Sugar implementation remains the deterministic published DBSCAN core rather than the full uncertainty-resampling pipeline. MRR is not defined head-to-head because the literature catalogues are unordered.

This result does not establish pristine cross-survey generalization. The prior NASA ASFN 2018/2019 negative validation remains binding and is not altered or rescued by this audit. No protected target data or new external-survey scientific data were accessed.
