# OrbitTrace reciprocal-transfer HDBSCAN v1 — frozen protocol

## Status

Frozen before the first technically valid scientific outcome of reciprocal-transfer HDBSCAN v1.

This is a separately motivated successor to the already-promoted recurrent-EOM HDBSCAN v1. It is **not** a rescue of failed consensus-EOM or cross-year-core HDBSCAN. It does not alter the pooled recurrent-EOM parent, change HDBSCAN parameters, or use any result from the failed cross-year-core candidate to choose a threshold, weight, radius, feature, or hyperparameter.

Scientific firewall remains binding:

- protected solar longitude `[20.0,55.0]` is inaccessible;
- no OrbitTrace target information/events;
- no SonotaCo 2013/2014 access during method selection;
- no AMOS, EFN, MAARSY, or DMS scientific access;
- development data are exactly the permanent target-excluded GMN 2022+2023 population;
- all candidate memberships/ranks must be frozen before shower truth is evaluated;
- first technically valid outcome is binding;
- no post-result threshold, majority rule, HDBSCAN parameter, prediction rule, ranking rule, or matching rescue is allowed.

## 1. Parent and fixed representation

The promotion parent remains exact recurrent-EOM HDBSCAN v1:

- implementation Git blob `30ac3fa3bc47910370df528fcf3ae8ecb6277b47`;
- GMN development runner Git blob `fdc4f3f6e037014aadfcc3ce41b7344aa0a80b2c`;
- binding GMN run `31827903547`;
- binding parent result SHA-256 `433c641f57122b244b9476f5cbcb5e6f82956d9467270a9f24945600a32d2106`.

The input representation is unchanged:

`GEO6 = (cos(sol), sin(sol), sin(sun_lon)*cos(ecl_lat), cos(sun_lon)*cos(ecl_lat), sin(ecl_lat), vg/72)`.

No orbital elements, shower labels, source labels, or comparator information enter the method.

## 2. Scientific motivation

Promoted recurrent-EOM builds one pooled two-year HDBSCAN hierarchy and changes flat-cluster selection so persistence must be supported in both observing years. Reciprocal-transfer HDBSCAN asks a distinct question: **does the same density structure exist when each observing year is clustered independently?**

This avoids assuming that one pooled hierarchy is the correct topological representation of both years. It also avoids introducing a cross-year distance threshold. Each annual HDBSCAN model supplies its own density hierarchy, and HDBSCAN's standard out-of-sample prediction operator transports points from one year into the clustering learned from the other.

The recurrence criterion is reciprocal transport consistency: an annual cluster survives only when a strict majority of its members are assigned to one cluster in the opposite-year model, and that opposite-year cluster has a strict-majority mapping back to the original cluster.

A strict majority (`> 1/2`) is used because it is the unique threshold at which one counterpart necessarily contains more mapped members than all alternatives combined. No majority fraction is tuned or searched.

## 3. Annual HDBSCAN models

Fit two completely separate standard HDBSCAN models, one to target-excluded GMN 2022 GEO6 rows and one to target-excluded GMN 2023 GEO6 rows.

Both use exactly:

- `min_cluster_size=10`;
- `min_samples=10`;
- metric `euclidean`;
- `cluster_selection_method='eom'`;
- `cluster_selection_epsilon=0.0`;
- `allow_single_cluster=False`;
- `prediction_data=True` solely so HDBSCAN's standard prediction operator is available;
- all other HDBSCAN defaults unchanged.

The selected annual clusters are exactly the model's native non-noise EOM labels. No custom EOM objective is used in the successor.

Before any scientific outcome, a zero-data engineering audit must show that toggling only `prediction_data=False -> True` leaves the ordinary HDBSCAN labels, condensed-tree selected partition, and `cluster_persistence_` values unchanged on deterministic synthetic fixtures.

## 4. Frozen cross-year transport operator

Use the exact `hdbscan.prediction.approximate_predict` implementation supplied by the pinned HDBSCAN runtime.

For every 2022 event, predict its label under the fitted 2023 model. For every 2023 event, predict its label under the fitted 2022 model. Prediction probabilities are recorded diagnostically but **do not** enter matching, candidate existence, membership, or ranking.

No cross-year model is refit with transported points. The prediction operator assigns each opposite-year point to an already-existing annual clustering or to noise (`-1`).

## 5. Strict-majority annual mapping

For each selected annual cluster `A` in 2022:

1. take exactly its native 2022 members;
2. inspect those members' predicted labels under the 2023 model;
3. count every predicted label including noise;
4. `A` has a forward counterpart `B` only if one **non-noise** 2023 cluster label receives strictly more than half of all members of `A`;
5. otherwise `A` has no counterpart.

Apply the identical rule from each selected 2023 cluster back into the 2022 model.

Because the rule is strict majority, each annual cluster has at most one counterpart.

