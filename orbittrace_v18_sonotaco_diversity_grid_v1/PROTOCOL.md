# OrbitTrace v18 — exposed SonotaCo diversity-grid development

## Scientific role

v17 is preserved as a successful broad-universe successor that beats Sugar in both 2013 and 2014 but still loses the HDBSCAN matched comparison under budgets 11 and 9. The remaining failure is concentrated in very-top-of-ranking efficiency: strong v17 families exist below the HDBSCAN cutoff while top slots include partial/redundant cores.

SonotaCo 2013/2014 is already exposed. This v18 stage is therefore explicitly **development**, not external validation. It may use the exposed labels to select among a pre-existing finite ranking grid, but every grid candidate must be generated and frozen before truth is loaded in the workflow and every result must be retained.

## Fixed candidate architecture

Candidate generation, learned quality scores, and membership are unchanged from v17:

1. exact #862 pair-portable hard/P19/P20 proposal universe;
2. v15 adaptive hard-family consensus over caps `(128,96,64)` with `K=min(cap,N_local)`;
3. exact serialized #853 ExtraTrees quality model and exact 34-feature #860 unseen-data application;
4. exact fixed #461/v16 joint density+trajectory conformal membership expansion for ranks 1–100, including alpha `0.05`, k=2, affine order 1, +/-6 degree activity padding, density/residual ceilings 1.5, equal Fisher weights, empirical joint recalibration, no recursive support.

No proposal, model, feature, membership, radius, threshold, activity padding, or support rule may change in v18.

## Frozen grid

v18 re-evaluates only the diversity grid that already existed in the pre-SonotaCo #839 ranker laboratory:

- lambda: `{0.0, 0.2, 0.4, 0.6, 0.8}`
- scale: `{0.75, 1.0, 1.5}`

All 15 combinations are generated for both comparator-matched label-free row universes. The frozen #839 diversity formula and tie rule are unchanged. v17 corresponds to `(lambda=0.8, scale=1.0)` and must reproduce its existing outputs/metrics within exact deterministic semantics.

## Evaluation and selection

After all 30 candidate outputs (15 configurations x 2 row routes) are hash-frozen, load the already-exposed immutable truth/comparator artifact from v15 run `31405109267` and evaluate every configuration using exact #854 equal-budget one-to-one F1 semantics.

For each configuration and each of four panels (Sugar 2013, Sugar 2014, HDBSCAN 2013, HDBSCAN 2014), record:

- candidate macro-F1;
- frozen literature-comparator macro-F1;
- candidate recovered showers with F1>0.5;
- frozen literature-comparator recovered showers with F1>0.5;
- macro-F1 ratio candidate/comparator;
- recovery ratio candidate/comparator;
- whether both pairwise superiority conditions are met.

A configuration is an **all-panel development win** only if, on all four panels, candidate macro-F1 is strictly greater than the literature comparator and candidate recovered-F1>0.5 count is at least the comparator count.

The single development winner is selected by this predeclared lexicographic key, maximized in order:

1. number of panels satisfying both superiority conditions;
2. minimum macro-F1 ratio across the four panels;
3. minimum recovery ratio across the four panels;
4. mean macro-F1 ratio across the four panels;
5. mean recovery ratio across the four panels;
6. smaller Euclidean parameter displacement from v17 `(0.8,1.0)` after scaling lambda by 0.8 and scale displacement by 0.75;
7. smaller lambda;
8. smaller scale.

The full 15-row result table is retained regardless of winner. No second grid, interpolation, threshold change, or post-result local search is allowed within v18.

If no configuration wins all four panels, v18 fails literature superiority and the complete grid becomes preserved development evidence for the next separately named architectural diagnosis. If a configuration wins all four, it is only a SonotaCo-developed candidate and still requires a separately preregistered protected validation before any external-replication claim.

## Firewalls

- No MAARSY scientific values.
- No DMS scientific values.
- No OrbitTrace target information or target-region event access.
- Solar longitude 20°–55° remains inaccessible to target-containing work.
- Original OrbitTrace discovery provenance remains historical blind HDBSCAN.
