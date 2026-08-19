# OrbitTrace protected-prefix fusion CV v1 — frozen protocol

## Status

**FROZEN BEFORE THIS ARCHITECTURE'S FIRST CROSS-YEAR HELD-OUT GMN RESULT.**

This successor is motivated by two already-binding target-excluded GMN findings. First, recurrent-EOM residual error is dominated by ranking/selection and missing candidate structure rather than membership cleanup. Second, the sealed support-cut × annual-density-bifiltration candidate architecture recovered substantially more known showers than recurrent-EOM at equal budget and improved dominant precision without increasing fragmentation, but failed promotion because its all-replacement ranking reduced mean reciprocal rank (MRR). The scientific question here is therefore whether recurrent-EOM's early ordering can be structurally protected while support-cut candidates supply additional coverage.

This is a **catalogue fusion architecture**, not a new scalar recurrence score and not a post-result reranker. All source candidate memberships and source orders are inherited from the immutable zero-label prelabel produced before the earlier GMN truth endpoint.

## 1. Immutable source catalogue

Use only `SUPPORT_CUT_BIFILTRATION_INTERNAL_MASS_V1_PRELABEL.json` with SHA-256

`7b1ddfcd32cd0b52321e3b3dfc614a88dd9b973f947c1d4d0de74fddf26b59cd`.

For each deterministic `(denominator, bucket)` panel it contains:

- the recurrent-EOM catalogue in its already-frozen recurrent-stability order;
- the pairwise-disjoint support-cut catalogue in its already-frozen internal two-density persistence-mass order;
- the exact annual event-ID universes for 2022 and 2023;
- the exact equal recurrent-EOM candidate budget `K`.

No candidate membership, source score, source order, event universe, or budget may be reconstructed, altered, enriched, or selected from this experiment's truth result.

Exact budgets are:

- `d=128`, buckets 0..3: `K = 29, 35, 38, 33`;
- `d=1024`, buckets 0..3: `K = 8, 5, 6, 9`.

## 2. Protected-prefix fusion

The only configurable quantity is the recurrent-EOM protected prefix fraction, restricted *before truth* to the five quarters

`q ∈ {0, 1/4, 1/2, 3/4, 1}`.

For a panel with budget `K`, the protected recurrent prefix length is

`p(q,K) = 0` for `q=0`, otherwise `ceil(q K)`.

Construct the fused list deterministically:

1. copy the first `p(q,K)` recurrent-EOM candidates unchanged and in unchanged order;
2. scan the complete sealed support-cut list in its frozen internal-mass order and append a candidate only when its event membership is disjoint from every already-selected candidate, stopping at `K` total entries;
3. if fewer than `K` entries have been selected, scan the untouched recurrent-EOM tail in original order and append candidates whose memberships are disjoint from the current list until `K` is reached.

All output candidates must be pairwise event-disjoint and the list must contain exactly `K` entries. `q=1` must reproduce the recurrent-EOM equal-budget list exactly, both in memberships and evaluation metrics. Failure of either invariant is a technical failure, not a scientific result.

There is no overlap threshold, soft penalty, score blend, lineage quota, route-specific exception, bucket-specific tuning, candidate relabeling, or truth-dependent membership operation.

## 3. Cross-year configuration selection

This endpoint uses target-excluded GMN 2022/2023 as a two-fold cross-year development benchmark.

For each scale independently (`d=128` and `d=1024`):

- fold A uses **2023 only** to choose one shared `q` across all four buckets, then scores **2022 only**;
- fold B uses **2022 only** to choose one shared `q` across all four buckets, then scores **2023 only**.

The held-out year's labels may not influence configuration selection. The selected quarter is shared by all four buckets within that scale/fold; there is no per-bucket choice.

For each development year and candidate `q`, aggregate the unchanged inherited known-shower evaluator over the four buckets at that scale. A configuration is admissible only if, versus recurrent-EOM on the same development panels:

1. total qualified matches are not lower;
2. qualified matches are not lower in at least 3/4 buckets;
3. mean MRR is not lower;
4. mean top-100 dominant precision is not lower;
5. mean fragmentation is not higher.

Because `q=1` is exactly recurrent-EOM, at least one admissible configuration must exist.

Among admissible configurations choose lexicographically:

1. highest development qualified-match total;
2. highest number of bucketwise qualified non-regressions;
3. highest development mean MRR;
4. highest development mean top-100 dominant precision;
5. larger protected recurrent prefix.

No other objective, tolerance, tie-break, or parameter search is permitted.

## 4. Evaluation and promotion contract

Use the exact inherited recurrent-EOM known-shower evaluator and annual eligibility semantics. Only the selected opposite-year configuration is evaluated on each held-out year. Report the 16 held-out annual panels and aggregate the eight panels at each scale.

The successor is promoted on this GMN development endpoint only if **all ten** gates pass.

Fine `d=1024`:

1. held-out qualified total is strictly greater than recurrent-EOM;
2. held-out qualified recovery is nonlower in at least 6/8 panels;
3. held-out mean MRR is not lower;
4. held-out mean top-100 dominant precision is not lower;
5. held-out mean fragmentation is not higher.

Coarse `d=128`:

6. held-out qualified total is not lower;
7. held-out qualified recovery is nonlower in at least 6/8 panels;
8. held-out mean MRR is not lower;
9. held-out mean top-100 dominant precision is not lower;
10. held-out mean fragmentation is not higher.

A tie does not satisfy the fine strict-qualified-total gate. The first technically valid result is binding. A valid FAIL closes protected-prefix fusion CV v1. Do not change the quarter grid, prefix rounding, fusion order, disjointness rule, development admissibility, lexicographic objective, budgets, metrics, or gates after seeing the result.

## 5. Firewall and claim boundary

Only target-excluded GMN 2022/2023 development truth is authorized. The inclusive solar-longitude interval `[20°,55°]` remains excluded upstream.

Forbidden in this endpoint:

- OrbitTrace target information or target-region events;
- SonotaCo 2013/2014;
- ASFN/EFN event-level data;
- AMOS, MAARSY, or DMS;
- any pristine external endpoint;
- any post-result parameter search.

A PASS would establish a target-excluded GMN cross-year-held-out improvement over recurrent-EOM under this exact sparse-panel protocol. It would **not** establish universal state of the art, superiority to tuned HDBSCAN on the previously frozen symmetric SonotaCo benchmark, or external generalization. Any later SonotaCo or external characterization would require a separately frozen protocol and would preserve all existing negative results.
