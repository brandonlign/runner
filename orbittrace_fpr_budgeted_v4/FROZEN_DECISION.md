# OrbitTrace FPR-budgeted dual channel v4 — frozen development decision

Selection workflow: `31146852225`

Selection artifact: `8981784838`

Selection artifact digest: `sha256:1fd9aec02f915dd2aa3b94dfa5cdbc8b061987777070e581277ddef5a784fcdd`

Selector source commit: `7388036a1773860ea68db0788e8291cd21b97dbf`

Verdict: **`PASS_V4_DEVELOPMENT_SELECTION`**

## Frozen architecture

Continuous ranking:

- unchanged `orbittrace_multi_anchor_wavelet_energy_v3`.

Reporting decision:

- v3 primary channel: `p_v3 <= 3/129`;
- fixed4 sparse channel: `p_fixed4 <= 4/129`;
- combined detection: `(p_v3 <= 3/129) OR (p_fixed4 <= 4/129)`.

These integer thresholds are now frozen. They may not be changed from any transfer or validation result.

## Development result on SonotaCo 2025

The selector evaluated all 36 pairs with ranks 1–6 for each channel. Five pairs were feasible under the preregistered FPR and recall requirements. The deterministic minimum-FPR selection rule chose `(3,4)`.

- pooled FPR: **0.043457**;
- recall k=4: **0.154412**;
- recall k=6: **0.573529**;
- recall k=8: **0.823529**;
- recall k=12: **0.955882**.

For comparison, the frozen gate references were:

- fixed4 k=4 recall: `0.154412`;
- Brown-family wavelet k=6/8/12: `0.595588 / 0.830882 / 0.948529`;
- allowed tolerance at k=6/8/12: `0.03`.

The continuous ranking AUROC remains the frozen v3 value **0.836860**, above Brown-family wavelet **0.828506**.

## Interpretation boundary

This is development selection, not validation. The architecture is eligible only for unchanged transfer and later prospective validation. No transfer result may alter the v3 score, the fixed4 score, or the `(3/129, 4/129)` thresholds.
