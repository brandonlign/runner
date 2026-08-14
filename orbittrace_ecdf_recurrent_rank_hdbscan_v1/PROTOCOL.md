# OrbitTrace ECDF recurrent-rank HDBSCAN v1 — frozen protocol

## Status

Frozen before implementation and before the first technically valid scientific outcome of this successor.

This successor starts from the promoted recurrent-EOM HDBSCAN v1 method without changing its hierarchy, selected nodes, memberships, GEO6 representation, HDBSCAN parameters, or recurrent-EOM cluster-selection objective. Its only scientific change is the **label-free ordering of the already-selected recurrent-EOM families**.

The frozen motivation is scale invariance across observing years: annual EOM contributions are normalized by accessible event count, but their remaining numerical scales can still differ because the two yearly empirical density landscapes need not have the same distribution. A raw minimum therefore mixes recurrence strength with cross-year scale. The successor replaces only the final cross-year ordering with a rank/cdf representation that is invariant to any strictly increasing reparameterization applied separately to either year's annual EOM contributions.

This is not a rescue of reciprocal-transfer, cross-year-core, consensus-EOM, thinning stability, or the ASFN result. NASA ASFN 2018/2019 has already been scientifically observed and is permanently spent for this successor; no ASFN geometry, label, metric, candidate, threshold, or result may be used to construct, select, tune, or validate this method. Development is exactly the permanent target-excluded GMN 2022+2023 split. Any future external validation would require an already-untouched separately frozen panel such as the existing AMOS route and may not be modified in response to this successor.

## 1. Exact parent

The parent is promoted recurrent-EOM HDBSCAN v1:

- implementation Git blob `30ac3fa3bc47910370df528fcf3ae8ecb6277b47`;
- GMN runner Git blob `fdc4f3f6e037014aadfcc3ce41b7344aa0a80b2c`;
- binding GMN run `31827903547`;
- parent result SHA-256 `433c641f57122b244b9476f5cbcb5e6f82956d9467270a9f24945600a32d2106`;
- parent prelabel SHA-256 `e304f6660697ed27a7e2e546ba2b9f2ecdb43f923745cb7424a3781ad55b9ad1`.

All parent scientific choices remain exact:

- `GEO6 = (cos(sol), sin(sol), sin(sun_lon) cos(ecl_lat), cos(sun_lon) cos(ecl_lat), sin(ecl_lat), vg/72)`;
- pooled target-excluded GMN 2022+2023 hierarchy;
- HDBSCAN `min_cluster_size=10`, `min_samples=10`, Euclidean metric, EOM, `cluster_selection_epsilon=0`, `allow_single_cluster=False`;
- annual EOM contribution normalized by accessible event count in each year;
- recurrent cluster stability used for EOM extraction is `min(E_2022, E_2023)`;
- exact recurrent-EOM selected node set and memberships are retained unchanged.

## 2. Empirical-CDF annual rank transform

Let `N` be exactly the set of nodes selected by the promoted recurrent-EOM EOM extraction on the pooled hierarchy. For each selected node `i`, let `A_y(i)` be its already-computed normalized annual EOM contribution in year `y`.

For each year independently, define the frozen midrank empirical-CDF value

`Q_y(i) = ( L_y(i) + 0.5 * E_y(i) ) / |N|`,

where:

- `L_y(i)` is the number of selected nodes `j in N` with `A_y(j) < A_y(i)`;
- `E_y(i)` is the number of selected nodes `j in N` with `A_y(j) == A_y(i)`.

Equality is exact IEEE-754 equality on the already-computed frozen annual EOM floats; there is no tolerance, binning, rounding, jitter, or learned calibration.

This midrank ECDF is fixed because it treats tied annual contributions symmetrically and is invariant to strictly increasing transformations of each year's annual-stability scale.

No shower truth, v31 score, SonotaCo metric, ASFN result, comparator budget, family quality statistic, uncertainty field, source label, or target information enters `Q_y`.

## 3. Frozen successor ranking

The successor candidate catalogue is **exactly the same candidates, memberships, and family IDs as promoted recurrent-EOM**. Only order changes.

Rank candidates lexicographically by:

