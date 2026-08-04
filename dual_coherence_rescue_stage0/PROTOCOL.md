# Dual-coherence quartet rescue: frozen development screen

## Question

Can a partition-invariant four-event coherence channel recover the exactly-four-member sensitivity lost by the median eight-way reference/query statistic, while a separate outer empirical calibration preserves the strong false-alarm control and multi-member power already demonstrated by local conformal coherence?

This is a **new development candidate**, not a rescue or reinterpretation of PR #31. PR #31 remains killed under its frozen gate.

## Development and confirmation boundary

- Development data: GMN years 2019, 2021, 2023, and 2025 from the exact PR #14 artifact.
- Retired data: 2020, 2022, and 2024. Their prior Stage-0 and Stage-1 results motivated the structural diagnosis, but no event, label, score, or outcome from those years may be read by this screen.
- If every gate passes, the only authorized continuation is a separately frozen **fresh-year data gate** for 2018 and the available blinded 2026 interval. A development pass does not authorize a GhostStream application or catalog scan.

## GhostStream blindness

Before any pool, window, score, calibration set, fold, or endpoint is formed, remove every event with solar longitude from 20.0° through 55.0°. No GhostStream radiant, speed, orbit, membership, event list, or detection score may be used.

## Frozen data and windows

- Use the exact PR #14 selected-event artifact from runner workflow `30855193522`.
- Preserve its parser, quality filters, IAU MDC complex/parent grouping, five complex-disjoint folds, and ESV exclusion.
- Use all 24 year-by-60° solar-longitude groups in 2019/2021/2023/2025.
- Every window contains 128 events from one year and a ±10° solar-longitude neighborhood.
- Positive windows contain `k in {4, 6, 8, 12}` real members of one established shower-year plus local real IAU `-1` meteors.
- Use two deterministic positive replicates for every eligible shower-year-member-count combination.
- Negative windows contain only local real IAU `-1` meteors.

## Shared physical geometry

Use the exact PR #14 distance:

- relative solar longitude / 2°;
- Sun-centered ecliptic longitude / 2°;
- Sun-centered ecliptic latitude / 2°;
- geocentric speed / 2 km/s.

No orbital elements, shower identity, absolute date, or absolute solar longitude enter either candidate component.

## Component 1: unchanged local conformal coherence

For each window:

1. Form the full physical-distance matrix.
2. For each of eight deterministic salts, split the 128 events into 64 reference and 64 query events.
3. For every query event, compute distance to its second-nearest reference event.
4. Average the two smallest query distances and negate the result.
5. Take the median across the eight splits.

This is the unchanged mechanism that generalized strongly in PR #31 but missed the two k=4 recall gates.

## Component 2: partition-invariant quartet cover

For each event, compute its distance to its third-nearest other event. Take the minimum across all 128 possible centers and negate it.

Equivalently, this is the negative radius of the smallest event-centered ball containing four observed events. It is invariant to arbitrary reference/query partitions and directly targets an exactly-four-event coherent subset. The metric triangle inequality bounds every pair in the selected quartet by twice the covering radius.

## Nested same-corpus local calibration

For every year-sector, draw independent windows from the same fixed empirical sporadic corpus and generator:

1. **Inner calibration:** 128 windows. Build separate empirical score distributions for LCC and quartet cover.
2. Convert each later window’s two raw component scores to conservative local rank p-values against those inner distributions.
3. Define the union statistic as `-log(min(p_LCC, p_quartet))`.
4. **Outer calibration:** 128 new windows. Build the empirical local distribution of the union statistic.
5. **Audit:** 64 additional windows. Convert the union statistic to a final conservative local rank p-value against the outer distribution.

The outer layer is mandatory: it calibrates the multiple-statistic union itself rather than treating the smaller component p-value as valid without correction. Window overlap is allowed because the inferential unit is a Monte Carlo draw from the fixed empirical window generator.

## Fixed comparators

- unchanged LCC component;
- quartet component alone;
- radius-2.5 local density;
- DBSCAN with epsilon 2.5 and minimum samples 4.

No comparator parameter is reselected.

## Frozen endpoints

Primary:

- union weak-window AUROC for `k in {4,6,8}`;
- k=4 union recall and gain relative to the contemporaneous unchanged LCC component at final local p ≤0.05 and ≤0.01;
- pooled and worst-sector union false-positive rates;
- preservation of k=6 and k=8 recall.

Secondary:

- all component and comparator AUROCs;
- five complex-fold AUROCs;
- monotonic recall through k=12;
- fraction of k=4 positives detected by the union but missed by LCC.

## Frozen continuation gates

Every gate must pass:

1. pooled union FPR at 0.05 ≤0.060;
2. pooled union FPR at 0.01 ≤0.020;
3. worst year-sector union FPR at 0.05 ≤0.120;
4. union weak AUROC ≥0.79;
5. union AUROC no more than 0.01 below unchanged LCC;
6. union AUROC no more than 0.01 below the stronger fixed density/DBSCAN comparator;
7. at least four of five union fold AUROCs ≥0.75;
8. no union fold AUROC below 0.70;
9. union k=4 recall at 0.05 ≥0.17;
10. union k=4 recall at 0.05 exceeds LCC by at least 0.025;
11. union k=4 recall at 0.01 ≥0.06;
12. union k=4 recall at 0.01 exceeds LCC by at least 0.01;
13. union k=6 recall at 0.05 is no more than 0.03 below LCC;
14. union k=8 recall at 0.05 is no more than 0.03 below LCC;
15. union k=6 recall at 0.01 is no more than 0.03 below LCC;
16. union k=8 recall at 0.01 is no more than 0.03 below LCC;
17. union recall is nondecreasing from k=4 to 6 to 8 to 12 at 0.05;
18. the same monotonicity holds at 0.01;
19. at least 2% of all k=4 positives are unique union rescues at 0.05.

Any failed gate kills the candidate. Do not change component definitions, aggregation, sample counts, seeds, sectors, thresholds, folds, member counts, comparator parameters, or blind interval after observing the result.