## 6. Reciprocal families

A recurrent family exists only for an annual-cluster pair `(A_2022, B_2023)` satisfying both:

- the strict-majority forward counterpart of `A_2022` is `B_2023`; and
- the strict-majority backward counterpart of `B_2023` is `A_2022`.

Each annual cluster may appear in at most one recurrent family. No secondary nearest-neighbour matching, Hungarian matching, radius, centroid threshold, probability threshold, fallback, merge, split, or orphan rescue is allowed.

Family membership is exactly the union of:

- native members of annual cluster `A_2022` in 2022; and
- native members of annual cluster `B_2023` in 2023.

Transported predictions do not add members. Thus each year's family membership comes solely from that year's independently fitted HDBSCAN cluster.

## 7. Frozen ranking

For a reciprocal pair, let native annual HDBSCAN persistence values be `P_2022` and `P_2023` from `cluster_persistence_`.

Rank recurrent families lexicographically by:

1. descending `min(P_2022, P_2023)` — worst-year native persistence;
2. descending `max(P_2022, P_2023)` — stronger-year persistence only as a tie breaker;
3. descending `min(n_2022, n_2023)` — worst-year native member count;
4. descending total member count;
5. ascending deterministic family ID computed from the exact two annual label/member identities.

The forward/backward majority fractions and prediction probabilities are reporting-only and cannot alter the rank.

No learned model, fusion, recurrent-EOM score, v31 score, comparator budget, diversity penalty, or truth-aware quantity enters ranking.

## 8. Prelabel freeze

Before shower truth is evaluated, persist and hash-freeze:

- exact input event IDs/hashes for both years;
- both annual GEO6 arrays/hashes;
- exact native HDBSCAN labels for both years;
- exact annual cluster-persistence arrays;
- both annual condensed-tree hashes;
- complete 2022->2023 predicted-label vector and complete 2023->2022 predicted-label vector;
- prediction probabilities for provenance only;
- every annual cluster's strict-majority mapping or null status;
- every reciprocal pair;
- exact family memberships;
- complete deterministic family ranking;
- method/source/runtime hashes.

Only after that immutable prelabel payload exists may the sealed target-excluded GMN shower truth object be evaluated.

## 9. Binding GMN evaluation

Use exactly the promoted recurrent-EOM target-excluded GMN 2022+2023 truth convention and evaluator:

- exact 315,024 accessible 2022 events;
- exact 423,658 accessible 2023 events;
- eligible known shower = at least 4 labeled events in evaluated year;
- qualified match = dominant shower precision >= 0.5 and overlap >= 4;
- evaluate each year by restricting pooled family members to that year without changing the pooled rank;
- report recovered known showers @25/@50/@100/@500, full-catalogue qualified matches, top-100 dominant precision, MRR, and median top-500 fragmentation.

The workflow must reproduce the exact promoted recurrent-EOM parent result before accepting the successor comparison.

## 10. Frozen promotion gate versus recurrent-EOM

The first technically valid GMN outcome is binding.

Reciprocal-transfer HDBSCAN v1 passes only if all of the following hold versus exact promoted recurrent-EOM in the same evaluation semantics:

1. recovered@100 is strictly higher in at least one year and not lower in the other;
2. recovered@50 is not lower in either year;
3. top-100 dominant precision is not lower in either year;
4. MRR is not lower in either year;
5. median top-500 fragmentation is not higher in either year;
6. at least one reciprocal family exists and the successor catalogue is not identical to recurrent-EOM, proving the mechanism is active.

Recovered@25, recovered@500, full-catalogue qualified matches, transport majority fractions, and prediction probabilities are reporting-only.

PASS token:

`PASS_RECIPROCAL_TRANSFER_HDBSCAN_V1_GMN_DEVELOPMENT`

FAIL token:

`FAIL_RECIPROCAL_TRANSFER_HDBSCAN_V1_GMN_DEVELOPMENT`

A FAIL permanently rejects this exact reciprocal-transfer v1. No `>=0.5` versus `>0.5` change, prediction-probability cutoff, centroid fallback, orphan matching, alternate annual HDBSCAN parameters, EOM/leaf switch, rank combiner, or other result-informed rescue is authorized.

A PASS authorizes only a separately frozen exposed SonotaCo parent-superiority protocol. It does not authorize protected target access or pristine AMOS execution.

## 11. Novelty boundary

HDBSCAN is explicit prior art and must be cited. HDBSCAN's standard out-of-sample prediction operator is also prior art. The potential contribution is their repeated-observation composition: independent annual density hierarchies plus strict-majority **bidirectional** cross-model transport to define recurring physical families, with no fitted cross-year distance threshold.

No claim of being the first general temporal clustering method is authorized. Any eventual novelty claim must be limited to the exact repeated-observation HDBSCAN recurrence construction and supported by a dedicated literature review.
