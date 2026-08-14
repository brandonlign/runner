# RFT v1 cached-generate semantic equivalence result

**PASS — engineering identity only.**

Binding audit run `31815566243`, job `94816281335`, artifact `9224847857`, artifact digest `sha256:75ca0bf59e3b1cff29d5480097c1a2d4455c88d65db2edb633a7426eccb1b4cb`.

Frozen source identities:
- RFT v1 science blob `a5d5371f0c30a9c57ee4d8756ea41f454cd86301`;
- cached runner blob `2a599c6e8247eb819a1090591d586526eda6c0c1`.

Verdict: `PASS_RFT_V1_CACHED_GENERATE_SEMANTIC_EQUIVALENCE`.

Complete ordered output dictionaries were exactly equal under Python object equality and canonical JSON bytes for all four frozen evaluation modes:
- primary (`ownership=True`, trim on, persistence on): 1 synthetic output, SHA-256 `374da876732956fe09c8d8e28e64f79ba6c933698b5aaa4464fdf1ab3a5b8455`;
- no-path-ownership: 1 output, `b7313906ad5c950953ce1f5e9939cd5d0fd3fad96d5fe46651da49d8c6e2589c`;
- no-persistence: 2 outputs, `7fa65a0b4906c1f5cdcacfd5e01121db525d85a3ce47e788415daded74d8fbb0`;
- no-trim: 1 output, `374da876732956fe09c8d8e28e64f79ba6c933698b5aaa4464fdf1ab3a5b8455`.

The fixture explicitly exercised a persistence-passing tube, a persistence-rejected tube, both ownership modes, persistence on/off, and trim on/off. Frozen `fit_trim`, Jaccard persistence, scoring, family hashing and output sorting were not replaced.

No catalogue, labels, scientific endpoint, target data, SonotaCo, GMN 2023, MAARSY or DMS were accessed. This PASS proves only downstream cached-generation semantic equivalence given identical tubes. Atomization equivalence remains a separate audit.
