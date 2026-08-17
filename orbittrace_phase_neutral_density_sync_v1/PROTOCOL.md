# Phase-neutral density-synchronous recurrent-EOM v1

## Status

Frozen before the first paired GMN method outcome.

This is new exposed-development work authorized after the previous method-selection freeze was explicitly reopened. It must not be represented as preregistered before earlier GMN/SonotaCo outcomes.

## Why this lane exists

An exposed SonotaCo condensed-tree oracle diagnostic found that 57 of 58 recurrent-EOM candidate-generation misses had no node in the fixed GEO6 HDBSCAN hierarchy with F1 > 0.5. Only 1/58 was recoverable by changing extraction. That diagnostic therefore points to hierarchy/geometry, rather than EOM pruning, as the dominant missing-structure bottleneck.

The scientific hypothesis tested here is narrow: after the protected solar-longitude window has already been removed, using solar longitude as two ordinary Euclidean clustering dimensions may split or dilute radiant-speed structures whose observable radiant/speed locus persists across a wider activity interval. The successor therefore removes solar phase from the clustering distance while preserving every other density and recurrence choice.

This hypothesis was chosen using exposed development diagnostics. No SonotaCo truth is used to choose a phase weight, speed weight, HDBSCAN setting, threshold, route-specific rule, or rescue variant.

## Exact methods

Both methods use the same immutable current GMN 2022+2023 label-free snapshot produced under `SNAPSHOT_PROTOCOL.md`.

### Paired champion: GEO6 density-sync

Representation:

`[cos(sol), sin(sol), sin(lon)*cos(lat), cos(lon)*cos(lat), sin(lat), vg/72]`

HDBSCAN:

- `min_cluster_size=10`
- `min_samples=10`
- Euclidean metric
- `cluster_selection_method='eom'`
- `cluster_selection_epsilon=0`
- `allow_single_cluster=False`

Node objective and extraction are the exact #1263 density-synchronous recurrent-EOM definition:

`S_sync(C) = integral min(A_2022^C(lambda), A_2023^C(lambda)) d lambda`

where each annual alive-mass curve is normalized by that year's accessible event count.

### Sole successor: GEO4 phase-neutral density-sync

The only scientific change is the clustering representation:

`[sin(lon)*cos(lat), cos(lon)*cos(lat), sin(lat), vg/72]`

Solar longitude remains present in the event record only so the inclusive protected `[20°,55°]` exclusion can be verified. It does not enter the successor distance matrix.

HDBSCAN settings, density-synchronous objective, FOSC/EOM extraction, candidate ranking, truth evaluator and promotion gates are unchanged.

## Pretruth boundary

Before the sealed-truth artifact is available, the scientific workflow must fit both complete hierarchies and persist for both methods:

- condensed-tree SHA-256;
- selected node IDs;
- all selected family memberships;
- candidate counts;
- complete ordered membership hashes;
- ordinary and density-synchronous node quality values required for audit;
- full candidate ordering.

The pretruth payload must prove that both methods use identical event IDs and year assignments and that all events lie outside `[20°,55°]`.

## Paired GMN promotion gate

The GEO4 successor is promoted only if all conditions hold against the GEO6 density-sync champion on this same snapshot:

For **each** of 2022 and 2023:

- recovered@50 is not lower;
- recovered@100 is not lower;
- top-100 dominant precision is not lower;
- MRR is not lower;
- median top-500 fragmentation is not higher.

Additionally:

- the mechanism must be active (hierarchy/membership/order differs); and
- recovered@100 must improve strictly in at least one year.

Recovered@25, recovered@500 and total qualified matches are reporting-only unless already included above.

This is a champion-based paired gate on a new exposed GMN snapshot. Historical #1263 metrics are contextual evidence only and are not numerically pooled with this snapshot.

## Closed rescue space

After the first technically valid paired GMN endpoint, the following are forbidden as result-informed rescues of this version:

- partial solar-phase weights;
- one phase coordinate instead of two;
- phase/radiant/speed rescaling;
- per-season, per-month or per-year phase handling;
- HDBSCAN parameter changes;
- GEO4/GEO6 candidate union or rank fusion;
- density-sync objective changes;
- route- or shower-specific rules;
- changing the promotion gate.

If GEO4 fails, exact phase-neutral density-sync v1 closes.

## Dormant exposed SonotaCo contingency

A separate `SONOTACO_PROTOCOL.md` must be frozen before the GMN result. It may execute only if the paired GMN gate passes. SonotaCo remains exposed development/validation, not external validation.

## Firewall

Protected OrbitTrace `[20°,55°]`, OrbitTrace target information/events, AMOS, MAARSY and DMS remain inaccessible. No pristine external dataset is authorized by this experiment.