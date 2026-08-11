# RFT v1 engineering cache run provenance

This file exists only to trigger the registered GMN-2022 engineering-equivalence workflow after the dataclass dynamic-import repair.

Scientific method changes: none.
Frozen science blob: `a5d5371f0c30a9c57ee4d8756ea41f454cd86301`.
Cached runner blob: `2a599c6e8247eb819a1090591d586526eda6c0c1`.
Memo wrapper blob: `d4e242b55de92af6c7c066ee7356170d349fb4e0`.
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
- The current wrapper restores normal import semantics by registering the pinned module before `exec_module()` and removing it only on import failure.

No RFT constants, membership logic, scoring, thresholds, perturbation semantics, or data-access policy changed in these repairs. This run remains target-excluded GMN-2022 development only and does not authorize GMN 2023 or SonotaCo.