1. descending `min(Q_2022, Q_2023)` — worst-year ECDF recurrence rank;
2. descending `max(Q_2022, Q_2023)` — stronger-year ECDF rank as a tie breaker;
3. descending promoted-parent `recurrent_stability`;
4. descending ordinary HDBSCAN stability;
5. descending member count;
6. ascending deterministic promoted-parent family ID.

No weighted blend, percentile threshold, alternate ECDF convention, year weighting, smoothing, clipping, rank fusion, learned model, or post-outcome tie-break change is authorized.

The parent candidate set must be byte-for-byte membership-identical after canonicalization. If any selected node or family membership changes, the run is technically invalid rather than a scientific result.

## 4. Required pre-outcome synthetic audit

Before GMN activation, deterministic synthetic fixtures must prove all of the following:

1. the ECDF ranker returns exactly the same candidate membership multiset supplied to it;
2. applying distinct strictly increasing affine transforms to the two annual-stability vectors leaves the complete successor order unchanged;
3. applying distinct strictly increasing exponential transforms to the two annual-stability vectors leaves the complete successor order unchanged;
4. exact ties receive identical midrank ECDF values;
5. a fixture with deliberately discordant annual scales changes raw-min ordering but leaves ECDF ordering determined only by within-year ranks, proving the intended mechanism is active;
6. repeated execution is deterministic;
7. no labels, GMN, SonotaCo, ASFN, AMOS, target data, MAARSY, or DMS are accessed.

A failed synthetic audit closes this implementation until an engineering-only correction restores the exact frozen mathematical definition. It does not authorize a scientific change.

## 5. Binding GMN evaluation

The first technically valid target-excluded GMN 2022+2023 outcome is binding.

Evaluation semantics are exactly the promoted recurrent-EOM semantics:

- same accessible event IDs and event counts;
- same protected `[20.0,55.0]` exclusion;
- same hidden shower truth object;
- eligible shower = at least 4 labeled events in evaluated year;
- qualified family = dominant shower precision >= 0.5 and overlap >= 4;
- each year evaluated by restricting pooled family members to that year's event IDs while retaining the pooled rank;
- report recovered known showers @25/@50/@100/@500, full-catalogue qualified matches, top-100 dominant precision, MRR, and median top-500 fragmentation.

The workflow must reproduce the exact promoted parent metrics from the exact pinned parent prelabel/result before the successor comparison is accepted.

## 6. Frozen promotion gate

ECDF recurrent-rank v1 passes only if all are true versus exact promoted recurrent-EOM:

1. recovered@100 is strictly higher in at least one year and not lower in the other;
2. recovered@50 is not lower in either year;
3. top-100 dominant precision is not lower in either year;
4. MRR is not lower in either year;
5. median top-500 fragmentation is not higher in either year;
6. the successor candidate memberships are exactly identical to the parent candidate memberships;
7. the complete successor order differs from the parent order, proving the rank mechanism is active.

Recovered@25, recovered@500, and full-catalogue qualified matches are reporting-only.

PASS token:

`PASS_ECDF_RECURRENT_RANK_HDBSCAN_V1_GMN_DEVELOPMENT`

FAIL token:

`FAIL_ECDF_RECURRENT_RANK_HDBSCAN_V1_GMN_DEVELOPMENT`

A FAIL permanently rejects this exact ranking successor. No ECDF definition change, quantile threshold, raw/ECDF blend, year weighting, alternate tie handling, rank fusion, or other result-informed rescue is authorized.

A PASS authorizes only a separately frozen exposed-development parent-superiority benchmark if one was frozen before the GMN result. It does not authorize ASFN reuse, AMOS protocol changes, or protected target access.

## 7. Firewall and chronology

- protected solar longitude `[20.0,55.0]` remains inaccessible;
- no OrbitTrace target information/events;
- no SonotaCo scientific access during GMN method selection;
- no ASFN access of any kind during method selection; ASFN is spent and ineligible for this successor;
- no AMOS, EFN, MAARSY, or DMS scientific access;
- candidate order must be hash-frozen before GMN shower truth is evaluated;
- first technically valid scientific outcome is binding;
- no post-result scientific change is permitted.
