# Fixed-scale TopoModal flagship — final matched literature benchmark protocol

## Role

This is a **benchmark-only post-selection evaluation** of the already-frozen fixed-scale TopoModal flagship. It does not modify the detector, its physical scale, graph, density estimator, ToMATo hierarchy, support floor, candidate construction, or candidate ordering.

The benchmark uses only the already-exposed SonotaCo 2013/2014 development/validation corpus outside the protected solar-longitude interval `[20.0,55.0]` inclusive. It is not pristine external validation.

## Frozen flagship

The exact flagship scientific source is the already-bound `orbittrace_topomodal_sparse_recovery_v1/run_development.py` Git blob:

`752df8212ce601227f6e9170b0fe994ba06b515d`

Its configuration remains exactly:

- solar physical halfwidth: 5 deg (`h_sol = 2 sin(5 deg / 2)`);
- radiant physical halfwidth: 4 deg (`h_rad = 2 sin(4 deg / 2)`);
- speed scale: 10% (`h_logv = ln 1.1`);
- exact Euclidean radius graph `r=1`;
- radius-count density divided by catalogue size;
- GUDHI ToMATo manual graph/manual density;
- complete mode-merging hierarchy;
- minimum candidate support 4;
- exact frozen candidate ordering from the sparse-recovery source.

For each comparator, TopoModal is rerun from scratch on exactly that comparator's pooled 2013+2014 label-free row universe. The complete candidate order is persisted and SHA-256 frozen before shower truth opens.

## Comparators

Exactly three representative literature methods are frozen. No additional method may be added after any benchmark result is seen.

### A. Sugar et al. (2017) uncertainty-aware DBSCAN

Use the already-audited full uncertainty-aware catalogue pipeline, source SHA-256:

`5b7699a2cf07b9b9ac6dee006c66a9b509af73ee3763093fa333d13e1deca0cb`

with the already-frozen rules:

- published six-dimensional Sun-centered geocentric feature vector;
- DBSCAN min samples 5;
- epsilon = 23rd percentile of fourth non-self-neighbor distance;
- 1000 uncertainty-clone realizations;
- cluster-overlap merge fraction 0.5;
- minimum recurrence 100/1000;
- deterministic seed root 20170209;
- exact previously-audited SonotaCo uncertainty / convergence-angle eligibility.

### B. Pena-Asensio & Ferrari (2025) catalogue HDBSCAN

Use the already-audited faithful catalogue implementation, source SHA-256:

`a8b638f56dad2597973178523e8ad15e177a4f57e7fe6159fedc84d754afd3d2`

with:

- HDBSCAN 0.8.44;
- GEO six-dimensional representation;
- `min_cluster_size=100`;
- `min_samples=None` (package default tied to minimum cluster size);
- Euclidean metric;
- EOM cluster selection;
- zero cluster-selection epsilon;
- exact previously-audited catalogue-quality eligibility.

### C. Rudawska & Jenniskens (2014) Southworth-Hawkins single linkage

Use the published catalogue rule without tuning:

- Southworth-Hawkins `D_SH` orbit dissimilarity;
- orbital fields `(q,e,i,omega,Omega)`;
- single-link connected components with strict `D_SH < 0.05`;
- minimum component membership 6;
- no truth-informed merging, splitting, threshold alteration, or ranking.

The D_SH implementation must be numerically audited before execution against the already-audited dense `pairwise_dsh` primitive in Git blob `ab17e1205d72d8ab8361d8ba6cdad2e4c31fdcb2`. The scalable implementation may use exact necessary prefilters (`|dq|<0.05`, `|de|<0.05`) because every omitted pair is mathematically incapable of satisfying `D_SH < 0.05`; all retained candidate pairs receive the exact D_SH calculation.

## Same-information row universes

The pre-existing SonotaCo label-free normalizer Git blob is fixed as:

`0264546418d0b50fa53514a6ba170f7c3e33d4d3`

It removes `[20.0,55.0]` immediately after solar longitude decoding and before any other scientific field is decoded.

Three comparator-specific universes are frozen pretruth:

1. `sugar`: exact existing Sugar pairwise eligibility;
2. `hdbscan`: exact existing catalogue-HDBSCAN pairwise eligibility;
3. `dsh`: base retained SonotaCo geometry plus finite `q,e,peri,node,inc` required by the published D_SH criterion.

For each comparator, both TopoModal and the comparator receive exactly the same annual row IDs.

## Evaluation

Use the exact already-frozen matched literature evaluator SHA-256:

`cefcc8900a7b3d083f81148427e9f80e2c7192bb25dd9bb635e6677aa23a555c`

and the existing SonotaCo -> eligible MDC complex truth mapping SHA-256:

`f8ba2446dce96d69652727092189903c40493e2fe741eb746f7fb5181edea778`

For each comparator and each year independently:

1. let `B` equal the number of non-noise literature families produced before truth;
2. evaluate all `B` literature families;
3. evaluate the first `min(B, N_topomodal)` frozen TopoModal candidates;
4. use the identical annual row universe and truth mapping;
5. apply the exact maximum-F1 one-to-one Hungarian assignment;
6. report macro-F1 and recovered known-shower count with assigned F1 > 0.5.

A panel is a **TopoModal WIN** iff:

- `TopoModal macro-F1 > literature macro-F1`, and
- `TopoModal recovered(F1>0.5) >= literature recovered(F1>0.5)`.

The final token `PASS_TOPOMODAL_FLAGSHIP_MATCHED_LITERATURE_V1` requires WIN on all six panels:

- Sugar 2013 / 2014;
- published HDBSCAN 2013 / 2014;
- D_SH single linkage 2013 / 2014.

A technically valid failure is binding. There is no comparator-specific rescue, parameter change, alternate threshold, changed candidate budget, row-subset alteration, ranking change, or replacement comparator after results.

## Claim boundary

A six-panel PASS supports the statement that the frozen TopoModal flagship **outperformed representative contemporary and classical literature methods on the matched exposed SonotaCo 2013/2014 benchmark**. It does not establish universal superiority over all published methods or pristine cross-survey external validation.

## Firewall

Every stage must preserve:

- `blind_exclusion=[20.0,55.0]`;
- `target_information_access=false`;
- `target_region_events_accessed=false`;
- `orbittrace_target_access=false`;
- `maarsy_scientific_access=false`;
- `dms_scientific_access=false`;
- `truth_access_before_pretruth=false`;
- `post_result_parameter_search=false`.
