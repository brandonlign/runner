# Multiscale HDBSCAN final blind OrbitTrace discovery v1 — frozen protocol

## Authorization
This final target-inclusive application is authorized only because the exact SonotaCo-derived multiscale HDBSCAN rule passed the separately frozen ASFN 2018/2019 transfer gate with no parameter changes (`PASS_MULTISCALE_HDBSCAN_ASFN_GENERALIZATION_V1`).

## Frozen discovery method
Use the complete label-free GMN 2022+2023 catalogue returned by the existing audited blind-catalogue transport. No shower labels, canonical OrbitTrace IDs, target coordinates, target activity interval, or prior target reveal may be available during Stage A.

Generate ordinary pooled GEO6 HDBSCAN EOM catalogues at min_cluster_size values 10,20,30,40,50,60,70,80,90,100,120,150,200,300,500,750,1000, with min_samples=None, Euclidean distance, no single cluster, and HDBSCAN 0.8.44. Exact duplicate memberships are merged across scales.

As in the frozen SonotaCo development implementation and ASFN transfer, an exact recurrent-EOM HDBSCAN v1 catalogue may enter only as an auxiliary structural-overlap witness; recurrent-only memberships are never reportable final candidates. For GMN use the promoted recurrent-EOM parent geometry `min_cluster_size=10`, `min_samples=10`, with the exact frozen recurrent-EOM stability implementation. This auxiliary catalogue is constructed label-free before target access.

For every reportable HDBSCAN membership compute the frozen feature vector:
1. maximum Jaccard overlap to any distinct membership in the merged HDBSCAN + auxiliary recurrent structural universe;
2. pooled GEO6 compactness `1/(1+mean squared scatter)`;
3. 2022/2023 centroid consistency `1/(1+ ||c22-c23|| / (sqrt((s22+s23)/2)+1e-9))`;
4. annual balance `2*min(n22,n23)/(n22+n23)`;
5. maximum HDBSCAN membership probability over support scales;
6. number of HDBSCAN support scales;
7. inverse minimum HDBSCAN support scale;
8. inverse log membership size.

Rank-normalize each feature over reportable memberships. Frozen weights are exactly `[0.335,0.250,0.230,0.215,0.128,0.145,1.0,0.0]`. Base score is the weighted sum. Final ordering is greedy maximal-marginal selection with redundancy penalty `lambda=0.25`, subtracting `lambda * max Jaccard` to any already-selected reportable candidate. No parameter, weight, scale, feature, or tie rule may change after Stage A begins.

## Two-stage firewall
Stage A freezes the complete method identity and the exact top-100 ranked memberships before the canonical OrbitTrace package exists in the job workspace. Stage A is uploaded as an immutable artifact.

Only after that upload may Stage B download the exact previously pinned canonical review package. Stage B performs trajectory-ID set intersection only; no membership recomputation, reranking, merging, target-distance matching, or tuning is allowed.

## Success gate
The already-established final blind recovery firewall is inherited unchanged:
- final multiscale rank <= 100;
- at least 4 exact canonical 2022 members;
- at least 4 exact canonical 2023 members;
- at least 8 exact canonical members total;
- exact target F1 strictly > 0.5 against the 18-member 2022+2023 canonical target.

If no candidate passes all gates, verdict is final failure. No rescue sweep or second scientific reveal is authorized.
