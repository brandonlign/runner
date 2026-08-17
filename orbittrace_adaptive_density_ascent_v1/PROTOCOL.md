# OrbitTrace Adaptive Density Ascent v1 — frozen development protocol

## Scientific role

This is a separately named successor created after the fixed-scale TopoModal flagship lost narrowly to the exact published catalogue-HDBSCAN comparator on exposed SonotaCo 2013/2014, while two fundamentally different global-partition successors (Compact Mixture v1 and Reciprocal Rank Communities v1) failed decisively.

All predecessor outcomes remain binding. This method does not edit or rescue them.

SonotaCo 2013/2014 remains **EXPOSED DEVELOPMENT ONLY**. A pass here is development evidence only and must be followed by a separately frozen target-excluded GMN scale/generalization test.

## Motivation

The two failed global partitions indicate that forcing the sporadic background into a complete catalogue partition is structurally wrong for this task. Meteor streams should instead appear as local high-density modes embedded in a broad background.

Adaptive Density Ascent v1 therefore uses a nonparametric nearest-neighbor density estimate and a local density-ascent forest. Every reportable candidate is one basin of attraction of a local density mode. The architecture permits many small local basins rather than forcing a few global communities or assuming Gaussian component shapes.

Nearest-neighbor density estimation, density cluster trees, and mode-seeking are established statistical ideas. The tested OrbitTrace construction is the fixed meteor-physics embedding + sample-size-derived kNN density + local ascent basin definition + frozen density-peak salience order. This protocol does not claim that generic mode-seeking itself is new.

## Frozen input

Use only the exact HDBSCAN-compatible truth-free SonotaCo 2013 and 2014 annual row universes already frozen in the prior matched-literature benchmark.

Protected solar longitude `[20°,55°]` is excluded inclusively upstream.

Detector inputs are only:
- `id` for membership bookkeeping;
- `sol`;
- `sun_lon`;
- `ecl_lat`;
- `vg`.

No shower/truth field, orbit, uncertainty, station metadata, year-as-feature, HDBSCAN output, or target information enters candidate generation or ordering.

The identical algorithm is fit independently to each annual catalogue.

## Frozen physical embedding

For each event use

`[cos(sol)/h_sol, sin(sol)/h_sol, cos(lat)cos(lon)/h_rad, cos(lat)sin(lon)/h_rad, sin(lat)/h_rad, log(vg)/h_logv]`

with
- `h_sol = 2 sin(5°/2)`;
- `h_rad = 2 sin(4°/2)`;
- `h_logv = ln(1.1)`.

## Frozen local density

For annual sample size `n`, define

`k(n) = ceil(log2(n))`.

Compute each event's `k` nearest *other* events in Euclidean physical-embedding distance. Distance ties are resolved by ascending row index.

Let `r_k(i)` be the distance to event `i`'s k-th nearest neighbor. Since the embedding dimension is fixed at `d=6`, use the log kNN-density score

`log rho_i = -6 log r_k(i)`.

The omitted multiplicative constants are common to all events and cannot affect the ascent forest or ranking.

## Frozen density-ascent forest

For event `i`, inspect its k nearest neighbors in increasing `(distance,row_index)` order. Its parent is the first neighbor `j` satisfying:

- `log rho_j > log rho_i`, or
- exact density tie and `j < i`.

If no such neighbor exists, `i` is a local mode/root.

Following parent pointers to a root assigns every event to exactly one local basin. This local-parent rule is intentionally restricted to the same k-neighborhood used for density estimation; there is no second neighborhood scale or distance threshold.

A basin is reportable iff it contains at least 4 annual events.

## Frozen mode salience and candidate order

Let `R` be the set of local roots and let `rho_r` denote a root density.

For each root except the globally densest root, define `delta_r` as the Euclidean physical-embedding distance to the nearest root with strictly greater density (ties use lower root index as the higher-order root).

For the globally densest root, define `delta_r` as the maximum distance to any other root, following the standard density-peak convention that the top-density mode receives the catalogue-scale separation distance.

Define frozen log salience

`G_r = log rho_r + log delta_r`.

Rank reportable basins by descending `G_r`; exact ties are resolved only by SHA-256 of sorted member IDs.

No basin purity, truth, HDBSCAN overlap, recurrence, orbit, annual consistency, or post-result statistic changes this order.

## Frozen structural gates before truth

Before any v1 shower truth access, each annual candidate catalogue must satisfy:
- `k(n)` equals the frozen formula;
- more than one local root exists;
- reportable candidate capacity is at least the exact HDBSCAN family budget;
- no reportable basin contains more than 10% of the annual catalogue;
- all salience scores are finite;
- ranks are contiguous and deterministic.

These gates are label-free and exist only to reject technical/global-collapse pathologies.

## Frozen runtime

- Python 3.11;
- NumPy `2.3.5`;
- SciPy `1.17.0`;
- scikit-learn `1.8.0`.

## Frozen HDBSCAN comparison

Reuse byte-for-byte the exact published catalogue-HDBSCAN outputs previously frozen for SonotaCo 2013 and 2014.

For each year independently:
1. let `B` be the complete HDBSCAN family count for that year;
2. take the first `B` Adaptive Density Ascent candidates in the frozen order;
3. evaluate both catalogues on the identical row universe and identical frozen shower truth with the same Hungarian maximum-F1 evaluator used in the prior literature benchmark.

Eligible known showers remain those with at least 4 events in the exact annual row universe.

A year is a win only if:
- Adaptive Density Ascent macro-F1 is strictly greater than HDBSCAN macro-F1; and
- recovered showers with assigned F1 > 0.5 are at least the HDBSCAN count.

`PASS_ADAPTIVE_DENSITY_ASCENT_V1_HDBSCAN_DEVELOPMENT` requires wins in **both** 2013 and 2014. Any other technically valid result is `FAIL_ADAPTIVE_DENSITY_ASCENT_V1_HDBSCAN_DEVELOPMENT`.

## Firewall and closure

Scientific source, protocol, candidate catalogues/order, row hashes, exact HDBSCAN outputs, and evaluation rule must be hash-frozen before truth opens.

After the first technically valid v1 outcome, no k rule, density exponent, parent rule, support floor, salience formula, feature, metric, budget, or tie-break may be changed as a v1 rescue. Failure closes this exact family; success advances the exact frozen architecture to a separately preregistered target-excluded GMN test.

Protected `[20°,55°]`, OrbitTrace target information/events, MAARSY, and DMS remain inaccessible.
