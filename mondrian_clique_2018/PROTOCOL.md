# Coverage-normalized Mondrian four-clique: fresh complete-year 2018 confirmation

Status: frozen before any 2018 GMN file is downloaded, counted, scored, or inspected.

## Scientific question

Does the exact coverage-normalized 10° Mondrian four-clique method that passed the four-panel retrospective matrix in PR #38 preserve false-alarm control and weak-shower power on one completely untouched full observing year?

## Prior-result boundary

- PR #32 remains killed under coarse 60° calibration on fresh 2026 H1.
- PR #36 remains killed under its uniform 20-stratum four-panel feasibility rule.
- PR #38 passed a separately frozen development formulation across 2021, 2024, 2025, and spent January–June 2026.
- PR #38's H1 result is development evidence only because its half-year feasibility threshold was defined after PR #36.
- The present confirmation uses **2018 only**, a complete year never previously inspected in this project.

Before this protocol was committed, no 2018 monthly file, source checksum, event count, shower label, supported-bin count, candidate score, comparator score, or endpoint was read. The first workflow job is data-only. Candidate code is decoded and executed only if every frozen data gate passes.

Any failed data or scientific gate kills this exact confirmation. No file, threshold, seed, bin, score, shower subset, or endpoint may be changed after any 2018 result is observed.

## GhostStream blindness

Remove every event with solar longitude from 20.0° through 55.0° inclusive before fixed-window feasibility, calibration reservoirs, negative windows, positive windows, scores, folds, or endpoints are formed.

No GhostStream radiant, speed, orbit, membership, event list, local region, or detection score may be used.

## Exact one-year extraction

Derive the 2018 audit at runtime from exact PR #14 source `real_shower_meta_stage0/audit_real_shower_data.py`, required Git blob SHA `4a029051230f7c6e99b09e911f8a9e5228a58783`.

Preserve unchanged:

- all twelve GMN monthly-summary URLs;
- row parser and physical-field mapping;
- quality filters;
- MDC complex/parent mapping;
- deterministic labeled and sporadic reservoirs;
- source metadata and checksums;
- at most 500 labeled quality events per shower-year;
- at most 5,000 quality sporadics per month.

One-year eligibility is frozen as:

- eligible shower: at least 200 quality 2018 events and at least 20 events in 2018;
- strong shower: at least 300 quality 2018 events.

## Frozen data gates

Every data gate must pass before the score source is decoded:

1. at least 30 eligible showers;
2. at least 8 strong showers;
3. at least 20 eligible MDC complex/parent units;
4. at least 2 multi-shower complex/parent units;
5. at least 50,000 raw quality IAU `-1` meteors;
6. selected-event feature completeness at least 0.95;
7. exactly twelve nonempty 2018 monthly source files;
8. every selected event is from 2018;
9. after the blind interval is removed, at least 30 globally anchored 10° phase bins contain a sporadic center whose ±10° neighborhood contains at least 128 retained sporadics.

Failure gives `KILL_2018_DATA_GATE` and skips all scoring.

## Frozen windows and geometry

If and only if the data gate passes:

- 128 events per window;
- one year per window;
- ±10° solar-longitude neighborhood;
- positive windows contain `k in {4,6,8,12}` real members from one eligible shower plus local real IAU `-1` meteors;
- four deterministic positive replicates per shower and member count;
- calibration and negative windows contain only local real IAU `-1` meteors;
- exact PR #14 distance with scales: relative solar longitude / 2°, Sun-centered ecliptic longitude / 2°, latitude / 2°, geocentric speed / 2 km/s.

No orbital element, shower identity, absolute date, absolute solar longitude, or catalogue parameter enters the candidate score.

## Exact frozen candidate

Use the exact passed PR #38 implementation reconstructed from `mondrian_clique_development/source_parts_v2/part00.b64` through `part03.b64`:

- decoded source SHA-256: `f1c121e97a660a3820a11814c4325eb3ab33d34a031e83bdfb03b4b392e259b8`;
- complete-year minimum supported-bin rule: 20;
- no source modification is permitted.

For each window:

1. compute the complete 128×128 physical-distance matrix;
2. for each event, select its three nearest other events;
3. compute the complete-link diameter of the anchor-plus-three subset;
4. take the minimum diameter over all anchors;
5. negate it so larger values indicate stronger four-event coherence.

## Exact 10° Mondrian calibration

Use globally anchored `[0°,10°), [10°,20°), ..., [350°,360°)` strata.

For every supported 2018 stratum outside the blind interval:

- 128 deterministic same-corpus calibration windows;
- 64 independent deterministic negative windows;
- conservative p-value `p = (1 + number of calibration scores >= score) / 129`.

Unsupported strata are not merged, shifted, or widened.

Use the exact PR #38 seed prefixes:

- `mondrian-development-support`;
- `mondrian-development-calibration`;
- `mondrian-development-negative`;
- `mondrian-development-positive`;
- `mondrian-development-split`.

## Comparators and folds

Compute on the identical windows:

- killed eight-split PR #31 statistic;
- radius-2.5 local density;
- epsilon-2.5, minimum-samples-4 DBSCAN largest cluster;
- five deterministic event-count-balanced folds of complete MDC complex/parent units.

No comparator or fold may be reselected.

## Frozen confirmation gates

Every gate must pass:

1. pooled candidate FPR at alpha 0.05 ≤0.060;
2. pooled candidate FPR at alpha 0.01 ≤0.020;
3. worst 60° reporting-sector FPR at alpha 0.05 ≤0.120;
4. weak-window AUROC ≥0.75;
5. candidate AUROC no more than 0.03 below the strongest fixed comparator;
6. at least four of five folds have candidate AUROC ≥0.70 and no fold is below 0.65;
7. recall at alpha 0.05 is at least 0.15, 0.30, and 0.45 for k=4,6,8;
8. recall at alpha 0.01 is at least 0.05, 0.15, and 0.25 for k=4,6,8;
9. recall is nondecreasing from k=4 to 6 to 8 to 12 at both thresholds.

Failure gives `KILL_MONDRIAN_CLIQUE_2018_CONFIRMATION`. A complete pass gives `PASS_MONDRIAN_CLIQUE_2018_CONFIRMATION` and authorizes only a separately frozen external-survey control and catalogue-level multiplicity study. It does not authorize a GhostStream claim or application.
