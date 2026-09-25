# OrbitTrace fixed-4° blind catalogue deployment

## Scientific question

Can the exact frozen fixed-4° coverage-normalized Mondrian anchored four-clique detector surface the OrbitTrace population in a catalogue-wide, target-free ranking before any OrbitTrace member identity is revealed?

This is a post-freeze deployment of the existing detector. It does not alter the detector, its 4° solar-longitude scale, the anchored four-clique definition, or any prior benchmark result. The only new component is a deterministic catalogue-search and cross-year recurrence wrapper needed to apply an episode detector to a complete catalogue.

## Isolation from the literature comparison

The deployment is confined to:

- branch `agent/orbittrace-fixed4-blind-catalogue-audit`;
- directory `orbittrace_blind_catalogue/`;
- workflow `orbittrace_fixed4_blind_catalogue_execution.yml`;
- concurrency group `orbittrace-fixed4-blind-catalogue-execution`;
- dedicated pre-reveal and final artifacts.

No file under `orbittrace_literature_comparison/` and no literature-comparison workflow, branch, result, or artifact is changed.

## Immutable detector

The execution must decode and verify these exact sources:

- detector SHA-256 `747b2b1471f3ba193d68a39dd82ad3ac8506be63b651d45f84ffabb8d1acd301`;
- baseline SHA-256 `7718ac5229475f4240305ad9c1e073c49702c771df36612d9be5baa877b46a50`;
- Mondrian scorer SHA-256 `f1c121e97a660a3820a11814c4325eb3ab33d34a031e83bdfb03b4b392e259b8`.

The detector remains:

- four-clique size: 4;
- solar-longitude scale: exactly 4° per distance unit;
- radiant longitude, radiant latitude, and geocentric speed scales: exactly those in the frozen distance function;
- local activity support: ±10°;
- Mondrian width: 10°.

The execution source must pass a numerical equivalence audit against the exact frozen pairwise-distance function before catalogue access.

## Blind catalogue

The target-free scan uses all available official GMN monthly trajectory files for:

- complete years 2019–2025;
- January–July 2026.

Every valid event must have finite:

- solar longitude in [0°, 360°];
- geocentric ecliptic longitude in [0°, 360°];
- geocentric ecliptic latitude in [-90°, 90°];
- geocentric speed in [5, 75] km/s.

Only events whose native GMN shower label normalizes to `SPORADIC` enter the discovery scan. Duplicate trajectory identifiers are removed within each year. No OrbitTrace identifier, coordinate, activity range, radiant, speed, orbital element, canonical count, or prior cluster membership may be present in or supplied to the blind scan source.

## Catalogue wrapper

The fixed detector was developed for 128-event local episodes. The catalogue wrapper applies its unchanged anchored four-clique core directly to every eligible event:

1. Divide each year into the frozen 10° Mondrian bins.
2. For every event as an anchor, consider events in the anchor bin and its two neighboring bins.
3. Use a deterministic six-dimensional circular embedding only as a nearest-neighbor prefilter.
4. Recompute exact frozen fixed-4° distances for all prefetched neighbors.
5. Select the anchor's exact three nearest eligible neighbors within ±10° solar longitude.
6. Score the resulting quartet by the exact frozen maximum pairwise diameter.
7. Deduplicate exact four-event sets.
8. Rank quartets within each year by increasing diameter with a SHA-256 tie break.

The prefilter uses 256 neighbors. A deterministic sample in every year and Mondrian bin is re-evaluated with 512 neighbors. Any selected-neighbor mismatch terminates the run; it cannot trigger adaptive expansion or reranking.

The top 100,000 quartets per year are preserved. The top 25,000 per year enter recurrence aggregation.

## Cross-year recurrence wrapper

Each quartet is represented by its circular mean solar longitude, circular mean Sun-centered radiant longitude, mean ecliptic latitude, and mean geocentric speed. Distances between quartet centroids use the same fixed physical scales as the detector.

For every retained quartet used as a seed:

- query the 32 nearest quartet centroids in every other year;
- choose the exact nearest quartet in that year;
- construct recurrence families at fixed centroid thresholds 1.5, 2.0, and 2.5 scaled units;
- use 2.0 as the primary threshold;
- require at least three represented years;
- rank families lexicographically by greater year support, greater summed `-log10` within-year empirical rank strength, smaller maximum pairwise centroid distance, smaller median quartet diameter, and SHA-256 tie break.

The top 5,000 families at each fixed threshold are preserved. No threshold is selected after reveal.

## Mandatory pre-reveal freeze

Before the canonical OrbitTrace artifact is downloaded or opened, the workflow must:

1. finish all catalogue parsing, quartet ranking, recurrence aggregation, and family ranking;
2. write `blind_scan.json`;
3. write and print its SHA-256;
4. upload a dedicated `orbittrace-fixed4-blind-scan-pre-reveal` artifact containing the scan, rankings, catalogue identifiers, provenance, and digest.

The canonical artifact may be retrieved only in a later workflow step. The reveal program must verify that `blind_scan.json` still matches the pre-reveal digest and is marked `BLIND_SCAN_FROZEN_BEFORE_TARGET_REVEAL`.

## Frozen reveal and decision rules

The reveal stage performs exact identifier overlap only. It cannot modify the scan, rerank a family, replace a quartet, alter a threshold, or add a candidate.

At the primary 2.0 threshold:

### Full blind rediscovery

- best exact-overlap family rank ≤ 100;
- family supports at least 4 years;
- at least 12 exact canonical OrbitTrace identifiers occur among its quartet slots;
- at least 4 years contain at least 2 exact canonical identifiers each.

Verdict: `FULL_BLIND_ORBITTRACE_REDISCOVERY`.

### Partial blind recovery

- best exact-overlap family rank ≤ 1,000;
- family supports at least 3 years;
- at least 8 exact canonical identifiers occur among its quartet slots;
- at least 3 years contain at least 2 exact canonical identifiers each.

Verdict: `PARTIAL_BLIND_ORBITTRACE_RECOVERY`.

Otherwise:

`NO_BLIND_ORBITTRACE_RECOVERY`.

The 1.5 and 2.5 thresholds are reported only as frozen sensitivity results and cannot replace the primary verdict.

## Claim boundary

A full result permits the statement that the frozen detector, with a separately frozen generic catalogue wrapper, independently rediscovered OrbitTrace in a target-free catalogue ranking. A partial result permits only a weaker blind-recovery statement. A negative result means the current detector cannot defensibly be presented as a blind OrbitTrace discovery method.

Even a full result does not rewrite the historical chronology: exploratory HDBSCAN first exposed the candidate. It also does not establish a formally recognized meteor shower or resolve branch-versus-distinct-stream status.

No post-reveal rerun, threshold change, candidate-pool expansion, year removal, month removal, target-specific filter, or ranking modification is authorized.
