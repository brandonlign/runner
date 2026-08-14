# Cross-year-core HDBSCAN v1 — exact Boruvka equivalence audit result

**Engineering result: POSITIVE. Scientific result: NONE.**

The scalable cross-year-core implementation passed its synthetic-only equivalence gate against the independently frozen dense mathematical reference.

- workflow run: `31846997065`
- artifact: `9236242893`
- artifact digest: `sha256:084483583f08452a455462dd655a4092895332f3d89561686d3556944e10aa19`
- execution head: `71bdded869073b4c6ac08d09ef702ee6c552996e`
- verdict: `PASS_CROSSYEAR_CORE_BORUVKA_DENSE_EQUIVALENCE_V1`
- absolute engineering tolerance frozen before GMN: `1e-12`
- HDBSCAN Boruvka mode: exact (`approx_min_span_tree=False`), `n_jobs=1`

Across all five preregistered synthetic fixture classes, the scalable implementation matched the dense reference in opposite-year core distances, MST edge-weight multiset, connectivity filtration, condensed-tree lambda/child-size structure, and the recurrent-EOM selected partition within the predeclared tolerance.

The scalable route uses HDBSCAN's exact KD-tree Boruvka traversal over the unchanged pooled GEO6 point cloud. Only the core-distance initialization is supplied by the exact opposite-year 10-nearest-neighbor table. No approximate neighbor graph or approximate spanning tree is used.

This engineering PASS satisfies the mandatory implementation-equivalence condition in the frozen protocol. It does not itself contain a GMN scientific result. The first technically valid target-excluded GMN 2022+2023 development execution, once separately source-pinned and activated, is binding.