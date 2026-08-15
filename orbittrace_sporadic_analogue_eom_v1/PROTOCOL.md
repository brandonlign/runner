# OrbitTrace sporadic-analogue EOM v1 — frozen protocol

## Goal

Test one structural successor designed specifically for cross-survey generalization: make HDBSCAN hierarchy selection depend on local shower density **relative to the survey's own seasonally matched sporadic background**, rather than raw density alone.

This is not a post-hoc candidate reranker and not a rescue of the failed log-density, rate-balance, year-shift, wavelet, cross-year-core, or local-kNN successors.

## Scientific motivation fixed before outcome

Meteor-shower false-positive work shows that the relevant difficulty is the strongly nonuniform sporadic background, and that a useful local control can be built from time-shifted shower analogues that preserve Sun-centred radiant and geocentric speed while moving solar longitude away from the candidate season. Moorhead (2015) fixes analogue offsets from +60 deg through +300 deg in 10 deg steps. Recent multi-survey work likewise uses explicit survey-specific sporadic nulls before density clustering.

The method below turns that prior idea into a label-free HDBSCAN node objective.

## Frozen parent

Exact density-synchronous recurrent-EOM HDBSCAN v1 from PR #1263, head `182f07ade6bb5d4be2c80b88df9216bb2d6eee2d`.

Parent target-excluded GMN 2022/2023 metrics:

- 2022 recovered@50 = 45, recovered@100 = 89, top100 precision = 0.7873334042799703, MRR = 0.022505373166085363, fragmentation median = 1.0;
- 2023 recovered@50 = 46, recovered@100 = 90, top100 precision = 0.7898245986099988, MRR = 0.02203028490649908, fragmentation median = 1.0;
- total recovered@100 = 179;
- candidate count = 2,094.

## Frozen representation and hierarchy

Unchanged parent GEO6:

`[cos(sol), sin(sol), sin(lon_sce) cos(beta), cos(lon_sce) cos(beta), sin(beta), vg/72]`

Unchanged HDBSCAN:

- min_cluster_size = 10
- min_samples = 10
- Euclidean metric
- EOM extraction
- epsilon = 0
- one pooled 2022+2023 hierarchy

The successor must use the exact same pooled hierarchy. It may change only the node quality supplied to EOM/FOSC extraction.

## Frozen sporadic-analogue local contrast

For each observing year separately:

1. Build a `cKDTree` on that year's accessible target-excluded GEO6 events.
2. Let `r_actual(i)` be the distance from event `i` to its 10th *other* same-year neighbour. `k=10` is inherited exactly from HDBSCAN `min_samples`; there is no new k search.
3. Construct the 25 published seasonal analogue offsets:

   `delta = 60, 70, ..., 300 deg`.

   For each event and offset, set `sol'=(sol+delta) mod 360`, preserve Sun-centred radiant and `vg`, and rebuild GEO6.
4. If an analogue solar longitude lies inside the protected inclusive `[20,55] deg` region, that analogue is discarded before any query. No protected event is loaded into the tree.
5. Query the same-year tree for the 10th-neighbour radius at every remaining analogue location. Define

   `r_bg(i) = median_delta r_analogue(i,delta)`.

6. Define dimensionless local density contrast

   `c(i) = r_bg(i) / r_actual(i)`.

7. Convert it to the fixed bounded symmetric weight

   `w(i) = 2*c(i)/(1+c(i))`.

   Thus `c=1 -> w=1`, `c->0 -> w->0`, `c->infinity -> w->2`, and `w(c)+w(1/c)=2`. No clipping, fit, learned parameter, percentile calibration, or label information is permitted.

## Frozen successor node objective

On the unchanged condensed hierarchy, replace each event's unit alive mass by `w(i)`.

For each cluster node and each observing year, sweep the exact direct-child departure lambdas as in density-synchronous recurrent-EOM. At each lambda interval compute the currently alive analogue-weighted mass, normalized by that year's total analogue weight. The successor node quality is

`S_analogue(C) = integral min(W_2022^C(lambda), W_2023^C(lambda)) d lambda`.

The current champion remains the direct comparison parent and is reconstructed from the same hierarchy before the successor.

## Pretruth freeze

Before any known-shower truth is opened, persist:

- event counts and year counts;
- pooled tree SHA-256;
- all per-event weights in pooled event order (or their exact array SHA-256 plus summary if artifact size requires);
- parent and successor selected nodes;
- complete successor memberships and rank order;
- candidate counts;
- exact method/source hashes;
- all firewall flags.

Known-shower labels may only be used after this pretruth object is written and hashed.

## Hard GMN success gate

This method is intended to produce a **meaningful** improvement, not another 89->90 result.

It passes only if all are true:

1. mechanism is active;
2. total recovered@100 across 2022+2023 is at least `184`, i.e. gain >= +5 over 179;
3. recovered@50 is not lower in either year;
4. recovered@100 is not lower in either year;
5. top-100 dominant precision is not lower in either year;
6. MRR is not lower in either year;
7. median top-500 fragmentation is not higher in either year.

If it fails, the exact method is permanently closed. No alternate analogue spacing, k, aggregation statistic, weight transform, cap, blend, threshold, or reranking rescue is authorized from that outcome.

If and only if it passes, it may proceed to a separately frozen SonotaCo transfer benchmark before any AMOS access.

## Firewalls

- Protected OrbitTrace solar-longitude region `[20,55] deg` remains inaccessible inclusively.
- OrbitTrace target information/events: inaccessible.
- SonotaCo 2013/2014: inaccessible during GMN development.
- ASFN and EFN: not used to design or score this successor.
- AMOS: inaccessible.
- MAARSY and DMS: inaccessible.
- No post-result parameter search or rescue.
