# BDCP1 engineering repair 1 — recurrent comparator identity audit

## Status

Runs `31965405024` and `31965475922` are **NO-SCIENTIFIC-RESULT** attempts.

- Run `31965405024` failed before candidate generation because the workflow omitted the `gudhi` dependency imported by the pinned historical sparse-recovery helper.
- Run `31965475922` reached the first BDCP1 bivariate enumeration panel but aborted at the recurrent-EOM comparator-summary assertion **before** `BIVARIATE_DENSITY_COMPONENT_PERSISTENCE_V1_PRELABEL.json` existed. The seal-before-truth and evaluator steps were skipped. No shower labels were evaluated.

The second failure exposes an audit-representation ambiguity, not permission to relax the parent control. The immutable #1284 structural artifact was produced by `orbittrace_topomodal_hierarchy_scale_v1.recurrent_candidates`, while the later frozen sparse-recovery helper uses `orbittrace_topomodal_sparse_recovery_v1.recurrent_ranked` so it can additionally rank the same selected recurrent-EOM candidates.

Repair 1 strengthens the pretruth comparator check by executing **both** historical implementations on every exact sparse panel and requiring all of the following before any prelabel can be written:

1. the original #1284 structural implementation reproduces the immutable #1284 recurrent-EOM candidate count and `(family_hash, member_count)` rows exactly;
2. the ranked sparse-recovery implementation and the #1284 structural implementation produce exactly the same set of event-ID memberships;
3. both have the same candidate count;
4. the ranked implementation remains the comparator order serialized into the BDCP1 prelabel, so truth evaluation uses the same selected-parent ranking as the prior sparse-recovery experiments.

No BDCP1 scientific quantity changes. The exact two-annual-density threshold lattice, connected components, support-cell area, support floor, candidate ranking, panels, truth metric, and ten gates remain frozen exactly as in `PROTOCOL.md`.

If either historical comparator implementation fails the strengthened membership identity audit, BDCP1 remains blocked before truth; no parent-control relaxation is authorized.