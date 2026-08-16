# OrbitTrace station-support-weighted topomodal scale diagnostic v1

## Status

**FROZEN BEFORE ANY PROJECT `Num (stat)` VALUE OR AVAILABILITY OUTCOME IS READ.**

Execute only if `orbittrace_topomodal_numstat_availability_v1` returns exactly `PASS_TOPOMODAL_NUMSTAT_AVAILABILITY_V1`.

This stage is zero-label structural only. It cannot open shower truth.

## 1. Sole scientific change from #1284

Reuse exact PR #1284:

- target-excluded GMN 2022+2023 rows;
- exact physical embedding (5° solar / 4° radiant / 10% log-speed scales);
- exact symmetric Euclidean radius-1 graph including self in local neighborhoods;
- GUDHI 3.12.0 `Tomato(graph_type='manual', density_type='manual')`;
- complete leaf/internal/root hierarchy;
- exact membership deduplication;
- minimum reportable support 4;
- exact d128/d1024 buckets 0..3;
- exact recurrent-EOM comparator;
- exact #1284 cross-scale Jaccard metric and five structural gates.

Change **only** the manual density field.

For each retained event `j`, define the fixed observational support weight

`w_j = Num(stat)_j`.

For every event `i` with original #1284 radius-1 neighborhood `N1(i)` including self, define

`rho_station(i) = sum_{j in N1(i)} w_j / sum_{k in subset} w_k`.

Thus density is local observed-station support mass as a fraction of total station support in that subset. There is no threshold, cap, logarithm, exponent, clipping, centering, learned coefficient, or mixture with ordinary radius-count density.

The graph itself is unchanged from #1284. Station identities/geography never enter the method.

## 2. Missingness rule

No imputation is allowed.

The predecessor availability PASS guarantees >=95% usable `num_stat`, but the scientific subset may not silently delete events. Therefore this successor is executable only if **all events in all eight exact frozen sparse subsets have usable integer `num_stat>=2`** at execution time.

If any frozen subset event lacks usable `num_stat`, stop with `BLOCKED_STATION_WEIGHTED_TOPOMODAL_INCOMPLETE_EVENT_WEIGHTS` before fitting ToMATo. This is not permission to impute, drop events, or alter the graph.

## 3. Firewall

Protected solar longitude `[20.0,55.0]` remains excluded inclusively before station weight enters the density field.

Forbidden:

- shower labels/truth;
- station identity or station geography;
- participating-station strings;
- orbit elements, fit error, uncertainty, or other quality variables;
- SonotaCo, ASFN/EFN, AMOS, MAARSY, DMS scientific access;
- any result-informed station-count transform or fusion.

## 4. Structural evaluation

Reuse #1284 exactly. For each bucket, compare the successor fine-subset memberships to restricted coarse-subset memberships using best Jaccard, and compare against exact recurrent-EOM on the same subsets.

Return `SUPPORTS_STATION_WEIGHTED_TOPOMODAL_CROSS_SCALE_COHERENCE` iff all five hold:

1. successor nonempty in all eight subsets;
2. successor fine candidate count >= recurrent-EOM in all four fine subsets;
3. pooled fine→coarse candidate-unweighted mean best Jaccard > recurrent-EOM;
4. median of four bucket fine→coarse mean-best-Jaccards > recurrent-EOM;
5. strict bucket-level wins over recurrent-EOM in at least 3/4 buckets.

Otherwise return `REFUTES_STATION_WEIGHTED_TOPOMODAL_CROSS_SCALE_COHERENCE`.

Also report #1284 predecessor controls descriptively only: pooled `0.8067062037`, median `0.8129624258`, 4/4 wins.

## 5. Consequence

A structural PASS authorizes one separately frozen truth-bearing recovery/ranking successor, whose complete order and gates must be fixed before shower truth. A structural FAIL permanently closes the exact station-weighted density architecture.

No rescue via threshold/cap/log/sqrt/exponent, station-count ECDF/rank, graph weighting, radius change, physical-scale change, ordinary-density blend, uncertainty fusion, support change, alternative subset, or gate relaxation is authorized from the outcome.