# Engineering correction v1 — no scientific result

Initial run `31934184610` is an engineering no-result only.

The run reached the first frozen subset (`d=128`, bucket `0`, `n=5567`) and then failed while recursively traversing the already-constructed rank-density merge tree:

`RecursionError: maximum recursion depth exceeded`

The exception occurred in the `collect(root_node)` traversal before the first subset produced any selected-candidate summary, before any recurrent-EOM comparison, before any cross-scale Jaccard metric, and before `RANKDENSITY_EOM_SCALE_V1.json` existed. Therefore no scientific outcome or gate was observed.

The merge tree can legitimately exceed Python's default recursion depth because single-link/MST upper-level-set trees may be highly unbalanced. This is an implementation/runtime limitation, not a change in the frozen architecture.

Authorized engineering correction only:

- preserve the exact frozen `PROTOCOL.md` and exact original `run_diagnostic.py` unchanged;
- invoke that exact implementation after raising Python's recursion limit to `100000` before `main()` runs;
- make no change to third-neighbor density ranks, empirical percentile levels, MST construction, simultaneous merge semantics, branch lifetime, excess-mass quality, minimum support, EOM tie rule, comparator, subsets, Jaccard metric, or gate.

If the corrected execution reaches the frozen result, that is the first technically valid scientific diagnostic outcome for this architecture.

No shower truth, protected target information/events, SonotaCo, ASFN/EFN event rows, AMOS, MAARSY, or DMS were accessed by the failed run.
