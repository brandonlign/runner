# OrbitTrace window-owned persistence recovery/ranking v1

## Purpose

This is the first truth-evaluated successor authorized by the zero-label structural PASS in PR #1283. It asks whether the exact window-owned local-persistence family architecture can beat the selected recurrent-EOM HDBSCAN method on the unchanged target-excluded GMN 2022+2023 development universe.

No structural parameter from #1283 may change. This stage adds only one preregistered label-free ranking to the exact family memberships.

## Firewall and corpus

- GMN **2022+2023 only**.
- Protected solar longitude `[20°,55°]` remains excluded before labels, hierarchy construction, memberships, ranks, and evaluation.
- No OrbitTrace target information or target-region event may be accessed.
- No SonotaCo, ASFN/EFN event-level data, AMOS, MAARSY, or DMS may be accessed scientifically.
- Labels remain sealed until both the exact recurrent-EOM comparator and the complete successor candidate set, membership list, ranking fields, and final order are written to a prelabel artifact.

## Exact inherited candidate architecture

The successor must reproduce PR #1283 exactly:

- GEO6 representation unchanged:
  `(cos(sol), sin(sol), sin(lon)*cos(lat), cos(lon)*cos(lat), sin(lat), vg/72)`;
- Persistable pinned to `LuisScoccola/persistable@7eb75b2e8d2fe5a18e49248aa7d1c97f829415be`;
- `Persistable(X_window, n_neighbors="auto", n_jobs=1)`, uniform measure, Euclidean metric;
- fixed 72 solar-longitude window centers `0°,5°,...,355°`;
- window membership iff circular solar-longitude distance to the center is `<=5°` (10° width, 5° step);
- exact package `_find_end()` + `compute_defaults()` midpoint slice;
- one midpoint `lambda_linkage` hierarchy per window;
- positive-persistence bar count `B`;
- all conservative flattenings `g=2..min(15,B)`, `keep_low_persistence_clusters=False`;
- exact-membership union of non-noise memberships with at least 4 events;
- deterministic owner = nearest fixed window center to candidate circular-mean solar longitude, tie to numerically smaller center;
- retain only candidates generated in their owner window;
- exact duplicate memberships deduplicated after ownership;
- no cross-window linking, transitive merge, centroid radius, Jaccard threshold, persistence threshold, preferred g, or alternate neighbor policy.

The target-excluded full pooled event count must be exactly **738,682**.

## Frozen ranking attributes

For each exact owned candidate membership, while generating the inherited `g=2..min(15,B)` ladder, record without changing membership:

- `g_first`: smallest requested cluster count `g` at which that exact membership appears;
- `g_last`: largest `g` at which that exact membership appears;
- `g_span`: number of distinct `g` values at which that exact membership appears;
- `member_count_2022` and `member_count_2023` from event-year metadata only;
- `member_count_total`;
- `both_years_present = (member_count_2022 > 0 and member_count_2023 > 0)`;
- owner window center;
- family ID = SHA-256 hash of sorted member IDs.

If an exact membership is encountered more than once inside its owner window, these fields are the union over those identical appearances. No approximate-membership matching is permitted.

## Sole frozen ranking

Sort candidates lexicographically by:

1. `both_years_present` descending (`True` before `False`);
2. `g_first` ascending;
3. `g_span` descending;
4. `min(member_count_2022, member_count_2023)` descending;
5. `member_count_total` descending;
6. `family_id` ascending.

This is the only successor order. There is no score blend, fitted weight, local-exposure normalization, alternative recurrence statistic, ranking grid, threshold grid, post-result reranking, or rescue queue.

Scientific rationale fixed before truth: cross-year presence is independent support without requiring equal annual counts; `g_first` is the candidate's relative persistence order inside its local hierarchy; `g_span` measures exact-membership stability across the already-frozen ladder; annual/total support are deterministic tie-breakers rather than fitted weights.

## Exact recurrent-EOM comparator

Reconstruct the selected parent from `orbittrace_recurrent_eom_hdbscan_v1/run_development.py` exactly:

- GEO6;
- HDBSCAN min_cluster_size=10, min_samples=10;
- Euclidean;
- standard hierarchy;
- annual alive-mass/EOM normalized by total accessible event count per year;
- recurrent node quality `min(E_2022_norm, E_2023_norm)`;
- FOSC/EOM extraction;
- frozen recurrent ranking.

The comparator must reproduce the authoritative recurrent-EOM development metrics before the successor may be interpreted.

Expected recurrent-EOM metrics:

### 2022
- @25: `22`
- @50: `45`
- @100: `89`
- @500: `193`
- top-100 dominant precision: `0.7856486013`
- MRR: `0.0224982696`
- qualified matches: `236`
- fragmentation median top500: `1.0`

### 2023
- @25: `23`
- @50: `46`
- @100: `89`
- @500: `192`
- top-100 dominant precision: `0.7867680237`
- MRR: `0.0220239289`
- qualified matches: `244`
- fragmentation median top500: `1.0`

Tiny floating differences are permitted only at `1e-9` absolute tolerance for floating metrics; integer metrics must match exactly.

## Prelabel barrier

Before the hidden label mapping is read by the evaluator, write an immutable prelabel JSON containing:

- exact input counts by year;
- exact candidate-generation configuration;
- every successor family ID, owner center, member IDs, and all ranking attributes;
- the exact final successor rank order;
- exact recurrent-EOM family membership/order;
- candidate counts;
- target/firewall assertions.

Record and later embed the SHA-256 of this prelabel artifact in the scientific result.

## Evaluation

Use the exact recurrent-EOM evaluator definitions:

- per-year eligible label: at least 4 labeled accessible events in that year;
- candidate evaluated using only that year's members;
- positive qualified family: precision >=0.5 and overlap >=4 for its best eligible label;
- report recovered @25/@50/@100/@500, top-100 dominant precision, MRR over represented labels, qualified matches, and median top-500 fragmentation.

No metric definition changes.

## Frozen promotion gates

The successor passes only if **all** gates hold separately in both 2022 and 2023:

1. `recovered_at_25 >= recurrent_parent`;
2. `recovered_at_50 >= recurrent_parent`;
3. `recovered_at_100 >= recurrent_parent`;
4. `recovered_at_500 >= recurrent_parent`;
5. `top100_dominant_precision >= recurrent_parent`;
6. `mrr >= recurrent_parent`;
7. `qualified_matches >= recurrent_parent`;
8. `fragmentation_median_top500 <= recurrent_parent`.

Additionally:

9. `recovered_at_100` must be **strictly greater** than recurrent-EOM in at least one of the two years;
10. at least 100 successor candidates must exist so every top-100 metric is defined without padding.

A scientific FAIL closes this exact inherited candidate architecture + lexicographic ranking. No same-result rescue may change ranking priority, add/remove attributes, weight attributes, filter candidates, alter window geometry, change persistence ladder range, use exposure normalization, add local background scoring, change representation, or relax gates.

A PASS authorizes only a separately frozen exposed SonotaCo 2013/2014 comparison or another governance-approved transfer stage; it does not authorize protected target access.