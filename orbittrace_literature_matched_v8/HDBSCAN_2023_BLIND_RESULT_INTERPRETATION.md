# Blind-safe HDBSCAN 2023 result interpretation — frozen before downstream reuse

Workflow run `31226945294` executed the preregistered comparison-only blind repair from `EXACT_ROW_CORRECTION_1.md` on the exact SonotaCo 2023 archive.

The patched runner SHA-256 was `2445c954ed863a77c3be0b25b2d0dc1a61dbdaa8d533400015fde30d92139783`. The underlying published-method configuration remained unchanged: `hdbscan==0.8.44`, unstandardized GEO six-vector, `min_cluster_size=100`, package-default `min_samples`, Euclidean metric, and `eom` selection.

The runner emitted complete primary and full-catalogue HDBSCAN outputs, including `full_catalogue_assignments.jsonl.gz` SHA-256 `35f629b1dff4d04cdc13aa8224171ec1ab8e06b52836900d66ff978b5c235761` and result JSON SHA-256 `098b7230c73a51c44c8de72dfe184fb4829ffb44e5b3744f7e522e7ea7e8edd4`.

Its legacy verdict string was `FAIL_SONOTACO_2023_HDBSCAN_ONE_SHOT_TRANSFER` for exactly two gates:

- `exact_row_count = false`
- `all_rows_parsed = false`

Those gates encode the pre-blinding expectation that every raw archive row is retained by the parser. They are structurally incompatible with the preregistered comparison requirement to remove solar longitude 20°–55° before any other field or shower label is read. They therefore cannot serve as integrity gates for this blind-safe comparison rerun.

Every method-relevant execution gate in the emitted result is true:

- exact archive hash;
- exact effective header width;
- frozen HDBSCAN version;
- frozen HDBSCAN parameters unchanged;
- nonempty quality catalogue;
- primary reference showers present;
- primary clustering completed;
- full-catalogue clustering completed.

The blind-safe rerun produced 26,460 full-catalogue quality-filtered events, 14 non-noise clusters, and the expected sparse behavior of the unchanged `min_cluster_size=100` catalogue method. These scientific outputs are preserved regardless of whether they favor v8.

## Downstream eligibility rule

The full-catalogue assignment file may be used in the exact-row pairwise benchmark **only after a separate GitHub Actions verification confirms**:

1. its SHA-256 is exactly `35f629b1dff4d04cdc13aa8224171ec1ab8e06b52836900d66ff978b5c235761`;
2. every assignment ID resolves to the exact SonotaCo 2023 archive;
3. zero assignment IDs have solar longitude in 20°–55°;
4. no shower label or other excluded-row content is inspected by that verification.

If any of those checks fails, the assignment is ineligible and HDBSCAN 2023 remains a genuine technical limitation for the final matched benchmark.

No HDBSCAN or v8 parameter, benchmark metric, size bin, or `delta >= 0.10` decision gate may change after this interpretation. No OrbitTrace target information or excluded-interval contents may be accessed.
