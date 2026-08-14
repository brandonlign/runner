# Cross-year-core HDBSCAN v1 — first GMN attempt technical no-result

**Scientific result: NONE. Engineering result: NEGATIVE runtime compatibility finding.**

The first activated target-excluded GMN workflow did not reach a prelabel freeze or any truth evaluation.

- workflow run: `31847359367`
- job: `94916402012`
- execution head: `cdeda2029745fd8cd86cb5f762233a1ba50c9bd0`
- uploaded failure artifact: `9236492700`
- artifact digest: `sha256:fb0cb20bd3a78fe346af8bcc1f28bfa1a5394093ab51b8c4f767712ccb81f4dd`
- failure time: `2026-08-14T22:44:35Z`

The run stopped at the parent single-linkage provenance accessor:

`parent_model.single_linkage_tree_._raw_tree`

under installed `hdbscan==0.8.43`, with:

`AttributeError: 'SingleLinkageTree' object has no attribute '_raw_tree'`.

This is a wrapper/API-accessor error. HDBSCAN's `SingleLinkageTree` stores the linkage as `_linkage` and exposes it through the public `to_numpy()` method; `_raw_tree` is not a `SingleLinkageTree` attribute.

The preserved artifact contains exactly these scientific-intermediate arrays plus environment/provenance:

- `CROSSYEAR_CORE_DISTANCES.npy`
- `CROSSYEAR_CORE_MST.npy`
- `CROSSYEAR_CORE_SINGLE_LINKAGE.npy`
- `CROSSYEAR_CORE_CONDENSED_TREE.npy`
- `environment.txt`
- `execution_commit.txt`
- `python_version.txt`
- `source_input_output_sha256.txt`

It contains **no** `CROSSYEAR_CORE_HDBSCAN_V1_PRELABEL.json` and **no** `CROSSYEAR_CORE_HDBSCAN_V1_GMN_DEVELOPMENT.json`. Therefore the sealed shower truth was never evaluated and no cross-year-core GMN scientific verdict exists.

The hierarchy arrays are preserved as engineering intermediates only. They may not be inspected for label/performance-informed method changes. The only authorized repair is semantic-neutral tree-access plumbing that leaves the frozen protocol, Boruvka adapter, cross-year-core geometry, EOM extraction, ranking, metrics, and gate unchanged.
