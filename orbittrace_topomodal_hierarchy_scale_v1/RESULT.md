# OrbitTrace fixed-scale topological modal hierarchy v1 — result

## 🟢 POSITIVE

Authoritative run: `31955621864`

Artifact: `9265889512`

Artifact digest: `sha256:2ddc5dbfc434b3887c284f639640d1b60276f5ceff1b9313e8604ddbb1beed6f`

Result SHA-256: `e8cf7d92e96db9a1c99578f6efc63baf1534b94ab975e94f789fa6bc4a718497`

Exact frozen interpretation:

`SUPPORTS_FIXED_SCALE_TOPOMODAL_HIERARCHY_CROSS_SCALE_COHERENCE`

The exact preregistered fixed-physical-scale radius-count + radius-graph + complete ToMATo mode hierarchy passed **all five** frozen structural gates on the four target-excluded GMN ~5.8k -> ~0.7k nested pairs. No shower truth was used.

Against exact recurrent-EOM HDBSCAN v1:

- pooled fine->coarse candidate-unweighted mean best Jaccard: `0.8067062037` vs `0.6152941107`;
- median bucket fine->coarse mean best Jaccard: `0.8129624258` vs `0.6089001948`;
- strict bucket wins: `4/4`;
- fine candidate non-collapse: PASS in `4/4` buckets;
- nonempty output: PASS in all eight subsets.

Bucket details (topological-modal vs recurrent-EOM):

- bucket 0: Jaccard `0.7908939874` vs `0.5606150794`; fine candidates `9` vs `8`;
- bucket 1: `0.7394508501` vs `0.7051527695`; fine candidates `7` vs `5`;
- bucket 2: `0.8664021164` vs `0.5504804711`; fine candidates `6` vs `6`;
- bucket 3: `0.8350308642` vs `0.6571853102`; fine candidates `9` vs `9`.

This directly resolves the single structural failure in PR #1279: preserving the exact same inherited physical scale but exposing the complete persistence-merging hierarchy prevents sparse candidate-count collapse while retaining the strong cross-scale identity of modal families.

The result does **not** itself establish shower recovery, ranking quality, or a promoted paper method. It authorizes exactly one separately frozen target-excluded GMN recovery/ranking successor before any shower truth is opened for that successor. The successor must use this exact frozen candidate hierarchy and may not modify radius, physical embedding, density estimator, graph, hierarchy membership construction, minimum support, subset rule, salt, or structural gate based on this result.

Protected `[20°,55°]`, OrbitTrace target information/events, shower truth, SonotaCo, ASFN/EFN event rows, AMOS, MAARSY and DMS were not accessed.