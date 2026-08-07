# OrbitTrace corroborated sparse rescue — v6 development protocol

## Preservation and motivation

v6 does not change any predecessor score. The continuous primary ranking remains frozen `orbittrace_multi_anchor_wavelet_energy_v3`; the sparse score remains frozen `orbittrace_fixed4`; Brown-family wavelet remains the literature ranking comparator.

The frozen v5 prospective SonotaCo 2024 result failed only its pooled-FPR gate (`0.060133 > 0.055`). Every recall gate passed, worst-sector FPR passed, and v3 again exceeded Brown in raw weak-stream AUROC (`0.855869 > 0.850314`). Inspection of the now-exposed development records showed that the v3 primary channel itself remained below the pooled-FPR cap and that the excess arose from the unrestricted OR rescue adding fixed4-only background detections.

The successor question is therefore narrow and fixed before selection: **can fixed4 remain a sparse rescue only when the continuous v3 ranking provides weak corroborating evidence?**

Existing v1–v5, fixed4, Brown-wavelet, prior dual-channel, Sugar, HDBSCAN, catalogue, and blind-recovery records remain untouched.

## Development evidence

v6 development uses only already exposed records from **2025, 2023, and 2024**:

- SonotaCo 2025 v5 high-resolution development;
- SonotaCo 2023 v5 high-resolution development;
- the frozen failed SonotaCo 2024 v5 prospective run, which is development evidence for successors after its one-shot failure was preserved.

No 2018 method-performance result may be opened during v6 development. **SonotaCo 2018** is reserved for a later one-shot prospective validation if v6 development passes and is frozen first.

## Frozen rule family

All p-values in this development stage are the already generated 512-null conservative empirical p-values on denominator 513.

For integer ranks, the candidate reporting rule is exactly:

`(p_v3 <= r_primary/513) OR ((p_fixed4 <= r_fixed4/513) AND (p_v3 <= r_corroboration/513))`.

The finite preregistered grid is:

- `r_primary in {1, ..., 26}`;
- `r_fixed4 in {1, ..., 26}`;
- `r_corroboration in {26, ..., 128}`.

This is exactly **69,628** candidate rules. `r_corroboration` is intentionally at least 26: the rescue may require weaker v3 evidence than the primary detection threshold, but it cannot become a completely uncorroborated fixed4 OR channel.

The complete 69,628-rule grid must be preserved in the development artifact. No rule outside this family may be substituted after results are opened.

## Frozen predecessor references

The success targets do not move with v6. For 2025 and 2023, the comparison recalls remain the exact immutable original 128-null predecessor metrics used by v5 development. For 2024, the references are the exact first-128/denominator-129 fixed4 and Brown outcomes preregistered and recorded in the frozen v5 prospective result.

Per year, the reference requirements are:

- k=4: at least predecessor fixed4 nominal-alpha=.05 recall;
- k=6, k=8, k=12: at least predecessor Brown nominal-alpha=.05 recall minus `0.03`.

Raw v3 AUROC must remain at least raw Brown AUROC in each development year.

## Per-year feasibility gates

A candidate rule is feasible only if **every** gate passes separately on all three development years:

- v3 weak-stream AUROC >= Brown-family wavelet weak-stream AUROC;
- pooled held-out-negative FPR <= `0.055`;
- worst reporting-sector FPR <= `0.08`;
- k=4 recall >= the frozen predecessor fixed4 k=4 reference;
- k=6 recall >= frozen predecessor Brown k=6 recall minus `0.03`;
- k=8 recall >= frozen predecessor Brown k=8 recall minus `0.03`;
- k=12 recall >= frozen predecessor Brown k=12 recall minus `0.03`;
- all v3 and fixed4 p-values lie exactly on the denominator-513 grid;
- input records match their exact frozen workflow artifacts.

## Deterministic selector

If no candidate is feasible, v6 fails.

If candidates are feasible, selection is deterministic in this order:

1. largest **minimum recall margin** across all 12 year-specific recall constraints;
2. lowest **maximum pooled FPR** across 2025, 2023, and 2024;
3. smallest `r_corroboration` (strongest corroboration requirement);
4. largest `r_primary` (prefer evidence from the primary continuous ranking when otherwise tied);
5. smallest `r_fixed4`;
6. lexicographic `(r_primary, r_fixed4, r_corroboration)` as a final deterministic tie-break.

No selector criterion may change after the development records are opened by the authoritative workflow.

## Promotion boundary

A passing development result freezes the exact three integer ranks and the corroborated-rescue Boolean rule. It does not change v3, fixed4, Brown, the 512-null calibration architecture, or any predecessor result.

Only after that freeze may SonotaCo 2018 be accessed in transport-only and score-free eligibility stages followed by one prospective scientific execution. No 2018 score, empirical detector p-value, recall, FPR, AUROC, threshold result, or method-performance comparison may be inspected before the v6 development freeze is committed.

A prospective 2018 failure must be preserved; same-2018 retuning is prohibited.
