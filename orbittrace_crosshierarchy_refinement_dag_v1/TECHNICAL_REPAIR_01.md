# Cross-hierarchy refinement DAG v1 — Technical Repair 01

## Classification of run 32184246575

Run `32184246575` is a **technical no-result**. It produced no DAG stability result, no prelabel/result artifact, and no shower-truth access existed anywhere in the workflow.

All setup, source-hash, artifact-download, firewall, GMN-universe, and recurrent-EOM rebind checks passed. Reconstruction reached d=128 bucket 0 and then stopped at:

`sealed sparse membership rebind failed d=128 b=0: {'topomodal_memberships_exact': False, 'recurrent_memberships_exact': True, 'event_count_exact': True, 'event_universe_exact': True}`

## Root cause

The scientific protocol named the **raw support-resolved TopoModal cut** as parent representation, but the first implementation rebound that parent against `source_overlap_consensus_candidates` inside the later recurrent-TopoModal Pareto prelabel.

That field is not the raw support-resolved cut. The Pareto builder consumes the already-filtered overlap-consensus `successor_candidates`, then copies those into `source_overlap_consensus_candidates`. On d=128 bucket 0, the raw support-resolved cut contains 69 candidates whereas overlap-consensus contains 62. Therefore the failed equality was comparing different frozen methods.

The authoritative raw support-resolved parent prelabel is:

- run: `31961908008`
- artifact: `9267530845` (`orbittrace-topomodal-support-resolved-cut-v1`)
- artifact digest: `sha256:92fc029751562bbff844fd5ef866448a5bf1972ce035e5f74851861a4948c9c8`
- prelabel SHA-256: `4529eadd9ff93aae057f0a6fd5e0dd923f2300b7c6e01b74a0b7638e22da6de6`
- d=128 raw TopoModal counts b0..b3: `69, 80, 79, 70`
- d=1024 raw TopoModal counts b0..b3: `9, 6, 6, 9`

## Frozen repair scope

Repair 01 may change only the provenance/rebind interface:

1. replace the later Pareto-prelabel input with the authoritative raw support-resolved-cut prelabel above;
2. compare reconstructed TopoModal memberships against that prelabel's exact `successor_candidates`;
3. compare reconstructed recurrent memberships against that prelabel's exact `recurrent_candidates`;
4. verify exact panel event count through `events_total` and exact panel universe through `event_universe_sha256`;
5. update source/input hashes and workflow plumbing required for those checks.

The repair must **not** change:

- any event, panel, denominator, bucket, salt, or blind interval;
- TopoModal geometry, radius, density, hierarchy, support, or cut;
- recurrent-EOM geometry, HDBSCAN parameters, recurrence extraction, or memberships;
- DAG edge definition (`nonempty exact intersection`);
- common-refinement atom definition;
- stability metric or projection rule;
- any of the nine structural gates;
- any threshold, weighting, pruning, ranking, parent preference, or tie rule;
- any firewall or interpretation boundary.

There is still no truth stage. Repair 01 must be frozen before another execution. If it reaches the structural gates, that first technically valid result is binding.