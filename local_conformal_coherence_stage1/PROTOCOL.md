# Local conformal coherence: frozen complex-held-out power gate

Status: Stage-1 candidate. Stage-0 null calibration passed on runner commit `c419be5d6e5bb1989586182e1f5c755313148ec7`. This protocol is frozen before any labeled-shower power result is computed.

## Scientific question

Can the locally calibrated method retain useful power for weak real meteor showers while preserving its false-alarm control on disjoint real sporadic backgrounds?

The claimed mechanism is not a new clustering algorithm by itself. It is the combination of:

1. reference/query cross-fitting inside each candidate search window, so a meteor cannot create its own evidence;
2. a fixed small-subset coherence statistic aimed at 4–8-member streams;
3. rank calibration against real background windows matched by year and solar-longitude sector;
4. a blinded null audit and complex-held-out real-shower power audit with no labeled-shower training.

## Frozen data and blindness

- Use the exact `selected_events.jsonl.gz` artifact and frozen parser from PR #14.
- Remove every event with solar longitude from 20.0 degrees through 55.0 degrees before any pool, window, score, or threshold is formed.
- The broad blind interval contains GhostStream-April-36.9. No GhostStream radiant, speed, orbit, membership, event list, or detection score may be used.
- Preserve the frozen ESV exclusion from the PR #14 parser.
- Established GMN shower labels are used only after the score and gates are frozen, and only to measure power.

## Search windows

Use the PR #14 geometry:

- 128 events per window;
- one frozen year;
- a +/-10 degree solar-longitude neighborhood;
- positive windows contain `k in {4, 6, 8, 12}` real members from one established shower-year and real local sporadics;
- weak-power endpoints use `k in {4, 6, 8}`;
- negative windows contain only real local sporadics.

## Fixed physical distance

Use exactly the PR #14 pairwise distance with fixed scales:

- relative solar longitude / 2 degrees;
- Sun-centered ecliptic longitude, latitude / 2 degrees;
- geocentric speed / 2 km/s.

No orbit elements, shower identity, absolute date, or absolute solar longitude enter the candidate score.

## Cross-fitted coherence score

For each window:

1. Compute its full 128-by-128 fixed physical distance matrix.
2. For each of eight deterministic split salts, divide the window into exactly 64 reference and 64 query events.
3. For every query event, measure its distance to the second-nearest reference event.
4. Take the mean of the two smallest query-to-reference second-neighbor distances and negate it, so larger is more coherent.
5. The final window score is the median across the eight split salts.

The top-two/second-neighbor construction is fixed from the target geometry before power is observed. It requires at least two query meteors to be supported by at least two reference meteors, corresponding to a four-event coherent subset, while the eight deterministic splits reduce dependence on one lucky partition.

## Local rank calibration

Define 60-degree solar-longitude sectors within each frozen year. The blind interval is removed before sector pools are built.

Stable-hash every sporadic event into one of two disjoint background pools:

- calibration-background pool;
- untouched null-test/background pool.

For every supported year-sector:

- generate 512 deterministic calibration negative windows from the calibration-background pool;
- generate 256 deterministic untouched negative windows from the null-test pool;
- require at least 128 locally available events for every generated window;
- convert a score to the conservative local rank p-value

`p = (1 + number of matched calibration scores >= score) / 513`.

Also compute a deliberately unmatched global rank calibration from every calibration sector combined. It is an ablation, not the candidate decision rule.

The resampled windows within a sector can overlap. Therefore the audit treats year-sector as the uncertainty block and reports empirical error by block; it does not claim independent-binomial exactness for individual windows.

## Real-shower evaluation

- Use the frozen MDC complex/parent grouping and five event-count-balanced folds from the blinded labeled data.
- No fold trains or tunes the candidate; folds are reporting units that prevent one shower family from dominating the result.
- Generate four deterministic positive replicates for every eligible shower-year-member-count combination using only the untouched background pool.
- Map every positive window to its year-sector and score it with the frozen local calibration.
- Keep the radius-2.5 local-density score and epsilon-2.5 DBSCAN score from PR #14 as fixed raw-power comparators. No parameter is reselected on Stage-1 labels.

## Frozen endpoints

Primary:

- mean weak-window AUROC across the five complex folds;
- detection recall at local p <= 0.05 and p <= 0.01 for k = 4, 6, and 8;
- empirical false-positive rate on untouched negative windows at the same thresholds.

Secondary:

- per-fold weak AUROC;
- power monotonicity with member count;
- worst year-sector false-positive rate;
- local-versus-global worst-sector calibration;
- candidate AUROC relative to fixed density and DBSCAN comparators.

## Frozen continuation gates

All must pass:

1. untouched-negative pooled false-positive rate <= 0.060 at alpha 0.05;
2. untouched-negative pooled false-positive rate <= 0.020 at alpha 0.01;
3. worst supported year-sector false-positive rate <= 0.120 at alpha 0.05;
4. local calibration has no worse worst-sector alpha-0.05 error than global unmatched calibration;
5. mean weak-window AUROC >= 0.75;
6. candidate weak AUROC is no more than 0.03 below the stronger fixed density/DBSCAN comparator;
7. at least four of five folds have weak AUROC >= 0.70, and no fold is below 0.65;
8. local-p recall at alpha 0.05 is at least 0.15, 0.30, and 0.45 for k = 4, 6, and 8 respectively;
9. local-p recall at alpha 0.01 is at least 0.05, 0.15, and 0.25 for k = 4, 6, and 8 respectively;
10. recall is nondecreasing from k = 4 to 6 to 8 to 12 at both thresholds.

## Kill rules

Kill the formulation if any gate fails. Do not rescue it by changing neighbor count, top-event count, split count, feature scales, sector width, p-value threshold, comparator parameter, shower subset, fold definition, or blind interval after seeing Stage-1 results.

A pass authorizes a separately frozen external weak-stream control and catalog-level multiple-testing study. It does not authorize a GhostStream claim or application.
