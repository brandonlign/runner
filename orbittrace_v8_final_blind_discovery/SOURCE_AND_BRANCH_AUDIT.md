# Source and branch audit for the final v8 blind discovery freeze

## Authoritative parent

The final discovery freeze starts directly from `agent/orbittrace-pooled-year-centroid-v8` at commit `c9d6c44704013ba0c9430100e98a29a56b453304` (PR #321), not from a later development branch.

The authoritative v8 result is the passed one-shot target-excluded GMN 2022/2023 development artifact `9009728299`, digest `sha256:88d2d607e05d027015c338f7e23b64a6195e55ae24f1b2ac745f5e9bc6df599e`.

## `agent/orbittrace-postpass-preparation`

A direct GitHub compare against the v8 branch showed this branch is **diverged**: it is 4 commits ahead and 29 behind v8, with merge base `44f4e51efe34e0950ee62fc97a6c2bd96f86e9a5`. Its four added files are confined to the older `orbittrace_wavelet_catalogue_v3_postpass/` preparation (`PRECOMMIT_PROTOCOL.md`, `authorize_validation.py`, `freeze_development_result.py`, `test_postpass_guards.py`).

Decision: do not merge, cherry-pick, import, or inherit this branch. Its useful high-level idea—freeze first and authorize later—is reimplemented independently in the v8 firewall.

## Old fixed4 blind-catalogue branches

PR #168 (`agent/orbittrace-fixed4-blind-catalogue-scan`) used a different scientific scanner: a calibration-thresholded fixed4 catalogue and the older family-ranking wrapper. It is not the v8 method and none of its scan output is an input here.

PR #175 (`agent/orbittrace-fixed4-blind-catalogue-reveal`) established a useful two-process firewall pattern: freeze a blind family list first and only then retrieve a canonical reference. Its exact-ID reveal rule and its **pre-reveal** rank depths (`<=25` full, `<=100` partial) predate the old reveal result. Those procedural rules are retained unchanged so the final v8 protocol does not choose a more favorable depth after any old result.

No old reveal artifact, old selected family identifier, old target overlap, old target rank, old canonical artifact locator, or old target coordinate is imported by the final Stage A source.

## Fixed4 source export

PR #206 exported and independently verified the decoded historical scanner/support sources without catalogue access. The support source used by v6/v8 is pinned at:

`sha256:fa18a19c08c6824c66606cbd92095dc3605cbcc30f17a468c9e525e7c6ff4a62`.

Its source establishes the exact geometry cuts, coordinate conversion, nearest-neighbour feature matrix, fixed4 metric, component construction, and v6 connected-family semantics used by this freeze.

## v9 exclusion

PR #339 (`agent/orbittrace-support-overlap-family-v9`) is a separately named successor based on v8 and changes cross-year adjacency to observed-support-ball overlap. It is not part of the promoted v8 architecture. The final Stage A source statically rejects any v9 import and keeps the v6 absolute centroid-link radius `1.5` exactly.

## Final allowed scientific lineage

The only scientific lineage used by Stage A is:

1. fixed4 support source `fa18a19c...` for label-free proposals, components, and v6 connected families;
2. v6 label-free scanner source `5c1ed560...`;
3. v8 pooled same-year centroid semantics from source `0632e728...`;
4. multiplicity episode/scoring source `fd9526ec...`;
5. wavelet-catalogue runtime `ef3e6931...`;
6. multi-anchor v3 source `f8067697...`;
7. independent Brown comparator `5ef0f7b3...`.

Stage B imports none of these scientific detector modules.

## Blindness boundary

Source and protocol auditing may inspect code, constants, historical pre-reveal protocol choices, commit relationships, and hashes. It may not open any GMN event in solar longitude 20°–55°, retrieve the withheld target reference, inspect target members/coordinates, or consume an old reveal result as a selection signal.

The target-containing catalogue is first accessible only inside an externally authorized Stage A run. The withheld reference is first accessible only after Stage B has independently verified Stage A's immutable ranked-family hash.
