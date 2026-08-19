# OrbitTrace M2D support-pruned cut v1

## Objective

Fix the oversized-family failure mode of the already-frozen support-resolved TopoModal + M2D method without changing its physical embedding, radius, minimum support, bifiltration evidence, M2D score, or ranking formula.

## Frozen structural change

The parent support-resolved cut uses `MIN_SUPPORT = 4` and recursively splits a TopoModal hierarchy node only when both immediate children have support >=4; otherwise it retains the parent when the parent has support >=4.

This can let an immediate child with support 1-3 force a much larger reportable sibling to remain merged into the parent.

Support-pruned cut v1 changes only that case:

1. leaf with support >=4 -> emit leaf;
2. both children support >=4 -> recurse into both;
3. exactly one child support >=4 -> discard the other child as sub-support noise and recurse into the reportable child;
4. both children support <4 while their parent support >=4 -> emit the parent;
5. otherwise emit nothing.

No event-size cap, persistence threshold, target interval, OrbitTrace coordinate, canonical OrbitTrace member ID, shower label, or post-result tuning parameter enters this rule.

## Frozen constants and inherited method

- physical embedding: exact frozen TopoModal hierarchy implementation;
- graph radius: 1.0;
- minimum support: 4;
- years: GMN 2022 and 2023 development panels;
- protected interval: solar longitude [20 deg, 55 deg] excluded before development candidate construction and truth evaluation;
- M2D formula: `M_2D(S)=(1/|S|)*sum_{B subseteq S}|B|*A(B)` using the exact already-frozen annual-density bifiltration catalogue;
- ranking: internal M2D descending, then modal contrast descending, then family hash ascending.

## Development comparison

Use exactly the eight target-excluded sparse GMN universes already used by the M2D literature-fairness result: denominators 128 and 1024, buckets 0..3, annualized to 16 truth panels. Candidate budgets are inherited from the already-frozen baseline M2D prelabel, so the refinement receives no extra candidate capacity.

The baseline is the immutable support-resolved-cut M2D prelabel SHA-256 `7b1ddfcd32cd0b52321e3b3dfc614a88dd9b973f947c1d4d0de74fddf26b59cd`.

Primary promotion gates, frozen before execution:

- refined candidate capacity >= the inherited baseline budget in every panel;
- pairwise-disjoint refined candidates in every panel;
- mean annual Hungarian macro-F1 across all 16 target-excluded GMN panels is not lower than baseline M2D;
- total annual `F1 > 0.5` recoveries across all 16 panels is not lower than baseline M2D;
- neither d=128 nor d=1024 scale has lower mean macro-F1 than baseline;
- neither scale has fewer `F1 > 0.5` recoveries than baseline;
- mean top-budget candidate member count is strictly lower than baseline and p90 top-budget candidate member count is no higher.

The size gates are diagnostic for the stated failure mode; the scientific-quality gates prohibit buying smaller clusters by sacrificing recovery/F1.

## Firewall

This development stage must not access the OrbitTrace protected [20 deg,55 deg] rows, canonical OrbitTrace member IDs, the rank-84 blind-reveal family, its 1,814-member membership, or any target-derived coordinate/interval statistic. SonotaCo is not used for parameter selection in this stage.

If this exact rule fails, v1 is frozen as a negative result. No threshold/radius/support sweep is authorized from the same truth result.

If it passes, the next stage may challenge the fair symmetric tuned-HDBSCAN benchmark. Only after the method is frozen independently of OrbitTrace may the already-revealed OrbitTrace target be used for post-freeze characterization; the original PR #1378 remains the clean blind evidence.