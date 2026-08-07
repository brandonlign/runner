# OrbitTrace v8 external validation — FRIPON 2018/2019 zero-data freshness audit

## Status
Frozen before any OrbitTrace project access to FRIPON 2018 or 2019 event records, event pages, downloads, radiants, velocities, orbital elements, or source/shower labels.

This is the single fallback catalogue search authorized after Harvard 1968–1969 failed v8 recurrence eligibility. The Harvard failure is catalogue/interface incompatibility, not a v8 scientific failure.

## Why FRIPON and why 2018/2019
Public FRIPON documentation exposes a coherent multi-station fireball network with event dates, radiants, speed products and orbital parameters. An independent A&A study states that the FRIPON database contained 3,871 confirmed events from April 2016 through June 2020. Without inspecting any event row or year count, reserve **2018 and 2019** prospectively as the two latest complete calendar years wholly contained in that published historical interval. No alternate FRIPON year pair may be selected after scientific values are accessed.

The year choice therefore uses only published temporal coverage and completeness logic, not target information, solar-longitude coverage, shower content, event-level values, or detector output.

## Immutable Harvard prerequisite
The corrected Harvard recurrence-eligibility run is `31227232530`, artifact `9012522244`, ZIP SHA-256 `7d9e68ec6f5f9790613869316839f9b6e5cb29c3a0c17f360dd244b0d6531c67`, verdict `FAIL_HARVARD_1968_1969_V8_RECURRENCE_ELIGIBILITY`. It records that `har6869.tab` was never downloaded/opened and that no scientific event value or OrbitTrace target information was accessed.

## Zero-data repository audit
Scan the complete set of remote repository branch refs, not only `main`, for evidence that FRIPON 2018/2019 has already been scientifically consumed by OrbitTrace work.

FRIPON markers include:
- `FRIPON`;
- `Fireball Recovery and InterPlanetary Observation Network`;
- `fireball.fripon.org`;
- `fripon_detections`;
- public database route names such as `list_multiple.php`, `displaymultiple.php`, or `list_pipeline.php`.

A FRIPON-related file is a potential scientific exposure if it contains either:
1. a literal reserved year `2018` or `2019`; or
2. an explicit FRIPON event/data-access marker such as a database URL, event-page route, pipeline field name, parser/download/access logic, or a FRIPON event identifier/path.

Generic bibliographic mentions of the FRIPON network/papers without reserved-year or event/data-access evidence are recorded separately and do not by themselves consume the panel.

The audit itself may read repository text only. It must not contact FRIPON, download a catalogue, inspect any event, or access OrbitTrace target information.

## Positive controls
The history scan must prove it reaches known spent external-work branches, including UKMON and AMOR external-validation branches. Failure of either positive control makes the freshness result invalid.

## Decision
- `PASS_FRIPON_2018_2019_REPO_SCIENTIFIC_FRESHNESS_AUDIT`: no potential FRIPON 2018/2019 scientific exposure and all positive controls pass.
- `FAIL_FRIPON_2018_2019_REPO_SCIENTIFIC_FRESHNESS_AUDIT`: any potential exposure appears or a positive control fails.

A pass authorizes only a separately frozen pre-scientific structure/interface audit. It does not authorize v8 execution or scientific-value access.
