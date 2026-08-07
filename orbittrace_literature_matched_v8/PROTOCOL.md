# OrbitTrace v8 matched literature benchmark — preregistered protocol

## Scope

This branch is **comparison-only**. It does not alter the promoted OrbitTrace v8 detector, develop a successor, or authorize the final OrbitTrace target reveal.

The scientific question is narrower: how does the already-frozen v8 pooled-year-centroid multiplicity method compare with the strongest faithfully implemented published meteor-stream methods when they are evaluated on the same survey years and the same blinded label universe?

## Frozen OrbitTrace method

The comparator under test is the exact promoted v8 source at commit `c9d6c44704013ba0c9430100e98a29a56b453304`:

- exact passed-v6 label-free candidate, quartet, component, and connected recurrent-family construction;
- family-link radius `1.5`;
- minimum component support `4` events and `2` quartets;
- exact 128-event local episodes;
- exact multi-anchor v3 and Brown scores;
- multiplicity `M=(v3/Brown)^2`;
- exact pooled same-year centroid repair: circular mean solar longitude and Sun-centered longitude, median ecliptic latitude and geocentric speed;
- multiplicity ranking by worst-year multiplicity, then geometric-mean multiplicity, then stable family ID.

No v8 threshold, radius, cap, weight, pooling rule, episode size, score, rank rule, or proposal rule may change in response to a competitor result.

## Benchmark panel

Primary matched-survey panel: **SonotaCo 2023 and SonotaCo 2025**.

Reasons fixed before execution:

1. Both years already have integrity-checked SonotaCo parsers and immutable archive provenance in this repository.
2. The faithful catalogue HDBSCAN transfer has already been frozen on these same two years.
3. The full 1,000-clone Sugar uncertainty pipeline has already been frozen on these same two years.
4. This is a benchmark panel, not a fresh prospective validation panel; its prior use is therefore reported rather than hidden.

The solar-longitude interval **20°–55° is excluded before shower-label access**. No event, member, coordinate, identity, score, or label from that excluded interval may be inspected by this benchmark.

No OrbitTrace coordinate, member, identity, target family, target-region event, or prior target recovery result may be accessed.

## Published comparators

### 1. Full Sugar et al. uncertainty pipeline — primary published comparator

Use the already-frozen results from:

- SonotaCo 2025 run `31075178517`, artifact `8957263372`;
- SonotaCo 2023 run `31076789635`, artifact `8957940764`.

The scientific configuration is unchanged: published six-dimensional Sun-centered GEO vector, DBSCAN `min_samples=5`, 2025-frozen epsilon `0.028705145052265017`, 1,000 uncertainty-clone catalogues, 50% overlap graph, retention at 100/1000 recurrences, strong at 500/1000, and the frozen deterministic merge interpretation. The retained master clusters are the primary Sugar output.

This is a faithful published-stage **survey transfer**, not an exact ASGARD covariance/software reproduction, because SonotaCo supplies marginal uncertainties.

### 2. Peña-Asensio & Ferrari catalogue HDBSCAN — primary published comparator

Use the already-frozen results from:

- SonotaCo 2025 run `31071589912`, artifact `8955917326`;
- SonotaCo 2023 run `31076062060`, artifact `8957554613`.

The scientific configuration is unchanged: published unstandardized GEO six-vector, `hdbscan==0.8.44`, `min_cluster_size=100`, package-default `min_samples`, Euclidean distance, and `eom` selection. The all-shower coverage audit is the relevant sparse-regime diagnostic because the paper-faithful primary analysis intentionally excludes reference showers below 100 annual members.

### 3. Southworth–Hawkins D_SH

The repository's exact Southworth–Hawkins implementation and Rudawska-style single-link episode comparator are retained as **targeted/episode recognition comparators**. They are not promoted to a catalogue-discovery comparator here because the published/implemented formulation is not a like-for-like ranked recurrent catalogue search and a naive all-pairs catalogue implementation would introduce a new O(N^2) discovery algorithm not specified by the cited method.

Therefore D_SH may inform where classical orbital association works, but it cannot be used either to prove or disprove v8 state-of-the-art catalogue discovery in this benchmark.

### 4. CMOR-style wavelet

No performance comparison will be manufactured. The frozen SonotaCo seven-year input audit found only 199/324 usable solar-longitude bins meeting the published local-radiant support floor, below the preregistered 80% requirement. CMOR wavelet remains **scientifically deferred for input incompatibility**, not scored as a loss.

