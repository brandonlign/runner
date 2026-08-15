# Recurrent-EOM HDBSCAN v1 — frozen GMN 2020/2021 archival temporal transfer

## Status and claim boundary

This protocol is frozen after recurrent-EOM HDBSCAN v1 passed its target-excluded GMN 2022/2023 development gate and the separately frozen exposed SonotaCo 2013/2014 v31-superiority benchmark, and **before the first recurrent-EOM outcome on GMN 2020/2021**.

GMN 2020/2021 is **not pristine** in the OrbitTrace repository: prior fixed4/RRF and multiplicity work already used these years. Therefore this run is a **retrospective fixed-protocol temporal robustness transfer only**. It is not external validation, does not satisfy the genuinely-unexposed generalization prerequisite, and cannot authorize target access.

No result from this transfer may alter recurrent-EOM v1.

## Frozen method

Use exact promoted recurrent-EOM HDBSCAN v1 unchanged:

- implementation blob `30ac3fa3bc47910370df528fcf3ae8ecb6277b47`;
- GEO6 representation `(cos(sol), sin(sol), sin(lon)*cos(lat), cos(lon)*cos(lat), sin(lat), vg/72)`;
- pooled two-year HDBSCAN hierarchy;
- `min_cluster_size=10`;
- `min_samples=10`;
- Euclidean metric;
- EOM cluster selection;
- `cluster_selection_epsilon=0`;
- `allow_single_cluster=False`;
- annual EOM contributions normalized by the accessible event count in each year;
- recurrent stability = minimum of the two normalized annual EOM values;
- exact HDBSCAN `get_clusters` extraction on the unchanged hierarchy;
- parent ranking by ordinary stability;
- successor ranking by recurrent stability, then ordinary stability, member count, deterministic family ID.

The only transport change from the binding GMN development runner is the calendar pair `2022,2023 -> 2020,2021` plus role/provenance strings and a year-generic integrity assertion. No method, representation, threshold, metric, ranking, truth definition, or scientific gate changes.

## Input and firewall

Use the same SHA-pinned GMN runtime/parser chain as the binding 2022/2023 run, with exactly 24 monthly sources for 2020 and 2021.

Before label use:

- remove solar longitude `[20°,55°]` exactly as in the promoted method;
- proposal generation, HDBSCAN fitting, recurrent stability, selected nodes, memberships, and pooled ranking are label-free;
- persist the complete parent and successor candidate payload before inspecting the sealed known-shower map.

Any missing monthly source, non-2020/2021 event, duplicate event ID, protected-region survivor, source/hash mismatch, parent extraction mismatch, or selected-node/label mismatch is a technical failure/no-result.

## Frozen evaluation

Use exactly the promoted GMN evaluator semantics, separately for 2020 and 2021:

- eligible known shower: at least 4 accessible events in that year;
- candidate is positive for a shower only at precision >= 0.5 and overlap >= 4;
- report recovered @25/@50/@100/@500, top-100 dominant precision, MRR, and median top-500 fragmentation.

The parent is vanilla HDBSCAN EOM on the exact same pooled hierarchy and events.

## Frozen gate

Use the exact promoted 2022/2023 recurrent-EOM gate with no relaxation:

For **each** year, successor must satisfy all of:

1. recovered@50 >= parent;
2. recovered@100 >= parent;
3. top-100 dominant precision >= parent;
4. MRR >= parent;
5. median top-500 fragmentation <= parent.

Across the two years:

6. recovered@100 must be **strictly higher in at least one year**;
7. recurrent-EOM must select a different HDBSCAN node set from vanilla EOM.

Pass token:

`PASS_RECURRENT_EOM_HDBSCAN_V1_GMN_2020_2021_RETROSPECTIVE_TRANSFER`

Otherwise:

`FAIL_RECURRENT_EOM_HDBSCAN_V1_GMN_2020_2021_RETROSPECTIVE_TRANSFER`

A failure is binding for this transfer and authorizes no rescue. A pass is positive retrospective robustness evidence only.

## Firewall declarations

The output must record:

- `scientific_role='TARGET_EXCLUDED_GMN_2020_2021_RETROSPECTIVE_TRANSFER_ONLY'`;
- `blind_exclusion=[20.0,55.0]`;
- `target_information_access=false`;
- `target_region_events_accessed=false`;
- `sonotaco_2013_2014_access=false`;
- `maarsy_scientific_access=false`;
- `dms_scientific_access=false`;
- `post_result_parameter_search=false`.
