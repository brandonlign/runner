# RFT v1 engineering cache run provenance

This file exists only to trigger the registered GMN-2022 engineering-equivalence workflow after the provenance-pin repair.

Scientific method changes: none.
Frozen science blob: `a5d5371f0c30a9c57ee4d8756ea41f454cd86301`.
Cached runner blob: `2a599c6e8247eb819a1090591d586526eda6c0c1`.
Memo wrapper blob: `2c8e27b01da333e7c14960df677f685bbadc8c01`.
GMN 2023 access: false.
SonotaCo access: false.
Target information access: false.
Target-region events accessed: false.
MAARSY scientific access: false.
DMS scientific access: false.

The first fast attempt failed before scientific execution because the engineering wrapper compared a Git blob SHA to a raw SHA-256 digest. That provenance-only bug is repaired here. The original frozen GMN-2022 workflow later reached its 240-minute timeout without producing a scientific result. This repaired cached run therefore remains GMN-2022 development only and must not authorize GMN 2023 by itself until engineering equivalence is documented from the frozen semantics and deterministic checks.
