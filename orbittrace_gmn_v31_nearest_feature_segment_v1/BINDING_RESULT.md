# GMN v31 local nearest-feature-segment v1 — binding result

Status: **FAIL — permanently closed**.

First technically valid run: GitHub Actions `31663287117`, job `94332478492`, commit `e8d804d1a181024f32ad10bb6ec0203fd1d5f267`, artifact `9167061715`, digest `sha256:9404aba10d5b1cdc019fbc3a3490610b20a29487a758d034560e4179405c28a3`.

The workflow reproduced the exact GMN v31 parent before candidate science:

- recovered@25 = 23
- recovered@50 = 41
- recovered@100 = 66
- top-100 dominant precision = 0.7229521515453452
- MRR = 0.050244164168646674
- qualified matches = 95
- prelabel SHA-256 `b45c4ce1a45bff515e411e211bc51dee879229ee97f7fcb7d8e7e05bfc106d09`
- feature matrix SHA-256 `fea3b063772c75b675e37a227b53a4aa3c5b86fdcbfcef1487b1e1448689cdf5`
- parent raw OOF margin SHA-256 `f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`

Frozen local nearest-feature-segment successor after exact parent diversity and equal hard-order fusion:

- recovered@25 = **25**
- recovered@50 = **41**
- recovered@100 = **64**
- recovered@500 = 95
- top-100 dominant precision = **0.7108219582092694**
- MRR = **0.05046548227391713**
- qualified matches = 95

Local segment order before hard-order fusion:

- recovered@25 = 23
- recovered@50 = 42
- recovered@100 = 63
- recovered@500 = 95
- top-100 dominant precision = 0.6403382646702291
- MRR = 0.03832104984255586
- qualified matches = 95

No selected endpoint pair had an identical feature vector (`duplicate_endpoint_vector_uses = 0`). Segment-margin SHA-256 is `ff2d4b97f207008942dcc86643fbc4bac41ae2f2c372a49b8f303eb9c66f608e`.

Binding gates:

- recovered@100 strictly better than parent: **FAIL** (64 < 66)
- recovered@50 nonregression: **PASS** (41 = 41)
- recovered@25 nonregression: **PASS** (25 > 23)
- top-100 precision nonregression: **FAIL** (0.7108219582092694 < 0.7229521515453452)
- MRR nonregression: **PASS** (0.05046548227391713 > 0.050244164168646674)
- qualified count identical: **PASS** (95)

Therefore `GMN_V31_NEAREST_FEATURE_SEGMENT_V1` is not promotable and does not authorize SonotaCo access.

Per the frozen protocol, this exact local-manifold lane is closed with no result-informed rescue: no infinite-line variant, all-pairs feature-line variant, nearest-three plane/simplex, endpoint group restriction, segment-length cutoff, weighted point/segment blend, transformed segment margin, alternate endpoint count, metric/feature/scaling/diversity/fusion change, or post-result second search is authorized.

Interpretation is limited to the tested mechanism. Local same-class segment interpolation improved very-early placement and MRR but degraded the primary top-100 recovery and top-100 precision. That pattern does not support replacing v31's nearest-point class geometry with the frozen two-endpoint closed-segment geometry.

Scientific firewall remained intact: GMN 2022+2023 target-excluded development only; protected solar longitude 20°–55°, OrbitTrace target information/events, SonotaCo 2013/2014, MAARSY, and DMS were not accessed.
