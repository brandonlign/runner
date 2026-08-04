# Partition-invariant four-star coherence: frozen H1 2026 confirmation protocol

Status: frozen before downloading or reading any January–June 2026 shower labels or candidate scores.

## Scientific question

Can a deterministic four-point coherence statistic recover the exactly-four-member sensitivity lost by the median reference/query split in PR #31 while preserving empirical false-alarm calibration and weak-shower discrimination?

PR #31 established that the same-corpus empirical-window null generalized to untouched 2020/2022/2024 data, but the split statistic failed only its two exactly-four-member recall gates. This is a new candidate, not a threshold adjustment or rerun of PR #31.

## Development and confirmation boundary

- Candidate development data: 2019, 2021, 2023, and 2025.
- Retired data that may not be reused for confirmation: 2020, 2022, and 2024.
- Untouched confirmation data: official GMN monthly trajectory summaries for January through June 2026 only.
- The candidate statistic, window generator, calibration design, seeds, comparators, endpoints, and gates are frozen before the 2026 data are downloaded.
- July and August 2026 are excluded even if available at runtime.

## GhostStream blindness

Before every pool, score, calibration distribution, fold, and endpoint, remove all events with solar longitude from 20.0° through 55.0°. No GhostStream radiant, speed, orbit, membership, event list, or detection score is used.

## Frozen data construction

Derive the January–June 2026 audit from the exact PR #14 parser, verified by Git blob SHA `4a029051230f7c6e99b09e911f8a9e5228a58783`.

A shower is eligible when it has at least 20 quality events in H1 2026. A strong shower has at least 100 quality events. The frozen data gates require:

- at least 20 eligible showers;
- at least 10 strong showers;
- at least 15 eligible MDC complex/parent units;
- at least 3 multi-shower complex units;
- at least 100,000 quality sporadic events before reservoir sampling;
- at least 95% completeness in the selected artifact.

Failure of any data gate kills the H1 2026 confirmation without changing months or thresholds.

## Search windows

- 128 events per window;
- one observing year and a ±10° solar-longitude neighborhood;
- positive windows contain `k in {4, 6, 8, 12}` real established-shower members and real local IAU `-1` meteors;
- four deterministic replicates per eligible shower/member-count combination;
- negative windows contain only real local IAU `-1` meteors;
- calibration and audit windows are independent draws from the same fixed empirical sporadic corpus.

## Fixed physical geometry

Use the exact PR #14 distance:

- relative solar longitude / 2°;
- Sun-centered ecliptic longitude and latitude / 2°;
- geocentric speed / 2 km/s.

No orbital elements, shower identity, absolute date, or absolute solar longitude enter the candidate score.

## Partition-invariant four-star score

For each 128-event window:

1. Compute the complete pairwise physical-distance matrix.
2. Treat every event as a possible center.
3. Add that center's three nearest neighbors.
4. Measure the maximum of the six pairwise distances within the resulting four-event set.
5. Take the minimum diameter across all 128 centers and negate it, so larger values indicate tighter four-point coherence.

The score uses every event symmetrically and contains no random reference/query partition. It directly targets the minimum four-event structure while remaining deterministic and computationally bounded.

## Frozen label-blind null gate

For every supported 60° solar-longitude sector in H1 2026:

- 256 calibration windows and 128 audit windows per batch;
- four independent fixed seed batches;
- conservative local rank p-values;
- at least three supported sectors.

Every batch must satisfy:

- pooled FPR at alpha 0.05 ≤ 0.060;
- pooled FPR at alpha 0.01 ≤ 0.020;
- worst-sector FPR at alpha 0.05 ≤ 0.120.

The null stage discards all shower labels before scoring.

## Frozen power gate

After an all-pass null result, run 512 fresh calibration windows and 256 independent negative windows per supported sector, plus the real positive panel.

Fixed comparators:

- local density with radius 2.5;
- DBSCAN with epsilon 2.5 and minimum samples 4.

Five deterministic folds contain complete MDC complex/parent units and are reporting units only.

Every power gate must pass:

1. pooled negative FPR at 0.05 ≤ 0.060;
2. pooled negative FPR at 0.01 ≤ 0.020;
3. worst-sector FPR at 0.05 ≤ 0.120;
4. weak-window AUROC ≥ 0.75;
5. candidate AUROC no more than 0.03 below the stronger fixed comparator;
6. at least four of five folds have AUROC ≥ 0.70 and no fold is below 0.65;
7. recall at 0.05 is at least 0.15, 0.30, and 0.45 for k=4,6,8;
8. recall at 0.01 is at least 0.05, 0.15, and 0.25 for k=4,6,8;
9. recall is nondecreasing through k=12 at both thresholds.

Any failed gate kills this candidate. No source, month, seed, score, threshold, comparator, fold, or shower subset may be changed after results are observed.

A pass authorizes only a separately frozen external weak-stream control and catalog-level family-wise error study. It does not authorize application to GhostStream.
