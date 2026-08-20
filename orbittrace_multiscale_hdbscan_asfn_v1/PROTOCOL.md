# Multiscale HDBSCAN ASFN transfer v1 — frozen protocol

## Purpose
Test the exact SonotaCo-derived multiscale HDBSCAN ranking once on NASA ASFN 2018/2019 before any OrbitTrace-inclusive discovery application.

## Frozen method
The candidate universe is the union of ordinary pooled GEO6 HDBSCAN EOM clusterings at min_cluster_size values 10,20,30,40,50,60,70,80,90,100,120,150,200,300,500,750,1000, with min_samples=None as in the corrective SonotaCo HDBSCAN benchmark. Exact duplicate memberships are merged across scales. The already-frozen historical ASFN recurrent-EOM 10/10 catalogue may enter only as an auxiliary structural overlap witness because that was part of the development implementation that produced the SonotaCo result; recurrent-only memberships are never reportable successor candidates.

For each reportable HDBSCAN membership compute the exact development features: maximum Jaccard overlap to any distinct candidate membership in the merged structural universe; pooled GEO6 compactness 1/(1+mean squared scatter); cross-year centroid displacement normalized by within-year scatter as 1/(1+sync); balanced annual support; maximum HDBSCAN membership probability; number of HDBSCAN support scales; inverse minimum support scale; inverse log membership size. Rank-normalize each feature over reportable memberships.

The frozen weight vector is [0.335,0.250,0.230,0.215,0.128,0.145,1.0,0.0]. Candidate selection uses greedy maximal-marginal ranking with Jaccard redundancy penalty lambda=0.25. No ASFN label, shower code, target coordinate, OrbitTrace ID, or post-result parameter change may alter the ranking.

## Transfer comparator and gate
For each direction 2019->2018 and 2018->2019, ordinary HDBSCAN selects min_cluster_size on the opposite-year labels from the same frozen grid by macro-F1, then recovered-shower count, then smaller min_cluster_size. The held-out-year multiscale catalogue is truncated to the tuned HDBSCAN candidate count. Evaluation uses one-to-one Hungarian macro-F1 over reference showers with at least four annual members. Recovery is assigned F1 > 0.5.

PASS requires, in both held-out directions, strictly higher macro-F1 than tuned HDBSCAN and no fewer recovered showers. Any failure ends the method: no OrbitTrace discovery application and no ASFN-specific rescue.

## Data and interpretation boundary
Use the exact pinned NASA archive nasfn_2013-2019.zip SHA-256 c091b0f3f87f10badbe5fa38e6c45ba818af99f1c27c2fd6a23be286074c89a4. Retain only 2018/2019 after inclusive solar-longitude [20,55] exclusion before scientific channel decoding. This ASFN corpus was previously exposed elsewhere in the OrbitTrace project, so this is cross-survey transfer/generalization evidence for this newly frozen multiscale method, not pristine project-wide validation.
