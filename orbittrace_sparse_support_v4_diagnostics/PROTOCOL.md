# OrbitTrace sparse-support v4 structural diagnostic protocol

## Purpose

Diagnose the completed sparse-support v4 development failure without changing v4, reopening catalogue data, tuning thresholds, or searching fusion weights.

This stage is diagnostic only. It is allowed to inspect the already-exposed target-excluded 2022–2023 development artifacts from:

- sparse-support v4 run `31190719956`, artifact `8999436151`;
- frozen fixed4 development run `31106001133`, artifact `8971289223`.

It must not parse any meteor catalogue, access 2024–2026 data, or access OrbitTrace coordinates, activity, members, or identity.

## Frozen diagnostic questions

1. Did v4 fail because the 197-family proposal scaffold lost known-shower capacity?
2. Did the 512-null empirical calibration retain enough resolution to rank the fixed4 proposals?
3. Does multi-anchor v3 provide ranking information materially distinct from the Brown comparator on this scaffold?
4. Did the fixed equal-weight RRF fail because it traded away fixed4 recoveries for insufficient v3 gains?

## Exact checks

- Verify exact SHA-256 digests for the v4 development JSON, v4 rankings, v4 family-score artifact, and frozen fixed4 development JSON.
- Reconstruct the fixed4 persistence evaluation and all top-100 recovered-label sets from the unchanged family universe.
- Measure the fraction of all 394 candidate family/year v3 and Brown empirical p-values equal to the exact floor `1/513`.
- Measure v3/Brown family-rank Spearman and Kendall correlations, minimum-score Spearman correlation, and top-100 family overlap.
- Measure v3/fixed4 and RRF/fixed4 top-100 family overlap.
- Record every known-shower label crossing the top-100 boundary relative to fixed4 for v3, Brown, and RRF.
- Record v3/Brown score-ratio distribution only as a descriptive diagnostic; do not create a new ranking from it.

For the diagnostic classification only, call v3 and Brown near-collinear when rank Spearman is at least `0.995` and top-100 family overlap is at least `95/100`. This threshold is fixed before the GitHub Actions run and is not a performance gate for any successor detector.

## Interpretation boundary

A saturated empirical p-value panel means the preregistered recurrence p-value/Fisher ranking cannot distinguish the proposals at the chosen null resolution; it does not by itself imply that v3 lacks all useful information. Near-collinearity with Brown means the promoted multi-anchor score contributes little independent ordering information on this particular fixed4 proposal scaffold.

Do not respond to a failed v4 gate by searching RRF weights, changing top-k thresholds, or increasing/decreasing a p-value cutoff on the same result. Any successor methodology must be separately named and must change the information used for ranking or proposal generation for a structural reason.
