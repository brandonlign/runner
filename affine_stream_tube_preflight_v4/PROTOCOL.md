# Four-event affine stream-tube scan: interface-complete frozen preflight

Status: frozen before any scientific score, calibration endpoint, recall value, AUROC, fold result, or continuation decision is computed.

## Scientific question

Can a sparse meteor stream be detected more effectively as a narrow local one-dimensional trajectory in solar-longitude/radiant/speed space than as a compact four-event blob?

This is the same physical formulation registered in PR #72. PR #72 produced no scientific result: its original source failed before scoring because it called functions with signatures that do not exist in the exact inherited PR #14/PR #38 modules, and later payload assembly was repeatedly cancelled. This branch fixes only those interface and execution semantics prospectively and preserves the statistic, coordinates, counts, seeds, gates, years, comparators, folds, and blind interval.

## Development boundary and blindness

- use only retired GMN 2019 and 2025 events from the exact PR #14 selected-event artifact;
- remove solar longitude 20.0° through 55.0° inclusive immediately after loading and before all factories, reservoirs, support probes, windows, scores, folds, and endpoints;
- do not read 2020, 2022, 2024, or 2026 events or results;
- use no GhostStream radiant, speed, orbit, member, event list, score, or local region.

## Frozen physical statistic

Every 128-event window uses:

- relative solar longitude / 2°;
- Sun-centered ecliptic radiant longitude / 2°, circularly wrapped and multiplied by the mean-latitude cosine;
- Sun-centered ecliptic radiant latitude / 2°;
- geocentric speed / 2 km/s.

For every anchor event:

1. find its three nearest other events using only phase-marginal radiant longitude, radiant latitude, and speed;
2. form the anchored four-event subset;
3. construct the four standardized coordinates above;
4. center the four points and fit their best one-dimensional affine line by eigendecomposition;
5. compute the RMS orthogonal residual to that line.

The window score is the negative minimum residual over all 128 anchors. Larger scores indicate a narrower observed stream tube. There is no template bank, learned radius, shower identity, orbital element, absolute date, or random partition in the candidate statistic.

## Frozen inherited interfaces

- exact PR #14 baseline source SHA-256: `7718ac5229475f4240305ad9c1e073c49702c771df36612d9be5baa877b46a50`;
- exact PR #38 scorer source SHA-256: `f1c121e97a660a3820a11814c4325eb3ab33d34a031e83bdfb03b4b392e259b8`;
- exact selected-event SHA-256: `63e1389e2666d10b05138044f428609266b367cabab2542295c154a510e40f01`;
- exact audit SHA-256: `f8ba2446dce96d69652727092189903c40493e2fe741eb746f7fb5181edea778`.

The adapter must use:

- `base.load_events`, `base.EpisodeFactory`, and `base.assign_folds` exactly as defined;
- `scorer.MondrianWindowFactory.make(year, bin, seed)` for sporadic windows;
- `scorer.make_positive(base, factory, shower, year, k, seed)` for positives;
- `scorer.score_all(base, episode, key)` for the exact anchored-quartet, split, density, and DBSCAN comparators;
- `scorer.conservative_rank_pvalue(score, calibration_scores)` for p-values.

## Frozen two-year Mondrian adapter

Calibration is pooled across the two retired years within each absolute 10° solar-longitude bin, matching the originally registered single-bin bank:

- a bin is supported when at least one of 2019 or 2025 can construct its deterministic support-probe window;
- each calibration or negative draw selects uniformly among the supported years for that bin using its already frozen deterministic RNG stream, then calls the exact year-specific PR #38 factory;
- positive construction selects uniformly among that shower's eligible 2019/2025 years using its frozen seed and retries only until its center falls in a supported bin;
- no year weight, support rule, or seed may change after execution.

Complex folds are the exact PR #14 folds on the blinded 2019/2025 labeled events. Eligible showers are those retained by the exact PR #14 episode factory.

## Frozen preflight

- 64 calibration and 32 independent negative windows per supported 10° bin;
- one positive replicate per eligible shower and `k ∈ {4,6,8,12}`;
- at least 20 supported bins, 25 eligible showers, and five nonempty complex folds;
- fixed seed prefixes already encoded in source;
- four worker threads affect execution only, never randomness or ordering.

## Fixed comparators

On the identical windows:

- PR #38 anchored four-event complete-link diameter;
- PR #31 eight-split reference/query statistic inherited through PR #38;
- radius-2.5 local density;
- epsilon-2.5, minimum-samples-4 DBSCAN.

## Frozen continuation gates

Every gate must pass:

1. pooled FPR at 0.05 ≤ 0.07 and at 0.01 ≤ 0.025;
2. worst supported 10°-bin FPR at 0.05 ≤ 0.1875;
3. weak-window AUROC ≥ 0.76 and within 0.03 of the strongest comparator;
4. at least four of five complex-fold AUROCs ≥ 0.68 and none below 0.62;
5. k=4 recall ≥ 0.16 / 0.04 at p ≤ 0.05 / 0.01;
6. k=4 gain over the anchored quartet ≥ 0.015 at at least one threshold;
7. k=6 recall ≥ 0.25 / 0.10 and k=8 recall ≥ 0.40 / 0.20;
8. recall is nondecreasing through k=12 at both thresholds.

Any failed gate kills this exact formulation. No neighbor count, coordinate, scale, line fit, residual, year pooling, calibration count, bin, seed, threshold, comparator, fold, blind interval, or endpoint may change afterward.

A pass authorizes only a separately frozen full four-year complex-held-out benchmark. It does not authorize confirmation data, a catalogue scan, or GhostStream application.

Exact candidate source SHA-256: `7ec195a34fa286129f01d181b7a8365623a0266d76c153a155d98d220cc833f3`.