# Catalogue-v6 development checkpoint/replay — infrastructure-only protocol

## Status

This is recovery infrastructure only. It does not authorize a second scientific development result while the authoritative repaired run `31270206927` is active or if that run completes scientifically.

It may be used only if the authoritative repaired execution ends without a scientific verdict because of infrastructure failure or timeout. A scientific `PASS_V3_PRIMARY_CATALOGUE_V6_DEVELOPMENT` or `FAIL_V3_PRIMARY_CATALOGUE_V6_DEVELOPMENT` permanently supersedes this recovery path for development adjudication.

No OrbitTrace target-containing access is authorized.

## Scientific identity

The scientific source is the exact frozen catalogue-v6 source SHA-256:

`a139802f328e0721a6b48b9b41e098660d03e0e218cec49f1d6251981a2828c9`

with only the exact two-line implementation repair established by source-only PR #490:

- instantiate `primary_components` through the already-frozen `component_records_track_v6(..., "v3")` call;
- instantiate `rescue_components` through the same frozen function with `"fixed4_rescue"`.

No detector score, threshold, proposal budget, calibration construction, membership definition, component rule, recurrence rule, family rule, ranking, metric, gate, baseline, target exclusion, or output semantics may change.

## Why a year checkpoint is valid

Source-only audit of the repaired frozen `main()` establishes this exact orchestration:

1. the frozen support parser constructs the target-excluded 2022/2023 scan and calibration inputs plus hidden labels;
2. `main()` loops over `YEARS` and calls `scan_year_v6(...)` independently for each year;
3. inside that loop the only cross-year state change is appending/extending the returned audit, anchors, and components;
4. primary/rescue recurrent-family construction occurs only after the loop;
5. label evaluation occurs only after family construction;
6. every scientific gate, verdict, result file, family file, and report is assembled by the original `main()` after those steps.

Therefore the exact return value of `scan_year_v6` for one immutable year/input universe is a natural computation checkpoint. Caching that return does not alter the method.

## Checkpoint creation

`run_year.py` may execute exactly one of 2022 or 2023. It still loads the exact frozen parser/sources and then calls the unchanged repaired `scan_year_v6` once for the selected year.

Each checkpoint includes:

- year;
- blind interval;
- catalogue-source identity record;
- scan/calibration row counts;
- SHA-256 of the **ordered event-ID sequence** for scan and calibration inputs;
- complete returned audit;
- complete returned anchors;
- complete returned components;
- repaired-v6 source SHA-256;
- base-runner source SHA-256;
- explicit `truth_used_for_scan=false` and `target_access=false` flags.

The checkpoint bytes are pickled with the current Python environment and separately SHA-256 pinned. Pickle is used only to preserve the exact native Python return objects and is accepted only from the repository's own hash-pinned Actions artifacts.

## Replay through the unchanged main

`replay_main.py` does **not** reimplement family construction, evaluation, gates, verdicts, or output writing.

It:

1. verifies both checkpoint byte hashes and all embedded source/firewall fields;
2. loads the same repaired v6/base/support modules;
3. calls the original support parser again;
4. requires exact catalogue-source identity plus exact scan/calibration counts and ordered event-ID SHA-256 equality for each year;
5. temporarily substitutes only `scan_year_v6` with a replay function returning the verified cached tuple `(audit, anchors, components)` for that same year;
6. calls the original frozen `main()` with the original scientific CLI arguments.

Thus every operation after `scan_year_v6` remains the exact original code. The recovery wrapper contains no promotion threshold, recovery threshold, precision threshold, qualified-match threshold, verdict string, family builder, evaluator, or ranking implementation.

## Parallelism and progress

If recovery is needed, the 2022 and 2023 checkpoint jobs may run independently/parallel because frozen `main()` already treats their `scan_year_v6` calls as independent until their returned objects are concatenated after the loop.

Each year job must emit:

- start marker with year, scan row count, calibration row count;
- an external one-minute CPU/RAM heartbeat while the unchanged scan is active;
- completion marker with anchor/component counts and checkpoint SHA-256.

The replay job must print input-identity guard success and one replay marker per year.

## Equivalence requirement

If this recovery path is ever activated, the scientific result is admissible only if all source-audit/replay-integrity checks pass. If the authoritative sequential run later also produces a scientific result, the two complete result JSONs, family payloads, gates, and verdicts must be compared; any difference blocks promotion and requires technical diagnosis.

No mismatch may be resolved by changing a scientific parameter or gate.