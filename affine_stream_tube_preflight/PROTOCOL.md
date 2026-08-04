# Four-event affine stream-tube scan: frozen development preflight

Status: frozen before authoritative scoring. This stage reads only the retired GMN development years 2019 and 2025 from the exact PR #14 artifact. It reads no 2020, 2021, 2022, 2023, 2024, or 2026 event into any development pool, score, fold, or endpoint.

## Scientific question

Can a sparse meteor stream be detected more effectively as a narrow local one-dimensional trajectory in solar-longitude/radiant/speed space than as a compact four-event blob?

This is distinct from killed PR #7. PR #7 scanned a coarse global bank of fixed drifting templates. This candidate searches only observed anchored four-event subsets, fits each subset's best local affine line, and empirically calibrates the complete selection against real same-corpus sporadic background.

## GhostStream blindness

Solar longitude 20 degrees through 55 degrees inclusive is removed from both labeled and sporadic 2019/2025 events before the Mondrian factory, positive factory, supported-bin probes, calibration windows, negative windows, folds, scores, or endpoints are formed. The authoritative result records the number removed and fails if any such event survives. No GhostStream radiant, speed, orbit, member, event list, detection score, or detailed solar-longitude location is used.

## Frozen physical statistic

Every 128-event window retains the established physical coordinates and scales:

- relative solar longitude / 2 degrees;
- Sun-centered ecliptic radiant longitude / 2 degrees, with circular wrapping and latitude cosine;
- Sun-centered ecliptic radiant latitude / 2 degrees;
- geocentric speed / 2 km/s.

For each event:

1. identify its three nearest other events in phase-marginal radiant/speed space, excluding relative solar longitude;
2. form the anchored four-event subset;
3. express its four standardized physical coordinates relative to the anchor;
4. fit the best one-dimensional affine line by principal components;
5. compute the RMS orthogonal residual from the line.

The window score is the negative minimum residual among all 128 anchored subsets. Larger scores indicate a narrower observed stream tube. The score has no random partition, global template bank, fitted radius, shower identity, orbit, or absolute date.

## Frozen development preflight

- years: 2019 and 2025 only;
- 128-event plus-or-minus 10-degree local windows;
- year-specific globally anchored 10-degree same-corpus Mondrian calibration;
- 64 calibration and 32 independent negative windows per supported year-bin;
- one positive replicate per eligible shower-year and `k in {4,6,8,12}`;
- at least 20 supported bins in each year, 25 eligible showers, and five nonempty complex/parent folds;
- exact deterministic seed prefixes `affine-tube-support`, `affine-tube-cal`, `affine-tube-neg`, and `affine-tube-pos`, with year included because window construction is year-specific;
- exact PR #14 episode/geometry source SHA-256 `7718ac5229475f4240305ad9c1e073c49702c771df36612d9be5baa877b46a50`;
- exact PR #38 scorer source SHA-256 `f1c121e97a660a3820a11814c4325eb3ab33d34a031e83bdfb03b4b392e259b8`;
- candidate source SHA-256 `1a9a69e7968840703f9a4199ef211bc597d318ac54f4602c6524b0028aa37759`;
- gzip/base64 encoded source length 8,608 characters in exactly three v4 chunks.

## Execution-integrity repair

The earlier runner attempts failed before an authoritative scientific result. The first called nonexistent convenience interfaces on the hash-verified PR #38 module. Later partial source encodings were never allowed to produce a score. The final repair was frozen without viewing any candidate, comparator, p-value, recall, AUROC, or fold endpoint.

The repaired harness changes only execution and data-boundary wiring required to implement the already frozen protocol:

- PR #14 events are filtered to 2019/2025 and then to the blind-excluded region before any factory is created;
- event complex keys are verified against the supplied PR #14 audit;
- the exact PR #14 module supplies episode construction, geometry, and complex-disjoint folds;
- the exact PR #38 module supplies Mondrian windows, positive-window construction, anchored quartet and split comparators, and conservative rank p-values;
- calibration is indexed by exact year and 10-degree bin;
- fixed density and DBSCAN comparators are computed from the exact PR #14 distance matrix using the PR #38 fixed parameters;
- all scientific failures write an authoritative JSON and Markdown result before the workflow gate fails.

No affine neighbor rule, coordinate, scale, line fit, residual, calibration count, negative count, positive count, comparator parameter, threshold, fold rule, blind interval, or scientific gate may change after the first authoritative result.

## Fixed comparators

Compute on identical windows:

- PR #38 anchored quartet diameter;
- PR #31 reference/query split statistic;
- radius-2.5 local density;
- epsilon-2.5, minimum-samples-4 DBSCAN.

## Frozen continuation gates

Every source-encoded gate must pass:

1. pooled FPR at 0.05 <= 0.07 and at 0.01 <= 0.025;
2. worst supported year-bin FPR at 0.05 <= 0.1875;
3. weak-window AUROC >= 0.76 and within 0.03 of the strongest fixed comparator;
4. at least four of five complex folds AUROC >= 0.68 and none below 0.62;
5. k=4 recall >= 0.16 / 0.04 at p <= 0.05 / 0.01;
6. k=4 gain over the anchored quartet of at least 0.015 at one threshold;
7. k=6 recall >= 0.25 / 0.10 and k=8 recall >= 0.40 / 0.20;
8. recall nondecreasing through k=12 at both thresholds.

Any failed gate kills this exact formulation. A pass authorizes only a separately frozen full four-year complex-held-out benchmark. It does not authorize confirmation data, a catalogue scan, SonotaCo 2024, or GhostStream application.
