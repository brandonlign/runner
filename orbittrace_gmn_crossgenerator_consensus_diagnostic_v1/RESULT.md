# OrbitTrace GMN cross-generator consensus diagnostic v1 — binding result

## Verdict

`PASS_GMN_CROSSGENERATOR_CONSENSUS_DIAGNOSTIC_V1`

This is a **target-excluded GMN 2022/2023 mechanism diagnostic only**. It is not a successor ranking, membership merge, suppression rule, SonotaCo result, or external validation.

## Frozen scientific provenance

- protocol freeze commit: `0daa2d223c395d6bd1c0185c7847ca71f9429948`
- implementation commit: `e98126ad5c11008c99ce8f15e8c9dbb1ddfb438e`
- execution-plumbing commit: `692f89b38d80a583a5024f0b98d8a6224d8a45de`
- binding workflow run: `31613021560`
- exact #839 ranker source SHA-256: `dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990`
- P19 prelabel SHA-256: `276129ef8f9f31a1f8e7b1570c15f5e67ed1a7274f293f5da65bab60f86e32b8`
- P20 prelabel SHA-256: `8ca358ae0f3ac96b188de9eac7bcfd6f870470873a2b7ee73b7ae76497c12734`

## Split-freeze pretruth graph

The complete P19↔P20 graph was constructed and frozen before GMN shower labels entered the evaluator.

- pretruth artifact: `orbittrace-gmn-crossgenerator-consensus-pretruth-v1`
- artifact ID: `9148009042`
- artifact digest: `sha256:68f106cf398bb6dfa7e80e4f4dcaa25b187eeeb2c112477f8c850fd7d36e6854`
- graph edge count: **698**
- graph file SHA-256: `1d7ccb41800b222df053e1f8240ceb2c21020ae160e0c6e6b33eda0b546b03ac`
- canonical edge SHA-256: `319d1a868d68148221caba82e28ca17b9a7f55b0f1f7b0f1c02a8fc9e5c28bb0`

The graph used exactly the preregistered relation: a P19 soft family and P20 soft family are adjacent iff they share at least one exact GMN event ID and their inherited #839 two-year centroid distance is `<= 1.0`. No graph threshold, overlap cutoff, route, source quota, or alternative graph was searched.

## Binding truth-aware diagnostic

- result artifact: `orbittrace-gmn-crossgenerator-consensus-diagnostic-v1`
- artifact ID: `9148108571`
- artifact digest: `sha256:65a19642f66f1dcce1fb4806de6f07159284486474497c6f7f10482168692c52`

Exact result:

- eligible label count: **355**
- qualified family count: **2,017**
- qualified label count: **256**
- qualified graph edges: **321**
- same-label qualified edges: **315**
- different-label qualified edges: **6**
- qualified-edge same-label precision: **0.9813084112149533**
- cross-generator duplicate labels: **126**
- captured cross-generator duplicate labels: **85**
- cross-generator duplicate-label capture: **0.6746031746031746**
- all duplicate labels: **194**
- captured all-duplicate labels: **85**
- all-duplicate-label capture: **0.4381443298969072**

All preregistered gates passed:

- `qualified_edge_count >= 20`: PASS
- `qualified_edge_same_label_precision >= 0.95`: PASS
- `crossgenerator_duplicate_label_count >= 20`: PASS
- `crossgenerator_duplicate_label_capture >= 0.50`: PASS
- `all_duplicate_label_capture >= 0.25`: PASS

## Scientific interpretation

The exact shared-event + inherited-centroid relation is a high-purity, label-free indicator of cross-generator fragmentation on the frozen GMN development universe. It captures a material fraction of duplicate recoverable shower labels while making only 6 different-label links among 321 truth-qualified links.

This PASS authorizes **only a separately frozen target-excluded GMN consolidation successor based on this exact graph relation**. It does not choose a membership merge, representative rule, component score, ranking rule, suppression rule, or model feature.

The graph itself is now immutable for this mechanism. Do not rescue or optimize it with a different distance threshold, Jaccard/shared-event-count cutoff, P19-P19/P20-P20 edges, source-specific thresholds, top-k conditioning, label-conditioned edges, or a post-result graph search.

## Protected-data firewall

Throughout the pretruth freeze and binding evaluation:

- `sonotaco_2013_2014_access = false`
- `sonotaco_feature_access = false`
- `target_information_access = false`
- `target_region_events_accessed = false`
- `maarsy_scientific_access = false`
- `dms_scientific_access = false`
- protected solar-longitude exclusion remained `[20.0, 55.0]`

No candidate order, component construction, merged membership, suppression rule, family deletion, source quota, or threshold search was evaluated in this diagnostic.
