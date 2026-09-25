# SonotaCo 2025 external development of the exact Mondrian four-clique method

Status: frozen before any SonotaCo detector score, window, fold, AUROC, false-positive rate, or recall endpoint is computed.

## Scientific question

Does the exact coverage-normalized four-clique method that passed GMN development in PR #38 retain calibration and weak-shower discrimination when transferred without score changes to an independent meteor survey?

This is external **development**, not confirmation. The exact survey-native token rule was selected and audited on SonotaCo 2025 in PR #66. SonotaCo 2024 remains value- and label-blinded and is reserved for one-shot confirmation only if every frozen 2025 gate passes.

## Frozen source boundary

- SonotaCo archive: `025a.zip`, SHA-256 `f4eb716a4b900658fcc658a633d918eca28946f59da75935f1fd5f6bc539bf52`.
- Annual member: `025a/_U2_20250101_S.csv`, SHA-256 `30d8cbdf414b2e9d6e587374fec7a4b6fa94c86e76a35e9b335cd4d0cbc917f7`.
- GMN/MDC mapping audit: SHA-256 `f8ba2446dce96d69652727092189903c40493e2fe741eb746f7fb5181edea778`.
- Exact PR #38 scorer: SHA-256 `f1c121e97a660a3820a11814c4325eb3ab33d34a031e83bdfb03b4b392e259b8`.
- Exact baseline payload: SHA-256 `2cb82a8c12913a6176ddd7c6333b57a4d672334934c0d2ca4b572e878590cfa2`; decoded source SHA-256 `7718ac5229475f4240305ad9c1e073c49702c771df36612d9be5baa877b46a50`.
- Frozen event-adapter source: SHA-256 `98f486b57cd9913a7183d2c529eecbeea8ab629bc139aa0cb53bdc36f647dfc8`.

The scorer is executed byte-for-byte. No statistic, seed, calibration bin, comparator, fold rule, threshold, or scientific gate is rewritten for SonotaCo.

## GhostStream blindness

Remove every row with solar longitude from 20.0° through 55.0° inclusive before label mapping, reservoirs, windows, scores, folds, or endpoints. No GhostStream radiant, speed, orbit, members, score, or local region enters this study.

## Frozen survey adapter

1. Parse all 36,826 published rows using the exact SonotaCo headers.
2. Require valid solar longitude, radiant, speed, at least two cameras, and complete nonnegative reported uncertainties.
3. Define background only as blank/no-letter tokens or tokens beginning `SPO`.
4. Map a labeled row only under the exact rule `^([A-Z0-9]{3})_JA$ -> captured three-character prefix` and only when that prefix has one unambiguous eligible GMN/MDC mapping.
5. Exclude every other labeled row. Never reassign an unmatched or invalid labeled row to background.
6. Preserve observed solar longitude, equatorial radiant, geocentric speed, reported uncertainties, station count, and fit error in the frozen GMN event schema.

The adapter must reproduce the aggregate-only PR #66 boundary exactly: 24,052 background events and 10,756 matched labeled events, with at least 30 supported codes and 25 supported complex/parent keys.

## Exact candidate and calibration

Use the unchanged PR #38 implementation:

- 128-event windows from a ±10° solar-longitude neighborhood;
- physical distance from relative solar longitude / 2°, Sun-centered ecliptic radiant longitude / 2°, latitude / 2°, and geocentric speed / 2 km/s;
- anchored four-event complete-link coherence score;
- globally anchored 10° Mondrian calibration bins;
- 128 same-survey calibration windows and 64 independent negative windows per supported bin;
- four positive replicates for k in {4,6,8,12};
- conservative rank p-values;
- the exact PR #38 seed prefixes.

Use `year=2025` and the pre-existing `odd-archive` corpus identifier solely because those are the exact scorer's frozen accepted interface values. They do not mix GMN events into SonotaCo.

## Fixed comparators and folds

Compute on identical windows:

- killed eight-split local conformal coherence statistic;
- radius-2.5 local density;
- epsilon-2.5 DBSCAN largest cluster;
- five complete complex/parent folds assigned by the unchanged baseline code.

## Frozen continuation gates

Every source-encoded PR #38 gate must pass independently:

1. pooled FPR at 0.05 <= 0.060;
2. pooled FPR at 0.01 <= 0.020;
3. worst 60° reporting-sector FPR at 0.05 <= 0.120;
4. weak-window AUROC >= 0.75;
5. candidate AUROC within 0.03 of the strongest comparator;
6. at least four of five folds have AUROC >= 0.70 and none is below 0.65;
7. recall at 0.05 is at least 0.15, 0.30, and 0.45 for k=4,6,8;
8. recall at 0.01 is at least 0.05, 0.15, and 0.25 for k=4,6,8;
9. recall is nondecreasing from k=4 to 6 to 8 to 12 at both thresholds.

Additional transfer requirements:

- at least 20 supported fixed 10° bins;
- at least 30 eligible showers after the blind interval;
- candidate AUROC must exceed both density and DBSCAN;
- all five fold AUROCs must be finite and every fold must contain at least one complex unit.

Any failed adapter or scientific gate kills this exact transfer. No mapping rule, event filter, bin, calibration count, seed, score, comparator, fold, threshold, or endpoint may change after the result.

A complete pass gives `PROCEED_TO_FROZEN_SONOTACO_2024_CONFIRMATION`. It authorizes only a separately frozen one-shot 2024 external confirmation using the already-pinned parser-v2 panel. It does not authorize GhostStream or catalogue application.
