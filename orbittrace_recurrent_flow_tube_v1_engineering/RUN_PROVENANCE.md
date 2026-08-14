# RFT v1 engineering cache run provenance

This file exists only to trigger the registered GMN-2022 engineering-equivalence workflow after infrastructure/runtime optimizations.

Scientific method changes: none.
Frozen science blob: `a5d5371f0c30a9c57ee4d8756ea41f454cd86301`.
Cached runner blob: `2a599c6e8247eb819a1090591d586526eda6c0c1`.
Parallel memo + batched-KD wrapper blob: `8b8a9d373f908dbb32ac9a6b43addeaeb19bb8fa`.
GMN 2023 access: false.
SonotaCo access: false.
Target information access: false.
Target-region events accessed: false.
MAARSY scientific access: false.
DMS scientific access: false.

Engineering history:
- The original frozen GMN-2022 workflow reached its 240-minute timeout without producing a scientific result.
- Fast attempt 1 failed before scientific execution because the engineering wrapper compared a Git blob SHA to a raw SHA-256 digest.
- Fast attempt 2 passed all source/runtime pins but failed before scientific execution because the dynamically loaded frozen RFT module was not registered in `sys.modules` before Python processed its `@dataclass` definitions.
- Fast attempt 3 passed all source/runtime pins, parsed the complete target-excluded GMN 2022 catalogue, and entered atomization, but replica 0 still had not completed after about 39 minutes when the hosted runner received a shutdown/cancel signal. No scientific result was produced.
- The four-worker parallel memo wrapper was subsequently launched twice, but both attempts received hosted-runner shutdown signals after only about eight minutes of scientific execution, before any replica completed. Those are infrastructure cancellations, not runtime/scientific outcomes.
- The current engineering wrapper keeps the frozen scientific functions and every exact distance/graph/component/medoid/tube rule unchanged. It runs the 17 independent perturbation replicas concurrently, memoizes only repeated calls for the identical ordered event-object pair, and reuses exact frozen `unit()` outputs.
- New implementation-only optimization: within each frozen 2-degree atomization bin, the exact same `cKDTree.query_ball_point(..., r=1.02)` candidate search is issued once in batch for all transformed rows instead of once per row. Candidate order cannot affect science because the frozen algorithm recomputes exact `pair_d` for all returned candidates and sorts by `(distance,event_id)` before selecting KNN. Several deterministic rows in every bin are required to have exactly identical candidate sets under batched and frozen scalar SciPy calls.
- The workflow fixes engineering parallelism at four workers and reconstructs tube caches in replica-number order before downstream persistence, so process completion order cannot affect scientific ordering.

No RFT constants, membership logic, scoring, thresholds, perturbation semantics, candidate rules, ablation definitions, or data-access policy changed in these repairs. This run remains target-excluded GMN-2022 development only and does not authorize GMN 2023 or SonotaCo.
