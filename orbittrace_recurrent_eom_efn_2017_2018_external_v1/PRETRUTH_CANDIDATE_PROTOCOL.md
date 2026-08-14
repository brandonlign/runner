# Recurrent-EOM HDBSCAN v1 — EFN 2017/2018 pretruth candidate freeze

**Status: frozen after binding Stage-2 retained native geometry and before any EFN `Shower` access or candidate-generation outcome.**

This protocol implements only the pretruth candidate-freeze phase already required by `PROTOCOL.md`. It changes no scientific method, input representation, HDBSCAN parameter, ranking rule, evaluator, external-validation gate, or label rule.

## Scientific role and firewall

- catalogue: fixed published EFN release `J/A+A/667/A157`;
- years: exactly 2017 and 2018;
- original catalogue size: exactly 824 records;
- protected solar-longitude interval: inclusive `[20.0,55.0]`, already excluded before geometry access;
- binding retained cohort: exactly 338 events in 2017 and 444 in 2018;
- this phase may read only the binding Stage-2 canonical geometry artifacts;
- `Shower`, `Object`, all orbit fields, target information/events, MAARSY, and DMS remain inaccessible;
- candidate generation must complete and be hash-frozen before Stage 3 is authorized.

## Binding Stage-2 geometry

Binding Stage-2 run: `31841984405`

Binding job: `94900635521`

Binding head: `9ef289fd6bc072df78c9a859ddd3945ccf7d2dc3`

Binding artifact: `9234569659`

Artifact digest:

`sha256:38f817f1a2c3be0ceef42e1f69c7c7607bc8b84431d663fcf308911c483ec0b3`

Binding Stage-2 freeze Git blob:

`463d31b738c3c133be000c36ee88e025d1565c5a`

Canonical geometry file SHA-256:

- 2017: `7583ae47b78401b52dfd9fe2fa1863580b987c69b3d6c8142445f6f3795e82b2`
- 2018: `01491fcecbd6e407a8c7424239210e2f233a22e527c9b74d694d0d2f936f9008`

Every input row must contain exactly:

`id, year, sol, sun_lon, ecl_lat, vg, iau, complex_key`

with `iau=0`, `complex_key='HIDDEN'`, positive finite `vg`, and canonical `sol` outside `[20,55]`.

## Exact promoted method

Pinned recurrent-EOM implementation Git blob:

`30ac3fa3bc47910370df528fcf3ae8ecb6277b47`

Pinned promoted development runner Git blob, used as the authoritative implementation template:

`fdc4f3f6e037014aadfcc3ce41b7344aa0a80b2c`

Exact runtime:

- Python 3.11;
- `numpy==2.1.3`;
- `scipy==1.14.1`;
- `scikit-learn==1.7.1`;
- `hdbscan==0.8.43`.

Exact GEO6 representation for each already-canonical Stage-2 row:

`(cos(sol), sin(sol), sin(sun_lon)*cos(ecl_lat), cos(sun_lon)*cos(ecl_lat), sin(ecl_lat), vg/72.0)`

with angular fields converted from degrees to radians only for construction of these trigonometric coordinates.

Exact HDBSCAN configuration:

- `min_cluster_size=10`;
- `min_samples=10`;
- metric `euclidean`;
- `cluster_selection_method='eom'`;
- `cluster_selection_epsilon=0.0`;
- `allow_single_cluster=False`;
- `prediction_data=False`.

Fit one pooled 2017+2018 hierarchy on the exact 782 Stage-2 rows.

## Vanilla parent extraction

1. Fit vanilla HDBSCAN with the exact configuration above.
2. Set `tree = model.condensed_tree_._raw_tree`.
3. Compute ordinary stability with `hdbscan._hdbscan_tree.compute_stability(tree)`.
4. Emit parent labels using the promoted `eom_labels(tree, ordinary_stability)` path.
5. Require exact canonical-partition identity between custom parent labels and `model.labels_`.
6. Identify parent selected nodes with the frozen `selected_eom_nodes` helper.
7. Require compact positive labels to be exactly `0..N-1` and node count to equal positive-label count.

