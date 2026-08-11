# RFT v1 engineering cache run provenance

This file exists only to trigger the registered GMN-2022 engineering-equivalence workflow after infrastructure/runtime optimizations.

Scientific method changes: none.
Frozen science blob: `a5d5371f0c30a9c57ee4d8756ea41f454cd86301`.
Cached runner blob: `2a599c6e8247eb819a1090591d586526eda6c0c1`.
Parallel memo wrapper blob: `8a10e18daa6ba5bf99864a67e8cd059704695735`.
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
- The current engineering wrapper keeps the frozen scientific functions unchanged, runs the 17 independent perturbation replicas concurrently, memoizes only repeated calls for the identical ordered event-object pair, and reuses exact frozen `unit()` outputs. Before cached base vectors are used in perturbation, representative vectorized outputs must be bit-identical to frozen singleton outputs.
- The workflow fixes engineering parallelism at four workers and reconstructs tube caches in replica-number order before downstream persistence, so process completion order cannot affect scientific ordering.

No RFT constants, membership logic, scoring, thresholds, perturbation semantics, candidate rules, ablation definitions, or data-access policy changed in these repairs. This run remains target-excluded GMN-2022 development only and does not authorize GMN 2023 or SonotaCo.
