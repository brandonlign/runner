# Recurrent-EOM selection/ranking diagnostic v1

## Status

Frozen zero-label diagnostic only. No shower truth, paper-score recomputation, successor ranking, or method promotion is authorized.

## Question

On the exact pooled SonotaCo 2013+2014 row universes used by the current paper benchmark, how much of recurrent-EOM's difference from ordinary EOM comes from:

1. selecting different condensed-tree memberships; versus
2. reordering memberships shared by both flat catalogues?

This diagnostic is motivated by the binding RC-EOM v1 paper result, which showed that ordinary-EOM evidence improves the Sugar panels while current recurrent-EOM remains better on the small-budget HDB panels. It does not use those truth labels internally.

## Frozen construction

For each current paper route (`sugar`, `hdbscan`):

- use the exact frozen 2013 and 2014 row hashes/counts;
- pool both years before clustering;
- use exact GEO6 geometry;
- fit HDBSCAN with `min_cluster_size=10`, `min_samples=10`, Euclidean metric, EOM, epsilon 0;
- reconstruct ordinary EOM with `compute_stability`;
- reconstruct exact recurrent-EOM with Git blob `30ac3fa3bc47910370df528fcf3ae8ecb6277b47`;
- freeze complete ordinary and recurrent catalogues before any label access;
- compare exact membership hashes and rank positions at K=10,14,20,40,43,50,100.

The output may state only structural facts: catalogue counts, exact membership overlap, membership-only differences, and rank shifts for shared candidates.

## Interpretation

- If the top-14 sets are identical but ordered differently, the HDB-panel mechanism is ranking-dominant.
- If recurrent top-14 contains memberships absent from the ordinary top-14, selection contributes at the exact paper budget.
- If recurrent top-14 memberships are absent from the entire ordinary catalogue, candidate selection is indispensable rather than a rank-only issue.

No successor is selected directly from this diagnostic. Any new method must be separately motivated and frozen before truth.
