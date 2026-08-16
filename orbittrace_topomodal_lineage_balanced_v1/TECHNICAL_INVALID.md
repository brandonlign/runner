# Topomodal lineage-balanced v1 — technical invalidity closure

## Verdict

**TECHNICALLY INVALID BEFORE TRUTH — CLOSED.**

This is not a shower-recovery failure. No immutable lineage-balanced v1 prelabel was ever written, no seal-before-truth step completed, and no shower-truth evaluation ran.

Two independent pretruth implementations failed on the same hierarchy node in the first frozen GMN sparse subset (`d=128, bucket=0`, node `3643`):

1. initial run `31963429131` / job `95204772723` aborted with `RuntimeError: bad lifetime 3643`;
2. engineering repair run `31963673540` / job `95205406620` computed each fixed child merge density directly from the exact radius graph and aborted with `RuntimeError: nonmonotone exact hierarchy lifetime at 3643`.

Repair 1 preserved the frozen radius, density, ToMATo hierarchy, complete #1284 candidate universe, surviving-mode lineage definition, and score semantics. It required exact graph-saddle persistence pairs to agree with GUDHI's finite persistence diagram and then required the proposed raw density-level lifetime to be monotone along the prominence hierarchy. The latter requirement failed.

Therefore the v1 quantity

`density-level lifetime = candidate formation density level - next enclosing merge density level`

is not a coherent nonnegative lifetime on the actual GUDHI ToMATo prominence hierarchy used here. Removing the monotonicity audit, clipping the value, changing the merge-level definition, or replacing the score after this failure would change the scientific method and is forbidden.

## Scientific consequence

The lineage-balancing **scheduling principle** remains scientifically motivated by the already-opened #1284 sparse-recovery failures: complete nested topomodal candidates preserve strong recovery, while several scalar global rankings leave MRR below recurrent-EOM. However, lineage-balanced v1 itself is permanently closed.

A successor must be frozen as a new architecture before truth. It may not reuse or reinterpret v1's invalid raw-density lifetime.

## Firewall

Both attempts remained target-excluded GMN 2022+2023 only. The protected solar-longitude interval `[20°,55°]` remained excluded. No OrbitTrace target information/events, SonotaCo event rows, ASFN/EFN event rows, MAARSY, or DMS entered either attempt.