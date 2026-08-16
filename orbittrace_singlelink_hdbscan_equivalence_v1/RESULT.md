# Scalable single-link equivalence v1 — result

## 🟢 PASS — exact implementation equivalence

GitHub Actions run `31930681256` completed successfully at execution head `475dfabc7e1a7c334ad95c75f83284c3c5664415`.

- artifact: `9259209913`
- artifact digest: `sha256:a3ef5315dfd93414befa2ee37348f3d6065e2fe254ad2e508d09b01363ede09d`
- result SHA-256: `5009d705799ec3c52963cd77e88e49a8573ebf652dba9acd367ee1cb88e0d2a4`
- exact verdict: `PASS_SCALABLE_SINGLELINK_EQUIVALENCE`

Across all eight frozen d=128 and d=1024 target-excluded GMN subsets, HDBSCAN 0.8.43 with `min_samples=1`, `min_cluster_size=2`, `algorithm='boruvka_kdtree'`, and `approx_min_span_tree=false` reproduced the exact sklearn Euclidean single-link hierarchy used by PR #1274 for the scientific feasibility diagnostic:

- sorted merge-distance multisets were exactly equal in every subset;
- maximum absolute merge-distance difference was `0.0` in every subset;
- exact branch membership hashes for all branches in the frozen 4–7, 8–15, 16–31 and 32–63 size bins were identical in every subset.

This is an implementation-equivalence result only. It does not promote raw single linkage as the paper method and does not constitute a scientific successor outcome.

## Consequence

The support-free single-link hierarchy underlying #1274 can be constructed through HDBSCAN's scalable Boruvka KD-tree path without reintroducing the parent `min_samples=10` core-distance scale. Therefore full-GMN successor development does not require the quadratic-memory sklearn agglomerative implementation used for the small-sample feasibility diagnostic.

## Firewall

No target information, protected-region events, shower truth, SonotaCo, ASFN/EFN event rows, AMOS, MAARSY or DMS were accessed by this equivalence test.
