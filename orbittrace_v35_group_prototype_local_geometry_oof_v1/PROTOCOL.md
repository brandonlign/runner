# OrbitTrace v35 strict-group prototype local-geometry ranker v1

## Scientific role
Separately frozen exposed-SonotaCo development successor after diagnostic #1040 showed that perfect representative choice within v31's already-surfaced HDB shower labels is insufficient: the remaining barrier necessarily includes **which shower groups are surfaced**. Earlier #1002 independently localized a major HDB failure to unseen shower-group recognition, while v31 showed that parameter-free local geometry is the strongest current HDBSCAN-2014 near miss.

This experiment changes one structural element from v31: the fold-training reference set is compressed from individual candidate families to **one prototype per strict training group**, so the geometry learns recoverable-group structure rather than fragment density. It does not change the 71D representation, annual recovery threshold, fold assignment, metric, k, annual combiner, diversity, or v19 fusion.

## Exact strict groups and targets
Use the immutable #950 v22 71D pretruth payload and the same strict groups already used for whole-shower OOF:
- a truth-associated family belongs to `SHOWER/<best recurrent label>`;
- a nonassociated family retains its deterministic singleton `NEG/<route>/<family_id>` group;
- all members of a strict group remain in exactly one deterministic OOF fold.

For each year separately, a training strict group is annual-positive iff **any family in that group** has the existing frozen annual target `F1_y > 0.5` for that same fixed v22 recurrent label. No threshold is selected here.

## Sole ranking rule
For each OOF fold:
1. compute arithmetic mean and population standard deviation (`ddof=0`) of every one of the 71 features using fold-training **families only**, exactly as v31; replace exactly-zero standard deviations by 1.0;
2. standardize fold-training and held-out family features with those training-family statistics;
3. for every fold-training strict group, form one prototype as the arithmetic mean of the standardized features of **all training families in that group** across both Sugar/HDB routes; because strict groups are already the unit of the OOF firewall, no held-out family enters any prototype;
4. for each year, label each prototype positive iff any family in its strict group has annual F1 > 0.5; all remaining group prototypes are nonpositive;
5. for each held-out family, compute ordinary Euclidean distance to the single nearest positive group prototype and the single nearest nonpositive group prototype;
6. annual margin is `d_nonpositive - d_positive`;
7. combine annual margins with exact frozen v24/v31 rule `min(margin_2013, margin_2014)`.

No prototype weighting, medoid selection, robust mean, route-specific prototype, minimum group size, k search (`k=1` only), metric search, feature weighting/subset, threshold, calibration, covariance correction, or source quota is authorized.

## Frozen post-score machinery
For each route independently apply exact #839 diversity (`lambda=0.8`, `scale=1.0`) to the combined margin, then exactly one equal rank-sum with the immutable v19 order. Only that fused order is a promotion candidate. No local-only order, rank product, sequential fusion, alternate diversity, fusion weighting, or route/year switching is evaluated.

## Binding gate
The first technically valid execution is binding. PASS requires the sole fused order to beat the corresponding literature comparator in all four Sugar/HDBSCAN 2013/2014 panels: macro-F1 strictly higher and recovered F1>0.5 count at least equal in every panel. Otherwise this exact group-prototype architecture is permanently rejected; no prototype definition, k, metric, feature, annual combiner, diversity, or fusion rescue is authorized.

A full exposed-SonotaCo prototype reference package may freeze only after a 4/4 OOF PASS. SonotaCo 2013/2014 remains exposed development-only, not pristine external validation. MAARSY, DMS, OrbitTrace target information, target-region events, and protected solar longitude 20-55 degrees remain inaccessible.
