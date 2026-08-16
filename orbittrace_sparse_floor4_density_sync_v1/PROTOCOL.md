# OrbitTrace sparse floor-4 density-synchronous recurrent-EOM v1 — frozen protocol

## Scientific goal
Test one minimal structural change aimed directly at sparse-stream recovery: lower only HDBSCAN's `min_cluster_size` from the promoted value 10 to **4**, while keeping `min_samples=10`, GEO6, the pooled target-excluded data, density-synchronous recurrent-EOM node selection, and ranking semantics unchanged.

The benchmark itself defines an eligible known shower in a year as at least **4 labeled events**. A hard 10-member HDBSCAN cluster-size floor can therefore make benchmark-eligible sparse structures impossible to become candidate clusters even before recurrence is evaluated. Density-synchronous recurrent-EOM already requires support from both years over the cluster lifetime; v1 asks whether retaining the conservative 10-neighbor density estimate while allowing 4-member branches exposes real sparse recurrent streams without sacrificing precision.

A GMN development PASS requires a meaningful improvement over the frozen 179 winner: total recovered@100 >= **184** (+5), with no annual regression in recovered@50, recovered@100, top-100 dominant precision, MRR, or median top-500 fragmentation. Only a clean GMN pass earns one separately frozen SonotaCo transfer test.

## Duplicate audit
Before freezing, repository code/commit/branch searches found no prior OrbitTrace recurrent-EOM or density-synchronous HDBSCAN experiment with `min_cluster_size=4`. The branch named `agent/orbittrace-hdbscan-exact-lower-bounds-v1` was inspected and concerns physical `q/e` comparator bounds, not HDBSCAN cluster-size bounds.

## Binding baseline
Compare only against the frozen density-synchronous recurrent-EOM GMN winner:
- run `31852836840`;
- artifact `9238142199`;
- 2022 recovered@100 = 89;
- 2023 recovered@100 = 90;
- total recovered@100 = **179**;
- ordered-membership SHA256 `e8f374ad03e7072463118ee6440a54d96d11e3aab17202cfe336f866530224f2`.

The baseline is read from its frozen artifact and is never recomputed for comparison.

## Data and firewall
- GMN 2022+2023 development only.
- Solar longitude 20°–55° excluded before clustering or any normalization/statistic.
- OrbitTrace target information and protected-region events inaccessible.
- Known-shower labels remain sealed until the complete successor hierarchy, selected nodes, memberships, scores, and order are durably persisted.
- SonotaCo 2013/2014, ASFN, EFN, AMOS, MAARSY, and DMS are not accessed.

## Representation held fixed
Use exact inherited GEO6:

`[cos(sol), sin(sol), sin(sun_lon)*cos(ecl_lat), cos(sun_lon)*cos(ecl_lat), sin(ecl_lat), vg/72]`.

No feature scaling, whitening, background factor, orbital element, uncertainty proxy, learned metric, or alternate geometry enters v1.

## Sole scientific change
Fit exact `hdbscan==0.8.43` on the pooled accessible 2022+2023 GEO6 rows with:
- `min_cluster_size=4` **(sole change; parent = 10)**;
- `min_samples=10` **unchanged**;
- `metric='euclidean'` unchanged;
- `cluster_selection_method='eom'` unchanged;
- `cluster_selection_epsilon=0.0` unchanged;
- `allow_single_cluster=False` unchanged;
- `prediction_data=False` unchanged.

Keeping `min_samples=10` deliberately preserves the promoted detector's conservative local-density/core-distance definition. This experiment is not a two-parameter relaxation.

Apply the exact frozen density-synchronous recurrent-EOM objective to the resulting condensed tree:
- reconstruct annual normalized EOM values exactly;
- integrate the minimum annual normalized alive-mass curve over each node's density lifetime;
- select nodes with the exact inherited EOM mirror using that synchronous stability;
- rank by descending synchronous stability, ordinary HDBSCAN stability, member count, deterministic family ID.

The successor candidate minimum support is therefore 4, matching the only changed HDBSCAN branch floor.

## Pretruth freeze
Before known-shower truth is indexed, persist:
- exact source/input hashes and event counts;
- exact HDBSCAN configuration showing `min_cluster_size=4`, `min_samples=10`;
- condensed-tree SHA256;
- selected density-synchronous nodes;
- complete ordered candidate memberships and scores;
- candidate count, smallest/largest selected family size, and ordered-membership SHA256;
- counts of selected families with pooled sizes 4–9 and >=10;
- firewall state.

## Binding structural gates
Require before/independent of truth:
- at least 100 selected candidate families;
- every selected family has >=4 members;
- at least one selected 4–9 member family (mechanism active in the intended sparse region);
- largest selected family <=1% of all accessible events;
- ordered memberships differ from the frozen 179 winner;
- density-synchronous annual reconstruction and tree-integrity checks pass.

A structural failure is a binding scientific failure unless caused by a source/runtime mismatch before successor output is formed.

## Binding GMN success gate
PASS requires all of:
1. total recovered@100 >= **184**;
2. 2022 recovered@50 >= frozen winner and recovered@100 >=89;
3. 2023 recovered@50 >= frozen winner and recovered@100 >=90;
4. top-100 dominant precision not lower in either year;
5. MRR not lower in either year;
6. median top-500 fragmentation not higher in either year;
7. every structural, source-pin, reproducibility, and firewall gate passes.

Anything else is FAIL.

## Transfer rule
A GMN PASS is only the first goal-level step. Freeze this exact floor-4 / `min_samples=10` algorithm before one exposed SonotaCo 2013/2014 transfer benchmark. No GMN-derived candidate identities, ranks, or numerical geometry values transfer.

Broad generalization still requires a genuinely untouched external survey; SonotaCo remains exposed development evidence only.

## No rescue
If v1 fails, permanently close this exact floor-4 architecture. Do not retry after outcome with:
- `min_cluster_size` 5–9 or 2–3;
- `min_samples=4` or any other `min_samples` change;
- leaf selection;
- epsilon changes;
- post-filtering small clusters;
- sparse-cluster bonuses or penalties;
- alternate ranking;
- feature/metric changes;
- target-guided exceptions.

Any later successor must have a distinct independently motivated mechanism.