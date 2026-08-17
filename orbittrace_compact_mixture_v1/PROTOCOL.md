# OrbitTrace Compact Mixture v1 — frozen development protocol

## Scientific role

This is a separately named successor architecture created after the fixed-scale TopoModal flagship failed to beat the exact published catalogue-HDBSCAN comparator on exposed SonotaCo 2013/2014.

It does **not** edit, tune, rescue, or reinterpret TopoModal. All prior positive and negative results remain binding for the methods that produced them.

SonotaCo 2013/2014 is **EXPOSED DEVELOPMENT ONLY**. A pass here would authorize a separately frozen target-excluded GMN scale/generalization evaluation; it would not constitute external validation.

## Motivation

The exposed benchmark indicates a specific structural tradeoff: fixed-scale TopoModal is substantially stronger under sparse-sample thinning, but catalogue-scale HDBSCAN retains a modest advantage on SonotaCo. Rather than tune a TopoModal radius, support floor, hierarchy, ranking, or HDBSCAN parameter, v1 tests a fundamentally different representation:

**model the entire catalogue as a soft finite mixture in fixed physical meteor geometry, then report intrinsically compact mixture components.**

The architecture is intentionally non-hierarchical and does not use DBSCAN/HDBSCAN connectivity, mutual reachability, persistence, EOM, ToMATo, local shells, D-criteria, shower labels, orbital elements, station metadata, or result-informed ranking.

## Frozen input

Use only the exact HDBSCAN-compatible, truth-free SonotaCo 2013 and 2014 row universes already frozen by the matched-literature benchmark.

The protected solar-longitude interval `[20°,55°]` is excluded inclusively before v1 receives any row.

Only these fields enter the detector:

- event ID (membership bookkeeping only);
- solar longitude `sol`;
- Sun-centered ecliptic radiant longitude `sun_lon`;
- ecliptic radiant latitude `ecl_lat`;
- geocentric speed `vg`.

No `iau`, shower/truth field, orbit, uncertainty, station, year indicator, or target information enters fitting or ranking.

## Frozen physical embedding

For each event use the same fixed physical geometry introduced by the TopoModal flagship:

`[cos(sol)/h_sol, sin(sol)/h_sol, cos(lat)cos(lon)/h_rad, cos(lat)sin(lon)/h_rad, sin(lat)/h_rad, log(vg)/h_logv]`

with

- `h_sol = 2 sin(5°/2)`;
- `h_rad = 2 sin(4°/2)`;
- `h_logv = ln(1.1)`.

Angles are converted to radians before trigonometric evaluation.

## Label-free complexity audit and fixed truncation

Before any v1 truth access, a deterministic diagonal-Gaussian BIC audit was run on the exact pooled truth-free HDBSCAN-compatible rows. BIC decreased monotonically over the audited truncations `K={8,16,32,64,96,128,160}` and remained decreasing at 160.

Therefore v1 fixes `K=160` as a **high-resolution truncation**, not as a claimed BIC optimum. No K beyond 160 is inspected before the first v1 truth outcome and no K may be changed after that outcome.

## Frozen mixture fit

Fit one pooled 2013+2014 `sklearn.mixture.GaussianMixture` with:

- `n_components=160`;
- `covariance_type="diag"`;
- `reg_covar=1e-4`;
- `tol=1e-3`;
- `max_iter=500`;
- `n_init=1`;
- `init_params="kmeans"`;
- `random_state=20260816`.

Runtime is frozen to NumPy `2.3.5`, SciPy `1.17.0`, scikit-learn `1.8.0`.

The fit must converge or v1 is technically invalid.

## Frozen candidate construction and order

Each event is assigned to its maximum-posterior component (hard MAP assignment). No posterior threshold is applied.

A component becomes a candidate iff its pooled MAP membership has at least 4 events.

For diagonal covariance `diag(v_k)`, define the component's intrinsic weighted peak-density score up to the common Gaussian constant as

`P_k = pi_k / sqrt(prod(v_k))`

where `pi_k` is the fitted mixture weight.

Candidates are ordered by descending `P_k`, with ascending fitted component index as the only deterministic tie-breaker. No annual support, recurrence, truth, HDBSCAN overlap, orbital coherence, external metadata, or post-fit quality score changes this order.

## Frozen HDBSCAN comparison

The exact previously frozen published catalogue-HDBSCAN outputs are reused byte-for-byte. They are not rerun or retuned.

For each year independently:

1. let `B` equal the complete published-HDBSCAN family count for that year;
2. take the first `B` Compact Mixture candidates in the frozen pooled order;
3. intersect those pooled candidate memberships with that year's exact row universe;
4. use the exact same frozen shower-truth mapping and Hungarian maximum-F1 evaluation as the prior matched-literature benchmark.

Eligible known showers are unchanged: at least 4 events in that year's exact row universe.

A year is a Compact Mixture win only if both:
- Compact Mixture macro-F1 is strictly greater than published HDBSCAN macro-F1;
- Compact Mixture recovered showers with assigned F1 > 0.5 is at least the HDBSCAN count.

`PASS_COMPACT_MIXTURE_V1_HDBSCAN_DEVELOPMENT` requires wins in **both 2013 and 2014**.

Anything else is `FAIL_COMPACT_MIXTURE_V1_HDBSCAN_DEVELOPMENT`.

## Scientific firewall and closure

The complete Compact Mixture source, configuration, candidate catalogue, candidate order, exact row hashes, and reused HDBSCAN outputs must be hash-frozen before SonotaCo shower truth is opened.

After the first technically valid truth outcome:

- no `K`, covariance type, regularization, initialization, support floor, posterior rule, score, ranking, feature, metric, budget, or tie-break may be changed as a v1 rescue;
- failure closes this exact v1 family;
- success advances the exact frozen v1 method to a separately preregistered target-excluded GMN scale/generalization test.

At all times:
- protected `[20°,55°]` target-region events remain inaccessible;
- OrbitTrace target information remains inaccessible;
- MAARSY and DMS remain scientifically inaccessible.