## Recurrent-EOM successor extraction

1. Supply the exact input-year vector aligned with the pooled geometry rows to frozen `recurrent_stability(tree, years)`.
2. Recurrent stability for a node remains the minimum of its 2017- and 2018-normalized EOM contributions.
3. Emit successor labels with frozen `eom_labels(tree, recurrent_stability)` on the **same condensed hierarchy**.
4. Identify successor selected nodes with frozen `selected_eom_nodes`.
5. Require compact positive labels to be exactly `0..N-1` and node count to equal positive-label count.

No parameter, weight, scale, annual combiner, hierarchy, distance, or feature change is permitted.

## Frozen candidate construction and ordering

For each selected node, membership is the sorted exact EFN `id` list assigned to its corresponding compact label. Every selected candidate must contain at least 10 members.

Deterministic family ID:

`sha256(prefix + '|' + '|'.join(sorted_member_ids)).hexdigest()[:20]`

Prefixes:

- vanilla parent: `HDBEOM`;
- recurrent successor: `REOM1`.

Vanilla candidate fields:

- `family_id`;
- `node_id`;
- `event_ids`;
- `member_count`;
- `ordinary_stability`.

Recurrent candidate fields:

- all fields above;
- `recurrent_stability`.

Vanilla order is fixed as:

1. descending ordinary stability;
2. descending member count;
3. ascending deterministic family ID.

Recurrent order is fixed as:

1. descending recurrent stability;
2. descending ordinary stability;
3. descending member count;
4. ascending deterministic family ID.

No label, shower code, truth statistic, quality field, orbit field, or result-informed score may influence candidate membership or ordering.

## Complete pretruth artifact requirement

Before any Stage-3 access, persist a single deterministic JSON payload containing at minimum:

- scientific role, catalogue, years, original 824-row identity, retained counts and Stage-2 geometry hashes;
- exact source/runtime/configuration identities;
- exact pooled event order and year vector identity;
- complete raw condensed-tree records (`parent`, `child`, `lambda_val`, `child_size`) and a byte-level condensed-tree SHA-256;
- complete ordinary stability mapping;
- complete annual recurrent stability mapping and recurrent stability mapping;
- vanilla selected node IDs;
- recurrent selected node IDs;
- every vanilla candidate membership and ordering score in complete deterministic rank order;
- every recurrent candidate membership and ordering score in complete deterministic rank order;
- canonical partition hashes for vanilla model labels, custom vanilla labels, and recurrent labels;
- mechanism-active flag (`vanilla selected nodes != recurrent selected nodes`);
- firewall declarations showing no truth-bearing field was available.

The workflow must hash-freeze the complete pretruth payload before any Stage-3 `Shower` query exists in that execution.

## Already-frozen external evaluator and gate

No metric is evaluated in this pretruth phase. After the complete pretruth payload is frozen, the evaluator/gate remain exactly those in `PROTOCOL.md`:

For each year, recurrent-EOM must have:

1. recovered@50 >= vanilla EOM;
2. recovered@100 >= vanilla EOM;
3. top-100 dominant precision >= vanilla EOM;
4. MRR >= vanilla EOM;
5. median top-500 fragmentation <= vanilla EOM.

Across years:

6. recovered@100 strictly higher in at least one year;
7. recurrent selected node set differs from vanilla.

If either year has zero eligible shower labels (fixed support >=4), endpoint is power-inconclusive.

Pass token:

`PASS_RECURRENT_EOM_HDBSCAN_V1_EFN_2017_2018_EXTERNAL_VALIDATION`

Fail token:

`FAIL_RECURRENT_EOM_HDBSCAN_V1_EFN_2017_2018_EXTERNAL_VALIDATION`

Power-inconclusive token:

`INCONCLUSIVE_RECURRENT_EOM_HDBSCAN_V1_EFN_2017_2018_EXTERNAL_VALIDATION_LABEL_POWER`

The first technically valid labeled endpoint is binding. No EFN-specific rescue or threshold/ranking/feature/parameter search is authorized.