## Matched evaluation rules

All v8 proposals, families, pooled centroids, local episodes, scores, and rankings are frozen before any retained shower label is consulted.

The new v8 SonotaCo transport changes only survey/year/parser plumbing. It may not change any scientific constant.

### Common shower-size bins

Annual known-shower size is computed after the benchmark parser's existing target exclusion and mapping rules:

- 4–9
- 10–24
- 25–49
- 50–99
- 100+

The benchmark reports **all bins**, not only sparse showers.

### V8 annual coverage endpoint

For each year and known shower, evaluate every already-frozen recurrent v8 family using only that year's family members. Match the family giving maximum F1 for that shower, breaking ties by precision, overlap count, then stable family ID. This label use is evaluation-only and occurs after the family/ranking freeze.

Report by annual size bin:

- number of reference showers;
- mean matched F1;
- showers with F1 > 0.5;
- showers with F1 > 0.8.

This endpoint is directly comparable in interpretation to the published-method annual coverage diagnostics, while retaining the important caveat that v8 proposals themselves require cross-year recurrence.

### V8 recurrent discovery endpoint

For showers with at least four mapped members in **both** 2023 and 2025, match one and the same recurrent v8 family by maximizing the minimum of its two annual F1 values, then geometric-mean annual F1, then total overlap, then stable family ID.

Report:

- minimum annual F1;
- geometric-mean annual F1;
- recovery at minimum annual F1 >= 0.5;
- recovery at minimum annual F1 >= 0.8;
- recovery and F1 by the minimum annual shower-size bin.

This is v8's natural recurrent-stream endpoint. It is not silently equated with an annual clustering task.

### Ranking quality

For the frozen v8 multiplicity order report:

- family count;
- top-K known-family recovery with `K=ceil(100*N/226)`, preserving v8's development top-100 catalogue fraction;
- top-K dominant-label precision;
- MRR of qualified known-shower matches;
- sparse and overall recovery by annual size bin where defined.

If downloaded published-method artifacts expose a genuine native cluster ranking and per-shower records, a secondary ranking comparison may be computed. If they do not, no artificial ranking will be invented for them.

## False-positive and compute reporting

Report for each method wherever the frozen artifacts make the quantity meaningful:

- number of returned families/clusters;
- noise/unassigned fraction for catalogue clustering;
- top-K dominant-label precision for v8;
- runtime and clone count for Sugar;
- runtime if recorded for v8/HDBSCAN;
- any method-specific false-positive burden clearly labelled rather than forced into an invalid common statistic.

## Comparison decision rules

The following interpretation is frozen before the new v8 SonotaCo run:

1. **Sparse HDBSCAN win for v8** may be stated only if v8's annual 4–9 and/or 10–24 mean F1 and F1>0.5 recovery are materially above the frozen HDBSCAN all-shower coverage values in both years, while the report also acknowledges HDBSCAN's large-shower advantage if present.
2. **Sparse Sugar win for v8** may be stated only if v8 materially exceeds the full retained-master Sugar result in the 4–9 bin in both years and does not rely on excluding unfavorable non-sparse bins from the report.
3. A broad claim that v8 "beats Sugar" or "beats HDBSCAN" is prohibited unless it wins the corresponding overall catalogue metrics on a genuinely common task. Sparse-regime superiority must be scoped to sparse recurrent-stream discovery/recognition.
4. A **state-of-the-art claim** is permitted only in a narrow scope supported by the matched results, for example "stronger sparse recurrent-stream recovery than these faithfully transferred catalogue methods on the target-excluded SonotaCo benchmark." It may not be generalized to all meteor-stream discovery, all surveys, radar wavelets, or all published methods.
5. Any integrity failure, underpowered family universe, or missing comparator record is preserved and reported as a limitation, not repaired by changing v8 or a competitor.

## Prohibitions

- No final OrbitTrace target reveal.
- No access to OrbitTrace coordinates, members, identity, excluded-interval contents, or target-specific recovery artifacts.
- No v8 tuning based on literature-method performance.
- No competitor weakening, sparse-specific retuning, or parameter matching that departs from the cited published configuration.
- No suppression of negative v8 or positive competitor results.
- No CMOR performance claim from an input-feasibility failure.
- No D_SH catalogue-discovery claim from an episode/targeted association implementation.
