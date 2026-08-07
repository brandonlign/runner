# OrbitTrace v7 joint-rank sparse-rescue development protocol

## Status

This is a successor-development experiment after the frozen v6 SonotaCo 2018 prospective failure. It does not alter v3, fixed4, Brown, v5, v6, or any prior result.

The exposed development evidence is SonotaCo 2025, 2023, 2024, and 2018. **SonotaCo 2017 is reserved for a future prospective test and must not be accessed for method performance during this development stage.** No 2017 labels, scores, p-values, recalls, FPRs, AUROCs, candidate identities, or threshold diagnostics may be used.

## Frozen two-channel inputs

The continuous channel is the already-frozen OrbitTrace v3 multi-anchor wavelet-energy p-value. The sparse channel is the already-frozen fixed4 p-value. Both are denominator-513 empirical p-values from the high-resolution calibration architecture. Neither score is retrained or modified here.

## Preregistered rule family

Exactly **19,604** deterministic rules are evaluated:

`(rank_v3 <= r_primary) OR ((rank_fixed4 <= r_fixed4) AND (rank_v3 * rank_fixed4 <= B))`

where:

- `rank_v3 = 513 * p_v3` and `rank_fixed4 = 513 * p_fixed4`, each required to be an exact positive integer calibration rank;
- `r_primary` ranges from 1 through 26;
- `r_fixed4` ranges from 1 through 26;
- `B` ranges from 32 through 256 in increments of 8.

The product condition is the only new v7 structural idea. It tests whether a sparse fixed4 rescue can be admitted when the **joint rank evidence** from the two frozen channels is sufficiently strong, without using shower identity, solar-longitude targeting, OrbitTrace coordinates, or target membership.

## Frozen cross-year gates

Every candidate rule must pass every gate separately in **2025, 2023, 2024, and 2018**:

1. frozen v3 weak-signal AUROC remains at least the frozen Brown-family AUROC;
2. pooled held-out false-positive rate `<= 0.055`;
3. worst reporting-sector false-positive rate `<= 0.08`;
4. k=4 recall is at least the frozen fixed4 k=4 reference for that year;
5. k=6, k=8, and k=12 recall are each no more than 0.03 below the frozen Brown-family reference for that year.

The predecessor reference numbers are fixed before this grid is run. The failed 2024 and 2018 prospective results are preserved as development evidence for this successor only; they are not rewritten as prior passes.

## Deterministic selection

If multiple rules pass all gates, selection is deterministic:

1. maximize the minimum recall margin across all 16 year-by-k recall constraints;
2. minimize the maximum pooled FPR across years;
3. minimize the maximum worst-sector FPR across years;
4. minimize product budget `B`;
5. maximize the primary v3 rank threshold;
6. minimize the fixed4 rank threshold.

If no rule passes, v7 is a frozen no-go. A failed development result does **not** authorize SonotaCo 2017 access.

## Claim boundary

A development pass would authorize a separately frozen prospective SonotaCo 2017 validation only. It would not establish blind catalogue rediscovery, OrbitTrace recovery, or historical discovery provenance. A development failure preserves the separately validated v3 ranking and fixed4 sparse channel; it only rejects this unified joint-rank Boolean architecture.
