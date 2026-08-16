# OrbitTrace topomodal annual topology confirmation v1 — frozen protocol

## Scientific question

The #1284 fixed-scale topological-modal hierarchy repeatedly improves sparse known-stream recovery, purity, fragmentation, and sample-size stability relative to recurrent-EOM, but every tested generic scalar ordering has lost MRR. This successor asks a different question:

> Does a pooled #1284 candidate represent a structure that is independently recovered by the **same fixed topology** in both observing years?

The method does not alter pooled candidate memberships. It replaces generic within-candidate ranking with independent annual topological confirmation.

## Distinction from closed cross-year lanes

This is not cross-year-core HDBSCAN: annual information does not enter a mutual-reachability graph or pooled hierarchy.

This is not two-view membership expansion: no event is added, removed, reassigned, classified, or expanded.

This is not year balance: event-count fractions do not enter the score.

This is not cross-year component matching used to create a new candidate universe: the pooled #1284 candidate universe is already immutable before the annual views are constructed.

The only new operation is confirmation of each frozen pooled candidate against independently generated 2022 and 2023 #1284-topology families.

## Firewall

- Development data: target-excluded GMN 2022+2023 only.
- Inclusive solar longitude 20°–55° is excluded before geometry, topology, confirmation, ranking, and truth.
- OrbitTrace target information/events remain inaccessible.
- Shower truth is inaccessible during geometry reconstruction, annual topology generation, confirmation, ranking, and prelabel sealing.
- SonotaCo 2013/2014, ASFN/EFN event-level data, AMOS, MAARSY, and DMS are inaccessible.
- The first technically valid truth outcome is binding.

## Immutable pooled candidate/comparator source

Reuse only the original #1284 pretruth payload:

- `TOPOMODAL_SPARSE_RECOVERY_V1_PRELABEL.json`
- SHA-256 `db608f84bf333d18d624199f2d31c27b4183ee3a75a3d930cef4b9766a19d4de`

This file was sealed before the original #1284 truth evaluation and contains, for each of the eight frozen sparse panels:

- exact pooled #1284 complete-hierarchy candidate memberships;
- exact recurrent-EOM candidate memberships and order;
- exact event-universe hash;
- exact equal-budget comparator count.

No prior truth result is an input to this successor.

## Sparse panels

Reuse exactly the same deterministic scale-stress panels:

- denominator 128, buckets 0–3;
- denominator 1024, buckets 0–3;
- exact event identities from immutable manifest `ORBITTRACE_EXACT_1284_SPARSE_UNIVERSE_MANIFEST_V1`, SHA-256 `3ed5c33216d7d1cf2cbc703da088b3a86132e50532fb996cfe475d7f6052d7f8`.

Panel sizes remain exactly:

- d128: 5567, 5840, 5857, 5816;
- d1024: 677, 739, 736, 766.

## Exact annual topology

For each sparse panel and each year independently:

1. Restrict the panel to that year's immutable event IDs.
2. Reconstruct the exact #1284 physical coordinates from the same immutable GMN monthly files:
   - solar longitude `sol`;
   - Sun-centered geocentric ecliptic longitude `sun_lon=(LAMgeo-sol) mod 360`;
   - geocentric ecliptic latitude `BETgeo`;
   - geocentric speed `Vgeo`.
3. Require all monthly file SHA-256 values to match the immutable sparse-universe manifest before any coordinates are accepted.
4. Use unchanged #1284 physical embedding:
   - `h_sol=2 sin(5°/2)`;
   - `h_rad=2 sin(4°/2)`;
   - `h_logv=ln(1.1)`;
   - exact six-dimensional embedding.
5. Use exact symmetric Euclidean radius graph `r=1.0`, including self.
6. Use annual density `rho_i=|N_i|/n_year`, including self.
7. Use GUDHI 3.12 manual-graph/manual-density ToMATo.
8. Retain every complete annual hierarchy membership with support >=4.

There is no year-specific threshold, cluster-count selection, persistence cut, station weighting, or HDBSCAN operation.

## Mandatory geometry/topology exactness audit before confirmation

Before a single annual-confirmation score is computed, the same reconstructed coordinates must be pooled back within each sparse panel and reproduce the original #1284 pooled candidate membership summary **exactly** for all eight panels.

Any pooled membership mismatch is an engineering no-result. It may be repaired only to reproduce the frozen #1284 geometry; it does not authorize a scientific change.

## Annual confirmation score

For each immutable pooled #1284 candidate `C` and year `y`:

- let `C_y` be the candidate's members belonging to year `y`;
- if `|C_y| < 4`, define `J_y(C)=0` using the already-fixed support-4 reporting floor;
- otherwise, for every reportable annual ToMATo family `A` in year `y`, compute Jaccard similarity
  `J(C_y,A)=|C_y ∩ A| / |C_y ∪ A|`;
- define `J_y(C)=max_A J(C_y,A)`.

The candidate recurrence/confirmation score is exactly

`J_rec(C)=min(J_2022(C), J_2023(C))`.

This is the sole scientific ranking coordinate.

## Frozen total order

Rank all pooled #1284 candidates by:

1. `J_rec` descending;
2. exact `family_hash` ascending for ties.

No root/finite tier is preserved. Root status, pooled density, prominence, support, member count, year balance, station count, orbit, activity profile, previous #1284 rank, recurrent-EOM overlap/rank, or any learned/fused score is forbidden.

The removal of root priority is part of this frozen architecture: if annual independent recurrence is the evidence of interest, a recurrent finite hierarchy state must be allowed to outrank an unconfirmed root.

## Immutable prelabel

Before shower truth is opened, serialize and SHA-256 seal for all eight panels:

- event-universe hash;
- exact original #1284 pooled membership for every candidate;
- exact annual topology membership summaries for 2022 and 2023;
- `J_2022`, `J_2023`, `J_rec`, final rank;
- exact recurrent-EOM candidate memberships/order from the original #1284 pretruth file;
- equal candidate budget `K = recurrent-EOM candidate count`.

Require successor candidate count >= K in all panels. The truth evaluator may not import the annual-topology generator or recalculate rankings.

## Binding truth endpoint

Use the same 16 annual sparse known-stream panels and the same ten gates used by #1284 and later successors.

Fine d1024:
1. qualified total strictly greater than recurrent-EOM;
2. qualified nonlower in at least 6/8 annual panels;
3. mean MRR not lower;
4. mean top-100 dominant precision not lower;
5. mean fragmentation not higher.

Coarse d128:
6. qualified total not lower;
7. qualified nonlower in at least 6/8 annual panels;
8. mean MRR not lower;
9. mean top-100 dominant precision not lower;
10. mean fragmentation not higher.

All ten gates must pass.

## Closure / no-rescue rule

A valid failure permanently closes this exact annual-topology-confirmation architecture. Do not change `min` to mean/geometric mean/product, introduce a Jaccard threshold, blend confirmation with root status/density/prominence/support/previous rank, change annual support, use asymmetric year weights, add HDBSCAN overlap, change graph scale, or tune a tie-break from the result.

A PASS would authorize only a separately frozen portability/scalability stage. It does not authorize protected target access or external event-level truth.
