# OrbitTrace density-sync FLASC refinement v1 — frozen protocol

## Scientific role

**TARGET-EXCLUDED GMN 2022+2023 DEVELOPMENT ONLY.**

This is one preregistered structural successor test. It asks whether some density-synchronous EOM winner families are broad containers that merge multiple real shower-like arms, while ordinary density leaves are too numerous and unstable to expose wholesale.

The successor uses FLASC branch detection only as an **internal refinement of the exact 179-winner families**. It does not replace GEO6, HDBSCAN density estimation, density-synchronous EOM selection, or the winner's global family order.

## Frozen baseline

Exact full-data density-synchronous recurrent-EOM winner from run `31852836840`:
- candidate count `2094`;
- total recovered@100 `179`;
- 2022: @50 `45`, @100 `89`, precision `0.7873334043`, MRR `0.02250537317`, fragmentation median top500 `1.0`;
- 2023: @50 `46`, @100 `90`, precision `0.7898245986`, MRR `0.02203028491`, fragmentation median top500 `1.0`.

The exact winner order hash is `e8f374ad03e7072463118ee6440a54d96d11e3aab17202cfe336f866530224f2`.

## Sole successor change

Reconstruct the exact winner hierarchy and exact 2094 winner families first. HDBSCAN settings remain GEO6, `min_cluster_size=10`, `min_samples=10`, Euclidean, EOM, epsilon `0`, `allow_single_cluster=False`.

Fit the same HDBSCAN hierarchy with branch-detection data enabled, and pass the **overridden exact density-synchronous EOM labels** into `hdbscan.branches.detect_branches_in_clusters`.

FLASC settings are frozen before outcome:
- `branch_detection_method="core"` for scalable kNN/mutual-reachability branch graphs on the 738,682-event catalogue;
- `label_sides_as_branches=False`, so only families with at least three selected branches (a real bifurcation, not a simple elongated two-sided shape) are refined;
- branch `min_cluster_size=10`;
- branch `max_cluster_size=0` / unlimited;
- branch selection method `eom`;
- branch selection epsilon `0.0`;
- branch selection persistence `0.0`;
- `allow_single_cluster=False`.

For each baseline family in its exact original global rank order:
1. if FLASC selects at most two branches, preserve that baseline family byte-for-byte as one candidate;
2. if FLASC selects three or more branches, replace that parent family by its selected non-noise FLASC branch families;
3. order replacement branches only within that parent's original slot by descending FLASC branch persistence, then descending member count, then deterministic family ID.

No branch from one parent can jump ahead of an earlier baseline parent. No baseline parent and its replacement branches coexist. Branch-segmentation noise/central fall-out is not promoted as a candidate. Every promoted branch must contain at least 10 events.

This makes FLASC a selective **parent-to-branches structural substitution**, not a new global reranker and not an EOM+leaf union.

## Prelabel freeze

Before known-shower truth is indexed, persist:
- exact reconstructed winner tree and order verification;
- FLASC version/settings;
- branch count and persistence for every winner family;
- list of refined baseline families;
- all replacement branch memberships;
- complete final successor candidate order and membership hash;
- source/input hashes and firewall state.

## Binding gate

The successor passes only if all are true:
1. total recovered@100 across 2022+2023 is at least `184` (`+5` minimum over 179);
2. neither year regresses in recovered@50;
3. neither year regresses in recovered@100;
4. neither year regresses in top100 dominant precision;
5. neither year regresses in MRR;
6. neither year worsens in median top500 fragmentation;
7. at least one baseline family is genuinely refined into >=3 promoted branches;
8. exact winner reconstruction, source pins, prelabel freeze, and all firewalls pass.

Otherwise the exact method is permanently `FAIL_DENSITY_SYNC_FLASC_REFINE_V1_GMN_DEVELOPMENT`. No post-result switch from core to full, two-sided branch labeling, branch-size tuning, persistence threshold, parent+branch union, branch quota, score blend, rank reweighting, or selective rescue is authorized.

## Firewall

- Protected solar longitude `[20°,55°]` removed inclusively before labels.
- OrbitTrace target information/events inaccessible.
- SonotaCo 2013/2014 inaccessible.
- AMOS inaccessible.
- ASFN/EFN inaccessible.
- MAARSY/DMS inaccessible scientifically.

A GMN pass would authorize only a separately frozen transfer test; it would not itself establish external generalization.