# Far-Outlier Core Refinement (FOCR) v1

## Motivation and development status

BWM v1 proved that persistence-witness modularity can make support-pruned TopoModal families much smaller, but it over-segmented ordinary families and lost recall. Core-Majority Regrowth (CMR) v1 recovered part of that recall but still underperformed the promoted support-pruned baseline when applied to every parent.

FOCR v1 therefore changes **where** refinement is allowed, not the underlying refinement. Normal support-pruned families are preserved exactly. Only extreme size outliers are replaced by the already-frozen CMR children from pretruth SHA-256 `8b77e80f305c6f47fc70b359bf03ebadcd6263b5d5ee6a6b9c30efda658bffcb`.

This rule is being designed after BWM/CMR target-excluded GMN development results were observed. GMN 2022/2023 is therefore explicitly a development set for FOCR v1, not an untouched validation set. OrbitTrace protected-region events/IDs/coordinates and SonotaCo truth remain prohibited from method construction.

## Frozen selector

For each of the eight exact target-excluded GMN sparse panels independently:

1. Take the member counts of **all** promoted support-pruned parent candidates in that panel.
2. Compute `Q1` and `Q3` with NumPy's default linear quantile definition.
3. Let `IQR = Q3 - Q1`.
4. Define Tukey's standard **outer upper fence** `F = Q3 + 3 * IQR`.
5. If a support-pruned parent has `member_count > F`, replace that parent by the frozen CMR v1 candidates having that exact parent family hash.
6. Otherwise retain the support-pruned parent unchanged.
7. Rank the resulting candidate catalogue by the unchanged exact M2D score descending, then membership hash.

The factor 3 is the conventional Tukey outer-fence definition for extreme outliers. It is not fit to GMN shower labels, OrbitTrace membership, or a target-family size. No alternative fence multiplier is authorized within FOCR v1.

## Prohibitions

FOCR v1 may not access OrbitTrace canonical IDs, target coordinates, the protected `[20°,55°]` events, prior target-family ranks/sizes, SonotaCo labels, or external-survey target truth during construction. It may not change CMR memberships, run a new modularity partition, change M2D, add a score blend, impose a hand size cap, or rescue a failed result after labels.

## Development evaluation

Use the exact PR #1377 comparator-capacity semantics and byte-frozen BWM hidden-label evaluator:

- `k = len(published comparator clusters)` per panel/year/comparator;
- FOCR uses the first `k` frozen FOCR candidates;
- promoted support-pruned v1 is evaluated identically;
- no padding;
- one-to-one Hungarian macro-F1 and `F1 > 0.5` recovery are unchanged.

The strict inherited ten gates remain the target for development: nonlower F1 and recovery against support-pruned v1 on Sugar, HDBSCAN, coarse, and fine routes, while preserving both published-configuration literature wins.

A GMN pass is only a development qualification. Any claim of generalization requires a subsequent frozen transfer test on a non-GMN endpoint not used to choose FOCR.