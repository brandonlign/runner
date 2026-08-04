# External validation of Mondrian four-clique coherence on EDMOND 2017

Status: frozen before the official EDMOND 2017 archive is downloaded, counted, labeled, transformed, or scored.

## Scientific question

Does the exact coverage-normalized 10° Mondrian four-clique method that passed the four GMN development panels in PR #38 preserve false-alarm control and weak-shower power in an independent observing network with a different reduction pipeline and native stream labels?

This is a cross-survey validation, not a GhostStream application and not a replacement for the unavailable complete-year GMN 2018 confirmation.

## Independence boundary

- Candidate detector, geometry, calibration bins, calibration counts, seeds, comparators, folds, thresholds, and gates are inherited unchanged from PR #38.
- External survey: EDMOND, year 2017 only.
- The prior NOP recovery used EDMOND 2011–2016 only. No EDMOND 2017 archive row, count, stream distribution, candidate score, or endpoint was inspected before this protocol and parser were committed.
- A schema sample from EDMOND 2011 was inspected only to freeze documented column names and the native label convention (`_spo` for sporadic background and exact non-sporadic `_stream` values for labeled streams).
- The first stage is data-only. Exact PR #38 source is decoded and run only if every data gate passes.
- Any failed data or scientific gate kills this exact formulation. No archive year, stream rule, quality threshold, phase bin, seed, score, comparator, fold, or gate may be changed after any EDMOND 2017 result is observed.

## Official source

Download exactly:

`https://ceres.ta3.sk/iaumdcdb/dataDBs/video_offline/iaumdcedmond2017.csv.zip`

Record URL, byte count, SHA-256, content type, last-modified header, ZIP member metadata, and complete headers.

Require the native EDMOND columns:

- unique row identifier: `_#`;
- solar longitude: `_sol`;
- geocentric radiant: `_ra_t`, `_dc_t`;
- geocentric speed: `_vg`;
- native stream assignment: `_stream`;
- quality coefficient: `_Qc`;
- UTC components: `_Y_ut`, `_M_ut`, `_D_ut`, `_h_ut`, `_m_ut`, `_s_ut`.

## Frozen event selection

Keep only rows whose UTC year is exactly 2017 and whose geometry is finite and physically bounded:

- `0 <= solar longitude < 360°`;
- `0 <= RA < 360°`;
- `-90° <= Dec <= 90°`;
- `5 <= Vg <= 80 km/s`;
- `_Qc >= 10`.

Normalize `_stream` by trimming whitespace and leading/trailing underscores and converting to uppercase.

- exact normalized `SPO` is the only sporadic-background label;
- a nonempty value other than `SPO` is a noisy external teacher label;
- blank labels are excluded from both background and positive pools and are never reclassified as sporadic.

Before any feasibility pool, calibration window, positive window, score, fold, or endpoint is formed, remove every event with solar longitude from 20.0° through 55.0° inclusive. No GhostStream radiant, speed, orbit, membership, event list, or result is used.

## Frozen external label eligibility

An exact normalized EDMOND stream code is eligible only if:

1. it has at least 20 selected events outside the blind interval;
2. at least one member-centered ±10° neighborhood contains at least 12 members of that exact code;
3. that same center has at least 124 selected `_spo` events within ±10°, sufficient for a 128-event k=4 episode.

Each eligible exact code receives a deterministic positive integer ID in lexical order. Its reporting/fold unit is `EDMOND:<exact code>`. Labels are used only to construct and evaluate positives; no label enters the candidate score or calibration distribution.

## Frozen data gates

Every gate must pass before candidate-source decoding:

1. downloaded archive is nonempty;
2. every parsed CSV member contains all required native columns;
3. at least 10,000 UTC-2017 rows;
4. finite geometry completeness at least 0.95 among UTC-2017 rows;
5. at least 8,000 rows pass the frozen physical and `_Qc` filters;
6. at least 5,000 selected `_spo` events outside the blind interval;
7. at least 20 locally feasible exact stream codes;
8. at least 5 eligible codes contain at least 100 selected events;
9. at least 20 globally anchored 10° phase bins contain a background center whose ±10° neighborhood has at least 128 selected `_spo` events;
10. the largest eligible stream contributes at most 25% of all selected labeled events.

Failure gives `KILL_EDMOND2017_DATA_GATE` and skips all scoring.

## Exact transformed artifact

Write deterministic gzip JSON Lines with the PR #38 event fields:

- `id`, `year`, `sol`, `ra`, `dec`, `vg`;
- `iau = -1` and `complex_key = SPORADIC` for `_spo`;
- deterministic positive `iau`, exact `code`, and `complex_key = EDMOND:<code>` for eligible labels.

Exclude noneligible labeled events rather than treating them as background.

## Exact candidate and calibration

If and only if the data gate passes, decode the unchanged PR #38 source from `mondrian_clique_development/source_parts_v2/part00.b64` through `part03.b64` and require SHA-256:

`f1c121e97a660a3820a11814c4325eb3ab33d34a031e83bdfb03b4b392e259b8`

Run it with:

- `year = 2017`;
- `corpus = edmond-2017-external`;
- complete-year minimum of 20 supported globally anchored 10° bins;
- 128 same-corpus calibration windows and 64 independent negative windows per supported bin;
- four deterministic positive replicates per eligible label and k in `{4,6,8,12}`;
- exact PR #38 seed prefixes.

The candidate remains the negative minimum complete-link diameter of every anchor-plus-three-nearest-neighbor subset in the 128-event physical-distance matrix.

## Fixed comparators and folds

On identical windows compute:

- killed eight-split PR #31 statistic;
- radius-2.5 local density;
- epsilon-2.5, minimum-samples-4 DBSCAN largest cluster;
- five deterministic event-count-balanced folds of exact EDMOND stream-code units.

Folds are reporting units only; no method is trained or tuned on EDMOND labels.

## Frozen external confirmation gates

Every gate must pass:

1. pooled candidate FPR at alpha 0.05 <= 0.060;
2. pooled candidate FPR at alpha 0.01 <= 0.020;
3. worst 60° reporting-sector FPR at alpha 0.05 <= 0.120;
4. weak-window AUROC >= 0.75;
5. candidate AUROC no more than 0.03 below the strongest fixed comparator;
6. at least four of five folds have candidate AUROC >= 0.70 and no fold is below 0.65;
7. recall at alpha 0.05 is at least 0.15, 0.30, and 0.45 for k=4,6,8;
8. recall at alpha 0.01 is at least 0.05, 0.15, and 0.25 for k=4,6,8;
9. recall is nondecreasing from k=4 to 6 to 8 to 12 at both thresholds.

Failure gives `KILL_EDMOND2017_EXTERNAL_CONFIRMATION`. A complete pass gives `PASS_EDMOND2017_EXTERNAL_CONFIRMATION` and authorizes only a separately frozen catalogue-level multiplicity study and a later blinded GhostStream evaluation. It does not itself create a GhostStream claim.
