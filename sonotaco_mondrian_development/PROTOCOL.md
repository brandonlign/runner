# SonotaCo 2025 coverage-normalized Mondrian quartet: frozen development protocol

Status: frozen before any SonotaCo candidate score, comparator score, p-value, AUROC, recall, false-positive endpoint, fold endpoint, or continuation decision is computed.

## Scientific question

Does the coverage-normalized 10° Mondrian four-clique mechanism that passed the GMN retrospective panels retain calibration and sparse-stream power in an independently produced meteor survey with different instrumentation, reductions, sampling density, and native shower labels?

This is an external-survey development test, not a new detector search. The quartet statistic, physical geometry, window size, calibration counts, comparator parameters, performance gates, and fold rules are inherited unchanged from the passed PR #38 formulation.

## Development and confirmation boundary

- SonotaCo 2025 is consumed development data because PR #58 exposed its aggregate label syntax and PR #66 validated one generic survey-native prefix rule.
- SonotaCo 2024 remains label- and value-blinded. PR #63 established only its archive/member hashes, row count, row widths, and header structure.
- A complete 2025 pass authorizes only a separately frozen one-shot 2024 confirmation using the exact source, parser rule, seeds, thresholds, folds, and gates fixed here.
- No result authorizes GhostStream application, catalogue scanning, or a discovery claim.

## Pinned inputs and exact inherited modules

- SonotaCo 2025 archive: `https://www.astro.sk/iaumdcDB/public/data/SNMv3/025a.zip`;
- archive SHA-256: `f4eb716a4b900658fcc658a633d918eca28946f59da75935f1fd5f6bc539bf52`;
- annual member: `025a/_U2_20250101_S.csv`;
- member SHA-256: `30d8cbdf414b2e9d6e587374fec7a4b6fa94c86e76a35e9b335cd4d0cbc917f7`;
- exact PR #14 GMN/MDC audit SHA-256: `f8ba2446dce96d69652727092189903c40493e2fe741eb746f7fb5181edea778`;
- exact PR #14 episode/geometry source SHA-256: `7718ac5229475f4240305ad9c1e073c49702c771df36612d9be5baa877b46a50`;
- exact passed PR #38 Mondrian scorer source SHA-256: `f1c121e97a660a3820a11814c4325eb3ab33d34a031e83bdfb03b4b392e259b8`;
- exact external adapter source SHA-256: `5e6d7a6545d83902362cc06c2fae5d285ae92eb2e8e1d7d42fd9769862ebf518`.

The adapter must dynamically load both inherited modules from their committed encoded payloads and reject any hash mismatch. It may not reimplement or modify their score, geometry, episode, fold, or calibration functions.

## Frozen SonotaCo adapter

The adapter performs only these survey-specific operations:

1. parse the exact annual CSV using its documented fields;
2. require finite physical `sol`, RA, Dec, and `Vg`, plus `Ncam >= 2`;
3. remove solar longitude 20.0° through 55.0° inclusive before any reservoir or score;
4. apply the exact PR #66 rule `^([A-Z0-9]{3})_JA$ → captured three-character code`;
5. map that code through the unchanged eligible PR #14 code mapping;
6. use `SPO`/background rows only for the sporadic reservoir;
7. exclude unmatched native labels from both positive and background pools;
8. apply the inherited ESV background mask;
9. convert RA/Dec to J2000 ecliptic longitude/latitude with the inherited function and form Sun-centered longitude with the inherited wrap rule;
10. create deterministic event IDs from annual row indices.

Before scoring, the adapter must exactly reproduce the passed PR #66 aggregate counts: 36,826 total rows, 1,372 blind removals, 24,052 reservoir-ready background rows before ESV exclusion, 10,756 matched rows, 645 unmatched rows, and 34 supported native codes. It must retain at least 10,000 background rows after ESV exclusion and at least 30 distinct mapped showers.

## Exact inherited benchmark

- one year: SonotaCo 2025;
- 128 events per window;
- local solar-longitude half-width: 10°;
- globally anchored 10° Mondrian calibration bins;
- at least 20 supported bins;
- 128 calibration-negative windows per supported bin;
- 64 independent test-negative windows per supported bin;
- positive member counts `k ∈ {4,6,8,12}`;
- four deterministic positive replicates per eligible shower and k;
- minimum 30 eligible showers with at least 20 mapped members;
- exact four-clique score: negative minimum complete-link diameter among every anchor and its three nearest neighbors;
- exact eight-split LCC, radius-2.5 density, and DBSCAN epsilon-2.5/min-samples-4 comparators;
- exact five complex-disjoint folds assigned by inherited count balancing;
- conservative local rank p-value `(1 + calibration exceedances) / 129`;
- unchanged seed prefixes from PR #38 with corpus label `sonotaco-2025-native`.

## Frozen scientific gates

Every gate must pass:

1. pooled candidate FPR at `p <= 0.05` at most 0.060;
2. pooled candidate FPR at `p <= 0.01` at most 0.020;
3. worst 60° reporting-sector FPR at `p <= 0.05` at most 0.120;
4. weak-window AUROC for `k ∈ {4,6,8}` at least 0.75;
5. candidate AUROC no more than 0.03 below the strongest fixed comparator;
6. at least four of five candidate fold AUROCs at least 0.70;
7. no candidate fold AUROC below 0.65;
8. recall at 0.05: k=4 at least 0.15, k=6 at least 0.30, k=8 at least 0.45;
9. recall at 0.01: k=4 at least 0.05, k=6 at least 0.15, k=8 at least 0.25;
10. recall nondecreasing from k=4 to 6 to 8 to 12 at both alpha levels.

All parser-consistency gates are also mandatory.

## Kill and continuation rules

Any failed gate kills this exact external-survey formulation. Do not alter the native-label syntax, mapping, quality rule, ESV mask, feature geometry, window width, quartet score, bin width, calibration count, seed, comparator, fold assignment, threshold, recall gate, survey year, or blind interval after the result.

A complete pass authorizes only a separately frozen SonotaCo 2024 confirmation branch. The 2024 source must be adapted only for its already documented trailing-empty structural difference; no 2024 label token, support count, value, score, or endpoint may be inspected until the complete confirmation source and gates are frozen.