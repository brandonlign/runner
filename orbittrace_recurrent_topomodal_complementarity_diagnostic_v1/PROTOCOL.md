# OrbitTrace recurrent-EOM × TopoModal complementarity diagnostic v1

## Scientific role

This is an **exposed SonotaCo development diagnostic and reproducibility audit only**. It does not alter, fit, rank, select, or promote a method, and it is not a pristine validation endpoint.

The provisional HDBSCAN-route intersection (21 of 32 recurrent-EOM candidate-generation failures recoverable somewhere in the frozen TopoModal candidate universe) was inspected interactively before this file was committed. Therefore this document **must not be described as a blind preregistration of that outcome**. Its purpose is to freeze an exact, auditable reproduction before any successor method is designed or benchmarked.

## Frozen inputs

Only two already-produced exposed-development artifacts may be read.

1. Exact recurrent-EOM residual diagnostic
   - workflow run: `31994209058`
   - artifact id: `9276300868`
   - artifact digest: `sha256:78108aa82ac4c9a372aa856f59daf14074b67a3bad6d1bb1ec4fae157e1a1f98`
   - required file: `RECURRENT_EOM_RESIDUAL_ANALYSIS_V1.json`
   - required file SHA-256: `19a50655a5612e6ef00e40e0eba7c1793f5bfe298c68c082baf8b35af4856078`

2. Exact fixed-scale TopoModal full-recoverability diagnostic
   - workflow run: `31986497845`
   - artifact id: `9273934102`
   - artifact digest: `sha256:7a929f807ab019bad7528380e667cfc41f42300d74e282b77e603f9a9676c218`
   - required file: `DIAGNOSTIC_RESULT.json`
   - required file SHA-256: `f673c2b3ace66e39020a05e077172370a0c026acc0fd40446773089600cba991`

No raw SonotaCo catalogue, no new truth parsing, no new clustering, and no new candidate generation are permitted in this diagnostic.

## Exact population

Evaluate only the two recurrent-EOM panels whose `route == "hdbscan"`, years 2013 and 2014.

For each such panel:

- take records whose frozen residual category is exactly `CANDIDATE_GENERATION_FAILURE`;
- join to the same-year TopoModal diagnostic `per_label` row by exact `truth_label == label`;
- require one and only one matching TopoModal row for every recurrent residual record under evaluation.

The Sugar panels are not evaluated because the frozen TopoModal full-recoverability artifact used here was constructed on the HDBSCAN-route event rows. No cross-route extrapolation is permitted.

## Exact complementarity criterion

A recurrent-EOM candidate-generation failure is `TOPOMODAL_COMPLEMENTARY_RECOVERY` iff the frozen same-label TopoModal row has:

`topomodal_best_f1 > 0.5`

Otherwise it is `NOT_RECOVERED_BY_TOPOMODAL`.

The threshold is inherited from the already-frozen recurrent residual diagnostic and TopoModal recoverability diagnostic. It must not be changed.

For every evaluated label, record:

- year;
- truth label;
- recurrent-EOM `best_all_f1`;
- TopoModal `topomodal_best_f1`;
- TopoModal `topomodal_first_rank_f1_gt_0_5`;
- complementarity classification.

Report counts and fractions per year and pooled across the two HDBSCAN-route panels.

## Invariants

The executable must fail closed unless all of the following hold:

- both required input SHA-256 values match exactly;
- recurrent schema is `ORBITTRACE_RECURRENT_EOM_RESIDUAL_ANALYSIS_V1`;
- recurrent parent method identifies recurrent-EOM HDBSCAN v1;
- exactly one HDBSCAN-route panel exists for each year 2013 and 2014;
- recurrent candidate-generation counts reproduce 16 in 2013 and 16 in 2014;
- TopoModal schema is `ORBITTRACE_TOPOMODAL_FULL_RECOVERABILITY_DIAGNOSTIC_V1`;
- TopoModal role is exposed SonotaCo development only;
- TopoModal protected-target-access flag is false;
- exactly one TopoModal panel exists for each year;
- exact-label joins are complete and unique.

## Outputs

Write:

- `COMPLEMENTARITY_RESULT.json`
- `environment.txt`
- `execution_commit.txt`

The result must explicitly state that this is a post-observation reproducibility audit and not a blind preregistration.

## Interpretation boundary

A positive result can establish only that the **already-frozen TopoModal candidate universe contains candidate structure missing from recurrent-EOM's frozen HDBSCAN-route output** on exposed SonotaCo development data.

It does **not** establish that a union method improves budgeted catalogue performance. It does not authorize a post-hoc ranker, route-specific rule, label-aware union, threshold search, or protected/external test.

Any multi-hierarchy successor must be specified separately using label-free / target-excluded development logic before its next outcome-bearing benchmark.

## Firewall

Forbidden throughout this diagnostic:

- protected solar-longitude region `[20°,55°]`;
- OrbitTrace target information or target-region events;
- AMOS;
- MAARSY;
- DMS;
- any pristine external endpoint;
- new method fitting or parameter search.
